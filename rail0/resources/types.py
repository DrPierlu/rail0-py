"""
Public types for the RAIL0 Python SDK.

All types reflect the OpenAPI schema in gen/openapi.json.
Request / response bodies use camelCase keys to match the JSON wire format.
"""

from __future__ import annotations

from typing import Literal, List
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
#  Core models
# ================================================================


class PaymentConfig(TypedDict):
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


class EIP712Domain(TypedDict):
    """EIP-712 domain for the token contract."""

    name: str
    version: str
    chainId: int
    verifyingContract: Address


class _TypeEntry(TypedDict):
    name: str
    type: str


class _EIP712Types(TypedDict):
    TransferWithAuthorization: List[_TypeEntry]


class EIP3009Message(TypedDict):
    """Message fields for the EIP-3009 TransferWithAuthorization typed-data signature."""

    from_: Address  # key is "from" in JSON
    to: Address
    value: Uint256String
    validAfter: Uint256String
    validBefore: Uint256String
    nonce: Bytes32


class SigningPayload(TypedDict):
    """EIP-712 typed-data structure returned by POST /payments."""

    domain: EIP712Domain
    types: _EIP712Types
    primaryType: Literal["TransferWithAuthorization"]
    message: EIP3009Message


# ================================================================
#  Request bodies
# ================================================================


class CreatePaymentRequest(TypedDict):
    """Body for payments.create_payment()."""

    payment: PaymentConfig
    amount: Uint256String
    chainId: int
    mode: Literal["authorize", "charge"]


class PayerSignatureRequest(TypedDict):
    """Body for payments.sign(). EIP-712 signature components."""

    v: int
    r: Bytes32
    s: Bytes32


class CapturePaymentRequest(TypedDict):
    """Body for payments.prepare_capture(). Amount to capture from escrow."""

    amount: Uint256String


class SubmitTransactionRequest(TypedDict):
    """Body for submit_capture(), submit_void(), submit_approve(), submit_refund()."""

    signedTransaction: str


class ApproveRequest(TypedDict):
    """Body for payments.prepare_approve(). Allowance to grant the RAIL0 contract."""

    amount: Uint256String


class RefundPaymentRequest(TypedDict):
    """Body for payments.prepare_refund(). Amount to refund to the payer."""

    amount: Uint256String


# ================================================================
#  Response shapes
# ================================================================


class CreatePaymentResponse(TypedDict):
    """Returned by payments.create_payment()."""

    paymentId: Bytes32
    configHash: Bytes32
    payment: PaymentConfig
    amount: Uint256String
    chainId: int
    rail0Contract: Address
    signingPayload: SigningPayload


class PayerSignatureResponse(TypedDict):
    """Returned by payments.sign()."""

    paymentId: Bytes32
    status: Literal["signature_stored"]
    recoveredPayer: Address


class AuthorizePaymentResponse(TypedDict):
    """Returned by payments.authorize()."""

    paymentId: Bytes32
    transactionHash: Bytes32
    capturableAmount: Uint256String
    authorizationExpiry: int


class ChargePaymentResponse(TypedDict):
    """Returned by payments.charge()."""

    paymentId: Bytes32
    transactionHash: Bytes32
    chargedAmount: Uint256String
    feeAmount: Uint256String
    refundableAmount: Uint256String


class PrepareTransactionResponse(TypedDict):
    """Returned by prepare operations. An unsigned EIP-1559 transaction ready for signing."""

    unsignedTransaction: str
    to: Address
    data: str
    chainId: int
    nonce: int
    maxFeePerGas: Uint256String
    maxPriorityFeePerGas: Uint256String
    gasLimit: Uint256String


class CapturePaymentResponse(TypedDict):
    """Returned by payments.submit_capture()."""

    paymentId: Bytes32
    transactionHash: Bytes32
    capturedAmount: Uint256String
    feeAmount: Uint256String
    capturableAmount: Uint256String
    refundableAmount: Uint256String
    authorizationExpiry: int


class VoidPaymentResponse(TypedDict):
    """Returned by payments.submit_void()."""

    paymentId: Bytes32
    transactionHash: Bytes32
    releasedAmount: Uint256String


class ReleasePaymentResponse(TypedDict):
    """Returned by payments.release()."""

    paymentId: Bytes32
    transactionHash: Bytes32
    releasedAmount: Uint256String


class ApproveResponse(TypedDict):
    """Returned by payments.submit_approve()."""

    transactionHash: Bytes32
    token: Address
    spender: Address
    amount: Uint256String


class RefundPaymentResponse(TypedDict):
    """Returned by payments.submit_refund()."""

    paymentId: Bytes32
    transactionHash: Bytes32
    refundedAmount: Uint256String
    refundableAmount: Uint256String


class ApiErrorBody(TypedDict):
    """Shape of error responses from the RAIL0 API."""

    code: str
    message: str
