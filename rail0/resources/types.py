"""
Public types for the RAIL0 Python SDK.

All types reflect the OpenAPI schema in gen/openapi.json.
Request / response bodies use camelCase keys to match the JSON wire format.
"""

from __future__ import annotations

from typing import Literal
from typing_extensions import TypedDict

# ================================================================
#  Primitive aliases
# ================================================================

Address = str
"""Checksummed or lowercase Ethereum address (42 chars, 0x-prefixed)."""

Bytes32 = str
"""32-byte value, hex-encoded (66 chars, 0x-prefixed). Used for payment IDs, hashes, and signature components."""

Uint256String = str
"""Unsigned 256-bit integer serialised as a decimal string. Avoids precision loss for large amounts."""

# ================================================================
#  Core model
# ================================================================


class Payment(TypedDict):
    """Immutable payment configuration shared by both payer and payee.

    The EIP-712 digest (configHash) is committed on-chain the first time
    authorize or charge is called. Every subsequent operation on the same
    paymentId must supply the exact same struct.
    """

    payer: Address
    payee: Address
    token: Address
    maxAmount: Uint256String
    authorizationExpiry: int
    refundExpiry: int
    feeBps: int
    feeReceiver: Address


class PaymentState(TypedDict):
    """On-chain mutable state for a payment, packed in a single storage slot."""

    exists: bool
    capturableAmount: Uint256String
    refundableAmount: Uint256String


# ================================================================
#  Request params
# ================================================================


class AuthorizeParams(TypedDict):
    """Body for payments.authorize().

    v, r, s are the EIP-3009 transferWithAuthorization signature produced
    by the payer's private key. Use sign_authorize() to build the signature off-chain.
    """

    payment: Payment
    amount: Uint256String
    v: int
    r: Bytes32
    s: Bytes32


ChargeParams = AuthorizeParams
"""Body for payments.charge() (one-shot authorize + capture). Same shape as AuthorizeParams."""


class CaptureParams(TypedDict):
    """Body for payments.capture()."""

    payment: Payment
    amount: Uint256String


class VoidParams(TypedDict):
    """Body for payments.void()."""

    payment: Payment


ReleaseParams = VoidParams
"""Body for payments.release(). Same shape as VoidParams."""


class RefundParams(TypedDict):
    """Body for payments.refund()."""

    payment: Payment
    amount: Uint256String


# ================================================================
#  Response shapes
# ================================================================


class PaymentResponse(TypedDict):
    """Full on-chain state returned by payments.get()."""

    paymentId: Bytes32
    state: PaymentState
    configHash: Bytes32


class TransactionResponse(TypedDict):
    """Returned by every write operation. The transaction may still be pending."""

    transactionHash: Bytes32
    status: Literal["pending", "confirmed", "failed"]


TransactionStatus = Literal["pending", "confirmed", "failed"]
"""Confirmation status of a submitted transaction."""


class TokenStatusResponse(TypedDict):
    """Returned by tokens.is_accepted()."""

    address: Address
    accepted: bool


class HashResponse(TypedDict):
    """EIP-712 digest of a Payment struct, returned by payments.hash()."""

    hash: Bytes32


class NonceResponse(TypedDict):
    """Returned by payments.authorize_nonce() and payments.charge_nonce()."""

    nonce: Bytes32


class DomainSeparatorResponse(TypedDict):
    """EIP-712 domain separator of the RAIL0 contract, returned by utils.domain_separator()."""

    domainSeparator: Bytes32


class VersionResponse(TypedDict):
    """Contract version number, returned by utils.version()."""

    version: int


class ApiErrorBody(TypedDict):
    """Shape of error responses from the RAIL0 API."""

    error: str
    message: str
