"""SIWE (EIP-4361) authentication resource for the RAIL0 SDK."""

from __future__ import annotations

import datetime
import hashlib
from typing import Any, Dict

import coincurve

from ..core.http import HttpClient


# ================================================================
#  Crypto helpers
# ================================================================

def _keccak256(data: bytes) -> bytes:
    """Return the Keccak-256 digest of *data*."""
    from Crypto.Hash import keccak  # type: ignore[import-untyped]

    k = keccak.new(digest_bits=256)
    k.update(data)
    return k.digest()


def private_key_to_address(private_key_hex: str) -> str:
    """Derive the EIP-55 checksummed Ethereum address from a hex private key.

    Args:
        private_key_hex: 32-byte private key as a hex string (with or without 0x prefix).

    Returns:
        EIP-55 checksummed address string, e.g. ``"0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"``.
    """
    key_bytes = bytes.fromhex(private_key_hex.removeprefix("0x"))
    priv = coincurve.PrivateKey(key_bytes)
    # Uncompressed pubkey: 0x04 || X(32) || Y(32)
    pub_bytes = priv.public_key.format(compressed=False)  # 65 bytes
    addr_hash = _keccak256(pub_bytes[1:])  # hash of X||Y
    addr_bytes = addr_hash[12:]  # last 20 bytes
    return _checksum_address(addr_bytes)


def _checksum_address(addr_bytes: bytes) -> str:
    """Apply EIP-55 checksum encoding to 20 raw address bytes."""
    lower = addr_bytes.hex()  # 40 hex chars, lowercase
    hash_bytes = _keccak256(lower.encode())
    out: list[str] = []
    for i, c in enumerate(lower):
        nibble = hash_bytes[i // 2] >> (4 if i % 2 == 0 else 0) & 0xF
        out.append(c.upper() if c.isalpha() and nibble >= 8 else c)
    return "0x" + "".join(out)


def personal_sign(private_key_hex: str, message: str) -> str:
    """Sign *message* with EIP-191 personal_sign and return a 0x-prefixed 65-byte hex signature.

    The signature bytes are ordered as ``r(32) || s(32) || v(1)`` where ``v ∈ {27, 28}``.

    Args:
        private_key_hex: 32-byte private key as a hex string (with or without 0x prefix).
        message: The plaintext message to sign (UTF-8).
    """
    msg_bytes = message.encode("utf-8")
    prefix = f"\x19Ethereum Signed Message:\n{len(msg_bytes)}".encode()
    digest = _keccak256(prefix + msg_bytes)

    key_bytes = bytes.fromhex(private_key_hex.removeprefix("0x"))
    priv = coincurve.PrivateKey(key_bytes)
    # coincurve returns 65 bytes: v(1) || r(32) || s(32) with v ∈ {0,1}
    raw_sig = priv.sign_recoverable(digest, hasher=None)  # hasher=None → pre-hashed
    v = raw_sig[64] + 27  # normalise to Ethereum convention {27,28}
    sig = raw_sig[:64] + bytes([v])
    return "0x" + sig.hex()


# ================================================================
#  EIP-4361 message builder
# ================================================================

def _build_siwe_message(domain: str, address: str, nonce: str) -> str:
    """Build a minimal EIP-4361 (SIWE) message string.

    The format is specified at https://eips.ethereum.org/EIPS/eip-4361.

    Args:
        domain: RFC 3986 authority of the requesting resource (e.g. ``"api.rail0.xyz"``).
        address: EIP-55 checksummed Ethereum address of the signer.
        nonce: Single-use random nonce from the server.

    Returns:
        The complete EIP-4361 message string, ready to be signed.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    issued_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    uri = f"https://{domain}"
    lines = [
        f"{domain} wants you to sign in with your Ethereum account:",
        address,
        "",
        "Sign in to RAIL0",
        "",
        f"URI: {uri}",
        "Version: 1",
        "Chain ID: 1",
        f"Nonce: {nonce}",
        f"Issued At: {issued_at}",
    ]
    return "\n".join(lines)


# ================================================================
#  Response types (plain dicts; no extra dep required)
# ================================================================

NonceResponse = Dict[str, Any]
"""Dict with keys ``nonce`` (str) and ``expires_at`` (str)."""

AuthResponse = Dict[str, Any]
"""Dict with keys ``token``, ``address``, ``account_id``, ``expires_at``."""


# ================================================================
#  AuthResource
# ================================================================

class AuthResource:
    """SIWE authentication operations.

    Typical usage::

        resp = client.auth.login(private_key_hex="0xdeadbeef...", domain="api.rail0.xyz")
        # resp["token"] is the JWT for subsequent requests
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Low-level API wrappers
    # ------------------------------------------------------------------

    def get_nonce(self) -> NonceResponse:
        """Fetch a single-use SIWE nonce from the API.

        Returns:
            A dict with ``nonce`` (str) and ``expires_at`` (ISO-8601 str).
        """
        return self._http.post("/nonces", {})  # type: ignore[return-value]

    def verify(self, message: str, signature: str) -> AuthResponse:
        """Submit a signed SIWE message to the API and obtain a JWT.

        Args:
            message: The EIP-4361 message string that was signed.
            signature: 0x-prefixed 65-byte hex signature (EIP-191 personal_sign).

        Returns:
            A dict with ``token``, ``address``, ``account_id``, and ``expires_at``.
        """
        return self._http.post("/auth", {"message": message, "signature": signature})  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # High-level helper
    # ------------------------------------------------------------------

    def login(self, private_key_hex: str, domain: str) -> AuthResponse:
        """Perform the full SIWE authentication flow in one call.

        Steps:

        1. ``POST /nonces`` — obtain a fresh nonce.
        2. Build an EIP-4361 message for *domain* and the address derived from *private_key_hex*.
        3. Sign the message with EIP-191 personal_sign using *private_key_hex*.
        4. ``POST /auth`` — verify the signature and return a JWT.

        Args:
            private_key_hex: 32-byte Ethereum private key, hex-encoded (with or without ``0x``).
            domain: Hostname of the API server, e.g. ``"api.rail0.xyz"``.  Used both as the
                SIWE domain and to build the ``URI`` field.

        Returns:
            A dict with ``token``, ``address``, ``account_id``, and ``expires_at``.
        """
        nonce_resp: NonceResponse = self.get_nonce()
        nonce: str = nonce_resp["nonce"]

        address = private_key_to_address(private_key_hex)
        message = _build_siwe_message(domain, address, nonce)
        signature = personal_sign(private_key_hex, message)

        return self.verify(message, signature)
