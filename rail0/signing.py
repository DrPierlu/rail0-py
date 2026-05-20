"""EIP-712 and EIP-3009 signing utilities for RAIL0 payments.

Requires the optional signing dependencies::

    pip install rail0[signing]
    # or: pip install coincurve pysha3

No private key is ever sent to the API — signatures are built off-chain and
included in the request body.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

try:
    import coincurve
    from Crypto.Hash import keccak as _keccak_lib
except ImportError as exc:
    raise ImportError(
        "Signing requires 'coincurve' and 'pycryptodome'. "
        "Install them with: pip install rail0[signing]"
    ) from exc

from .resources.types import Address, Bytes32, PaymentConfig

# ================================================================
#  EIP-712 type strings
# ================================================================

_DOMAIN_TYPE = "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
_TRANSFER_TYPE = (
    "TransferWithAuthorization(address from,address to,uint256 value,"
    "uint256 validAfter,uint256 validBefore,bytes32 nonce)"
)


def _keccak256(data: bytes) -> bytes:
    k = _keccak_lib.new(digest_bits=256)
    k.update(data)
    return k.digest()


_DOMAIN_TYPEHASH = _keccak256(_DOMAIN_TYPE.encode())
_TRANSFER_TYPEHASH = _keccak256(_TRANSFER_TYPE.encode())

# ================================================================
#  ABI encoding helpers (fixed-size types: address, uint256, bytes32)
# ================================================================


def _hex_to_bytes(hex_str: str) -> bytes:
    h = hex_str[2:] if hex_str.startswith("0x") else hex_str
    return bytes.fromhex(h)


def _abi_address(address: Address) -> bytes:
    return b"\x00" * 12 + _hex_to_bytes(address)


def _abi_uint256(value: int) -> bytes:
    return value.to_bytes(32, "big")


def _bytes_to_hex(data: bytes) -> Bytes32:
    return "0x" + data.hex()


# ================================================================
#  EIP-712 digest construction
# ================================================================


def _hash_domain(domain: TokenDomain) -> bytes:
    return _keccak256(
        _DOMAIN_TYPEHASH
        + _keccak256(domain.name.encode())
        + _keccak256(domain.version.encode())
        + _abi_uint256(domain.chain_id)
        + _abi_address(domain.verifying_contract)
    )


def _hash_struct(
    from_: Address,
    to: Address,
    value: int,
    valid_after: int,
    valid_before: int,
    nonce: Bytes32,
) -> bytes:
    return _keccak256(
        _TRANSFER_TYPEHASH
        + _abi_address(from_)
        + _abi_address(to)
        + _abi_uint256(value)
        + _abi_uint256(valid_after)
        + _abi_uint256(valid_before)
        + _hex_to_bytes(nonce)
    )


def _build_digest(
    domain: TokenDomain,
    from_: Address,
    to: Address,
    value: int,
    valid_after: int,
    valid_before: int,
    nonce: Bytes32,
) -> bytes:
    return _keccak256(
        b"\x19\x01"
        + _hash_domain(domain)
        + _hash_struct(from_, to, value, valid_after, valid_before, nonce)
    )


# ================================================================
#  Public types
# ================================================================


@dataclass
class TokenDomain:
    """EIP-712 domain of the ERC-20 token (NOT the RAIL0 contract)."""

    name: str
    """Token's EIP-712 name, e.g. 'USD Coin' for USDC."""

    version: str
    """Token's EIP-712 version, e.g. '2' for USDC."""

    chain_id: int

    verifying_contract: Address
    """Token contract address — used as verifyingContract in the domain."""


@dataclass
class Eip3009Signature:
    """EIP-3009 transferWithAuthorization signature, ready to pass into authorize / charge."""

    v: int
    """Recovery identifier (27 or 28)."""

    r: Bytes32
    """r component of the signature."""

    s: Bytes32
    """s component of the signature."""


@dataclass
class SignTransferParams:
    """Parameters for a raw transferWithAuthorization signature."""

    from_: Address
    to: Address
    """Recipient of the transfer — the RAIL0 contract address."""

    value: int
    """Amount in token base units (e.g. 6 decimals for USDC)."""

    valid_before: int
    """Latest block timestamp at which the signature is valid."""

    nonce: Bytes32
    """Unique bytes32 nonce — must not have been used before for this (from, to) pair."""

    valid_after: int = field(default=0)
    """Earliest block timestamp at which the signature is valid (default: 0)."""


@dataclass
class SignPaymentParams:
    """Parameters for signing an authorize or charge call.

    Obtain the nonce from create_payment() response: resp["signingPayload"]["message"]["nonce"].
    The contract hardcodes validAfter=0 and validBefore=payment.authorizationExpiry;
    these are not configurable by the caller.
    """

    private_key: Union[str, bytes]
    """Payer's private key (0x-prefixed hex string or raw bytes)."""

    payment: PaymentConfig
    amount: int
    """Amount to pull from the payer, in token base units."""

    nonce: Bytes32
    """Nonce from create_payment() response: resp["signingPayload"]["message"]["nonce"]."""

    contract_address: Address
    """Deployed RAIL0 contract address — receives the escrowed funds."""

    token_domain: TokenDomain
    """EIP-712 domain of the payment token (name, version from the token contract)."""

    valid_before: Optional[int] = None
    """Override validBefore; defaults to payment["authorizationExpiry"]."""


# ================================================================
#  Public API
# ================================================================


def _do_sign(
    private_key: Union[str, bytes],
    domain: TokenDomain,
    from_: Address,
    to: Address,
    value: int,
    valid_after: int,
    valid_before: int,
    nonce: Bytes32,
) -> Eip3009Signature:
    key_bytes = _hex_to_bytes(private_key) if isinstance(private_key, str) else private_key
    digest = _build_digest(domain, from_, to, value, valid_after, valid_before, nonce)

    key = coincurve.PrivateKey(key_bytes)
    # sign_recoverable returns [r(32), s(32), recovery_id(1)] = 65 bytes
    # hasher=None: digest is already keccak256 — pass raw bytes
    sig = key.sign_recoverable(digest, hasher=None)

    recovery_id = sig[64]
    r = sig[:32]
    s = sig[32:64]

    return Eip3009Signature(
        v=recovery_id + 27,
        r=_bytes_to_hex(r),
        s=_bytes_to_hex(s),
    )


def sign_transfer_with_authorization(
    private_key: Union[str, bytes],
    domain: TokenDomain,
    params: SignTransferParams,
) -> Eip3009Signature:
    """Sign a raw EIP-3009 transferWithAuthorization message.

    For RAIL0 payment flows prefer sign_authorize / sign_charge which
    set from_, to, valid_before automatically from the Payment struct.
    """
    return _do_sign(
        private_key,
        domain,
        from_=params.from_,
        to=params.to,
        value=params.value,
        valid_after=params.valid_after,
        valid_before=params.valid_before,
        nonce=params.nonce,
    )


def sign_authorize(params: SignPaymentParams) -> Eip3009Signature:
    """Sign the EIP-3009 payload required by an authorize call.

    ```python
    resp = client.payments.create_payment({
        "payment": payment,
        "amount": "50000000",
        "chainId": chain_id,
        "mode": "authorize",
    })
    nonce = resp["signingPayload"]["message"]["nonce"]
    sig = sign_authorize(SignPaymentParams(
        private_key=private_key,
        payment=payment,
        amount=50_000_000,
        nonce=nonce,
        contract_address=resp["rail0Contract"],
        token_domain=TokenDomain(**resp["signingPayload"]["domain"]),
    ))
    client.payments.sign(resp["paymentId"], {"v": sig.v, "r": sig.r, "s": sig.s})
    client.payments.authorize(resp["paymentId"])
    ```
    """
    return _do_sign(
        params.private_key,
        params.token_domain,
        from_=params.payment["payer"],
        to=params.contract_address,
        value=params.amount,
        valid_after=0,
        valid_before=params.valid_before if params.valid_before is not None else params.payment["authorizationExpiry"],
        nonce=params.nonce,
    )


def sign_charge(params: SignPaymentParams) -> Eip3009Signature:
    """Sign the EIP-3009 payload required by a charge call.

    ```python
    resp = client.payments.create_payment({
        "payment": payment,
        "amount": "25000000",
        "chainId": chain_id,
        "mode": "charge",
    })
    nonce = resp["signingPayload"]["message"]["nonce"]
    sig = sign_charge(SignPaymentParams(
        private_key=private_key,
        payment=payment,
        amount=25_000_000,
        nonce=nonce,
        contract_address=resp["rail0Contract"],
        token_domain=TokenDomain(**resp["signingPayload"]["domain"]),
    ))
    client.payments.sign(resp["paymentId"], {"v": sig.v, "r": sig.r, "s": sig.s})
    client.payments.charge(resp["paymentId"])
    ```
    """
    return _do_sign(
        params.private_key,
        params.token_domain,
        from_=params.payment["payer"],
        to=params.contract_address,
        value=params.amount,
        valid_after=0,
        valid_before=params.valid_before if params.valid_before is not None else params.payment["authorizationExpiry"],
        nonce=params.nonce,
    )
