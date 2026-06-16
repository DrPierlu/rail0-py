# GENERATED — DO NOT EDIT. Run `python gen/generate.py` to regenerate.
"""
Public types for the RAIL0 Python SDK.

All types mirror the OpenAPI schema in rail0-api/docs/openapi.json.
Request / response bodies use camelCase keys to match the JSON wire format.

This file is generated — do not hand-edit. Run `python gen/generate.py` to regenerate.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal
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
    """Immutable payment configuration returned by the API (e.g. in CreatePaymentResponse).

    Contains the full on-chain payment terms including server-applied policy fields
    (authorization_expiry, refund_expiry).
    """

    payer: Address
    payee: Address
    token: Address
    amount: Uint256String
    authorization_expiry: int
    refund_expiry: int


class EIP712Domain(TypedDict):
    """EIP-712 domain for the token contract."""

    name: str
    version: str
    chainId: int
    verifyingContract: Address


class EIP3009Message(TypedDict):
    """Message fields for the EIP-3009 TransferWithAuthorization signature."""

    # JSON key: "from"
    from_: Address
    to: Address
    value: Uint256String
    validAfter: Uint256String
    validBefore: Uint256String
    nonce: Bytes32


class SigningPayload(TypedDict):
    """EIP-712 typed-data structure that the payer (or payee for refund) must sign. Pass verbatim to `eth_signTypedData_v4`."""

    domain: EIP712Domain
    types: Dict[str, Any]
    primaryType: Literal["TransferWithAuthorization", "ReceiveWithAuthorization"]
    message: EIP3009Message


# ================================================================
#  Request bodies
# ================================================================


class _CreatePaymentRequestRequired(TypedDict):
    """Parameters needed to create a payment intent.

    All fields are flat — there is no nested ``payment`` object.
    """

    chain_id: int
    amount: Uint256String
    token: Address
    payer: Address
    payee: Address


class CreatePaymentRequest(_CreatePaymentRequestRequired, total=False):
    mode: Literal["authorize", "charge"]
    description: str
    metadata: Dict[str, Any]


class PayerSignatureRequest(TypedDict):
    """EIP-712 signature over the `signing_payload` returned by `POST /payments`."""

    signature: str


class CapturePaymentRequest(TypedDict):
    """Amount to capture from escrow. May be less than `capturable_amount` for a partial capture."""

    amount: Uint256String


class SubmitTransactionRequest(TypedDict):
    """Signed transaction to broadcast on-chain."""

    signed_transaction: str


class SubmitTransactionAcceptedResponse(TypedDict):
    """Acknowledgement that the transaction has been enqueued. Poll `GET /payments/{rail0_id}` for the final outcome."""

    rail0_id: Bytes32
    status: Literal["submitting"]


class ReleaseRequest(TypedDict, total=False):
    """Optional parameters for the release prepare step."""

    caller_address: Address


class RefundPaymentRequest(TypedDict):
    """Amount to refund to the payer."""

    amount: Uint256String


# ================================================================
#  Response shapes
# ================================================================


class _CreatePaymentResponseRequired(TypedDict):
    rail0_id: Bytes32
    config_hash: Bytes32
    payment: PaymentConfig
    chain_id: int
    rail0_contract: Address
    signing_payload: SigningPayload


class CreatePaymentResponse(_CreatePaymentResponseRequired, total=False):
    description: str
    metadata: Dict[str, Any]


class PayerSignatureResponse(TypedDict):
    rail0_id: Bytes32
    status: Literal["signature_stored"]
    recovered_payer: Address


class _GetPaymentResponseRequired(TypedDict):
    """Current state of a payment record."""

    rail0_id: Bytes32
    status: Literal["unsigned", "signed", "submitting", "submitted", "authorized", "charged", "captured", "partially_captured", "voided", "released", "refunded", "partially_refunded", "failed"]
    mode: Literal["authorize", "charge"]
    amount: Uint256String
    payer: Address
    payee: Address
    token: Address
    chain_id: int
    authorization_expiry: int
    refund_expiry: int


class GetPaymentResponse(_GetPaymentResponseRequired, total=False):
    description: str
    metadata: Dict[str, Any]
    on_chain: Dict[str, Any]
    last_broadcast_hash: Bytes32
    failure_code: str
    failure_message: str


class PrepareTransactionResponse(TypedDict):
    """An unsigned EIP-1559 transaction ready for the payee to sign."""

    unsigned_transaction: str
    transaction_id: str
    to: Address
    data: str
    chainId: int
    nonce: int
    maxFeePerGas: Uint256String
    maxPriorityFeePerGas: Uint256String
    gasLimit: Uint256String


class RefundPhase1Response(TypedDict):
    """Response from refund_prepare phase 1 — contains the EIP-3009 signing payload."""

    signing_payload: SigningPayload


class RefundPhase2Response(TypedDict):
    """Response from refund_prepare phase 2 — contains the unsigned on-chain refund transaction."""

    unsigned_transaction: str
    transaction_id: str


class RefundPrepareResponse(TypedDict, total=False):
    """Union response from refund_prepare — phase 1 returns signing_payload, phase 2 returns unsigned_transaction."""

    signing_payload: SigningPayload
    unsigned_transaction: str


class PaymentMethod(TypedDict):
    """A single accepted payment method for a account: one (chain, token, wallet) combination."""

    id: int
    token_id: int
    chain_id: int
    chain_name: str
    token_address: Address
    token_symbol: str
    token_decimals: int
    wallet_address: Address
    default: bool


class _WalletTokenRequired(TypedDict):
    """A wallet token configuration linking a wallet address to a specific token on a chain."""

    id: str
    wallet_id: str
    address: Address
    default: bool
    active: bool
    token_id: str
    token_symbol: str
    token_address: Address
    token_decimals: int
    chain_id: int
    chain_name: str
    chain_slug: str


class WalletToken(_WalletTokenRequired, total=False):
    label: str


class _PaymentSummaryRequired(TypedDict):
    """Condensed payment record returned by GET /payments."""

    rail0_id: Bytes32
    status: str
    mode: Literal["authorize", "charge"]
    amount: str
    payer: Address
    payee: Address
    token: Address
    authorization_expiry: int
    refund_expiry: int
    created_at: str


class PaymentSummary(_PaymentSummaryRequired, total=False):
    description: str
    metadata: Dict[str, Any]


class _TransactionRecordRequired(TypedDict):
    """An on-chain transaction attempt associated with a payment."""

    id: str
    operation: Literal["authorize", "charge", "capture", "void", "release", "refund"]
    status: Literal["pending", "submitting", "submitted", "confirmed", "failed"]
    fee_amount: str


class TransactionRecord(_TransactionRecordRequired, total=False):
    transaction_hash: Bytes32
    amount: str
    block_number: int
    error_reason: str
    pending_at: str
    submitted_at: str
    confirmed_at: str


class _TransactionRequired(TypedDict):
    """A blockchain transaction associated with a payment."""

    transaction_hash: Bytes32
    rail0_id: Bytes32
    operation: Literal["authorize", "charge", "capture", "void", "refund", "release"]
    status: Literal["submitted", "confirmed", "failed"]
    fee_amount: Uint256String
    submitted_at: str


class Transaction(_TransactionRequired, total=False):
    amount: Uint256String
    block_number: int
    confirmed_at: str


class ApiErrorBody(TypedDict):
    message: str
    code: str



# ================================================================
#  Other
# ================================================================


class _ConfirmTransactionRequestRequired(TypedDict):
    """Payload sent by the rail0-indexer when an on-chain event is detected for a known transaction."""

    payment_id: Bytes32
    event_type: Literal["authorized", "charged", "captured", "voided", "released", "refunded"]
    block_number: int


class ConfirmTransactionRequest(_ConfirmTransactionRequestRequired, total=False):
    amount: Uint256String


class _AccountRequired(TypedDict):
    """A RAIL0 merchant account."""

    id: str
    name: str
    slug: str
    email: str
    active: bool
    created_at: str


class Account(_AccountRequired, total=False):
    updated_at: str



# ================================================================
#  Pagination helpers (not in OpenAPI spec)
# ================================================================


class PageMeta(TypedDict):
    """Pagination metadata returned by list endpoints."""

    page: int
    per_page: int
    total: int


class PaginatedResponse(TypedDict):
    """Generic paginated list response."""

    data: List[Any]
    meta: PageMeta
