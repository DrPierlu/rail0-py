"""Tests for EIP-712 / EIP-3009 signing utilities."""

import pytest

try:
    from rail0.signing import (
        Eip3009Signature,
        SignPaymentParams,
        SignTransferParams,
        TokenDomain,
        sign_authorize,
        sign_charge,
        sign_transfer_with_authorization,
        _keccak256,
        _abi_address,
        _abi_uint256,
        _hex_to_bytes,
    )

    HAS_SIGNING = True
except ImportError:
    HAS_SIGNING = False

pytestmark = pytest.mark.skipif(not HAS_SIGNING, reason="coincurve/pysha3 not installed")

# Deterministic test key — NOT a real key, do not use in production.
TEST_PRIVATE_KEY = "0x4c0883a69102937d6231471b5dbb6e538eba2ef7a8a44572c79b13d1dea8c3e0"
TEST_FROM = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
TEST_TO = "0x6187e4DEC2e445e445E58b1B77A744A9E826E03d"

PAYMENT = {
    "payer": TEST_FROM,
    "payee": TEST_TO,
    "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "maxAmount": "100000000",
    "authorizationExpiry": 9999999999,
    "refundExpiry": 9999999999,
    "feeBps": 0,
    "feeReceiver": "0x0000000000000000000000000000000000000000",
}

if HAS_SIGNING:
    TOKEN_DOMAIN = TokenDomain(
        name="USD Coin",
        version="2",
        chain_id=8453,
        verifying_contract="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    )
else:
    TOKEN_DOMAIN = None  # type: ignore[assignment]

NONCE = "0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbbccccddddaaaabbbbccccdddd"


# ================================================================
#  Low-level ABI helpers
# ================================================================


def test_keccak256_known_value():
    # keccak256("") = 0xc5d246...
    result = _keccak256(b"")
    assert result == bytes.fromhex("c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")


def test_abi_address_pads_to_32_bytes():
    addr = "0x" + "ab" * 20
    encoded = _abi_address(addr)
    assert len(encoded) == 32
    assert encoded[:12] == b"\x00" * 12
    assert encoded[12:] == bytes.fromhex("ab" * 20)


def test_abi_uint256_encodes_big_endian():
    encoded = _abi_uint256(1)
    assert len(encoded) == 32
    assert encoded[-1] == 1
    assert encoded[:-1] == b"\x00" * 31


def test_abi_uint256_large_value():
    value = 2**256 - 1
    encoded = _abi_uint256(value)
    assert encoded == b"\xff" * 32


# ================================================================
#  Signature shape
# ================================================================


def test_sign_transfer_with_authorization_returns_signature():
    sig = sign_transfer_with_authorization(
        TEST_PRIVATE_KEY,
        TOKEN_DOMAIN,
        SignTransferParams(
            from_=TEST_FROM,
            to=TEST_TO,
            value=50_000_000,
            valid_before=9999999999,
            nonce=NONCE,
        ),
    )
    assert isinstance(sig, Eip3009Signature)
    assert sig.v in (27, 28)
    assert sig.r.startswith("0x")
    assert sig.s.startswith("0x")
    assert len(sig.r) == 66  # 0x + 64 hex chars
    assert len(sig.s) == 66


def test_sign_authorize_returns_signature():
    sig = sign_authorize(SignPaymentParams(
        private_key=TEST_PRIVATE_KEY,
        payment=PAYMENT,
        amount=50_000_000,
        nonce=NONCE,
        contract_address=TEST_TO,
        token_domain=TOKEN_DOMAIN,
    ))
    assert isinstance(sig, Eip3009Signature)
    assert sig.v in (27, 28)


def test_sign_charge_returns_signature():
    sig = sign_charge(SignPaymentParams(
        private_key=TEST_PRIVATE_KEY,
        payment=PAYMENT,
        amount=25_000_000,
        nonce=NONCE,
        contract_address=TEST_TO,
        token_domain=TOKEN_DOMAIN,
    ))
    assert isinstance(sig, Eip3009Signature)
    assert sig.v in (27, 28)


def test_sign_authorize_and_charge_produce_different_sigs_for_different_amounts():
    sig1 = sign_authorize(SignPaymentParams(
        private_key=TEST_PRIVATE_KEY,
        payment=PAYMENT,
        amount=50_000_000,
        nonce=NONCE,
        contract_address=TEST_TO,
        token_domain=TOKEN_DOMAIN,
    ))
    sig2 = sign_authorize(SignPaymentParams(
        private_key=TEST_PRIVATE_KEY,
        payment=PAYMENT,
        amount=25_000_000,
        nonce=NONCE,
        contract_address=TEST_TO,
        token_domain=TOKEN_DOMAIN,
    ))
    # Different amounts → different digests → different signatures
    assert (sig1.r, sig1.s) != (sig2.r, sig2.s)


def test_sign_is_deterministic():
    params = SignPaymentParams(
        private_key=TEST_PRIVATE_KEY,
        payment=PAYMENT,
        amount=50_000_000,
        nonce=NONCE,
        contract_address=TEST_TO,
        token_domain=TOKEN_DOMAIN,
    )
    sig1 = sign_authorize(params)
    sig2 = sign_authorize(params)
    assert sig1.v == sig2.v
    assert sig1.r == sig2.r
    assert sig1.s == sig2.s


def test_accepts_bytes_private_key():
    key_bytes = _hex_to_bytes(TEST_PRIVATE_KEY)
    sig = sign_authorize(SignPaymentParams(
        private_key=key_bytes,
        payment=PAYMENT,
        amount=50_000_000,
        nonce=NONCE,
        contract_address=TEST_TO,
        token_domain=TOKEN_DOMAIN,
    ))
    # Same result as hex key
    sig_hex = sign_authorize(SignPaymentParams(
        private_key=TEST_PRIVATE_KEY,
        payment=PAYMENT,
        amount=50_000_000,
        nonce=NONCE,
        contract_address=TEST_TO,
        token_domain=TOKEN_DOMAIN,
    ))
    assert sig.r == sig_hex.r
    assert sig.s == sig_hex.s
    assert sig.v == sig_hex.v


def test_valid_before_defaults_to_authorization_expiry():
    sig_default = sign_authorize(SignPaymentParams(
        private_key=TEST_PRIVATE_KEY,
        payment=PAYMENT,
        amount=50_000_000,
        nonce=NONCE,
        contract_address=TEST_TO,
        token_domain=TOKEN_DOMAIN,
        # valid_before not set → defaults to payment["authorizationExpiry"]
    ))
    sig_explicit = sign_authorize(SignPaymentParams(
        private_key=TEST_PRIVATE_KEY,
        payment=PAYMENT,
        amount=50_000_000,
        nonce=NONCE,
        contract_address=TEST_TO,
        token_domain=TOKEN_DOMAIN,
        valid_before=PAYMENT["authorizationExpiry"],
    ))
    assert sig_default.r == sig_explicit.r
    assert sig_default.s == sig_explicit.s
