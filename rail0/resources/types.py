"""
Public types for the RAIL0 Python SDK.

All types mirror the OpenAPI schema in rail0-api/doc/openapi.json.
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
    """Immutable payment configuration that maps 1-to-1 to the RAIL0 `Payment` Solidity struct."""

    payer: Address
    payee: Address
    token: Address
    amount: Uint256String
    authorizationExpiry: int
    refundExpiry: int
    feeBps: int
    feeReceiver: Address


class PaymentInput(TypedDict):
    """Buyer-supplied payment parameters. Policy fields (amount, authorizationExpiry, refundExpiry, feeBps, feeReceiver) are fixed API configuration and are applied server-side — they are not accepted in input but appear in CreatePaymentResponse.payment."""

    payer: Address
    payee: Address
    token: Address


class EIP712Domain(TypedDict):
    """EIP-712 domain for the token contract (used by EIP-3009 TransferWithAuthorization)."""

    name: str
    version: str
    chainId: int
    verifyingContract: Address


class EIP3009Message(TypedDict):
    """Message fields for the EIP-3009 TransferWithAuthorization typed-data signature."""

    # JSON key: "from"
    from_: Address
    to: Address
    value: Uint256String
    validAfter: Uint256String
    validBefore: Uint256String
    nonce: Bytes32


class SigningPayload(TypedDict):
    """EIP-712 typed-data structure that the payer must sign. The `domain`, `types`, and `message` fields follow the EIP-712 standard. Signing options: (a) wallet users pass this object verbatim to `eth_signTypedData_v4`; (b) backends with direct key access compute `keccak256('\x19\x01' || domainSeparator || hashStruct(message))` with any EIP-712 library and sign with secp256k1. Both approaches produce the same 65-byte signature to submit to `PUT /payments/{paymentId}/sign`."""

    domain: EIP712Domain
    types: Dict[str, Any]
    primaryType: Literal["TransferWithAuthorization"]
    message: EIP3009Message


# ================================================================
#  Request bodies
# ================================================================


class _CreatePaymentRequestRequired(TypedDict):
    """Parameters needed to create a payment intent. The API generates a unique `paymentId`, applies its fixed policy config, and constructs the EIP-712 signing payload."""

    payment: PaymentInput
    chainId: int


class CreatePaymentRequest(_CreatePaymentRequestRequired, total=False):
    mode: Literal["authorize", "charge"]


class PayerSignatureRequest(TypedDict):
    """EIP-712 signature over the `signingPayload` returned by `POST /payments`. Browser wallets return this directly from `eth_signTypedData_v4`; backends produce it with any EIP-712 library. The on-chain verification only checks the recovered address."""

    signature: str


class CapturePaymentRequest(TypedDict):
    """Amount to capture from escrow. May be less than the total capturable balance for a partial capture."""

    amount: Uint256String


class SubmitTransactionRequest(TypedDict):
    """Signed transaction to submit on-chain."""

    signedTransaction: str


class ApproveRequest(TypedDict):
    """Amount to approve on the token contract. Setting this to the maximum expected refund (or `type(uint256).max` for unlimited) avoids repeated approvals."""

    amount: Uint256String


class RefundPaymentRequest(TypedDict):
    """Amount to refund to the payer. Must be > 0 and <= current refundableAmount."""

    amount: Uint256String


# ================================================================
#  Response shapes
# ================================================================


class CreatePaymentResponse(TypedDict):
    paymentId: Bytes32
    configHash: Bytes32
    payment: PaymentConfig
    chainId: int
    rail0Contract: Address
    signingPayload: SigningPayload


class _PayerSignatureResponseRequired(TypedDict):
    paymentId: Bytes32
    status: Literal["signature_stored"]


class PayerSignatureResponse(_PayerSignatureResponseRequired, total=False):
    recoveredPayer: Address


class _AuthorizePaymentResponseRequired(TypedDict):
    paymentId: Bytes32
    transactionHash: Bytes32
    capturableAmount: Uint256String


class AuthorizePaymentResponse(_AuthorizePaymentResponseRequired, total=False):
    authorizationExpiry: int


class ChargePaymentResponse(TypedDict):
    paymentId: Bytes32
    transactionHash: Bytes32
    chargedAmount: Uint256String
    feeAmount: Uint256String
    refundableAmount: Uint256String


class PrepareTransactionResponse(TypedDict):
    """An unsigned EIP-1559 transaction ready for the payee to sign. Signing options: (a) wallet users pass `unsignedTransaction` to `eth_signTransaction`; (b) backends with direct key access sign the RLP blob with any secp256k1 library (e.g. `wallet.signTransaction` in ethers.js). Submit the resulting signed RLP to the corresponding `/submit` endpoint."""

    unsignedTransaction: str
    to: Address
    data: str
    chainId: int
    nonce: int
    maxFeePerGas: Uint256String
    maxPriorityFeePerGas: Uint256String
    gasLimit: Uint256String


class _CapturePaymentResponseRequired(TypedDict):
    paymentId: Bytes32
    transactionHash: Bytes32
    capturedAmount: Uint256String
    capturableAmount: Uint256String
    refundableAmount: Uint256String


class CapturePaymentResponse(_CapturePaymentResponseRequired, total=False):
    feeAmount: Uint256String
    authorizationExpiry: int


class VoidPaymentResponse(TypedDict):
    paymentId: Bytes32
    transactionHash: Bytes32
    releasedAmount: Uint256String


class ReleasePaymentResponse(TypedDict):
    paymentId: Bytes32
    transactionHash: Bytes32
    releasedAmount: Uint256String


class ApproveResponse(TypedDict):
    transactionHash: Bytes32
    token: Address
    spender: Address
    amount: Uint256String


class RefundPaymentResponse(TypedDict):
    paymentId: Bytes32
    transactionHash: Bytes32
    refundedAmount: Uint256String
    refundableAmount: Uint256String


class PaymentMethod(TypedDict):
    """A single accepted payment method for a merchant: one (chain, token, wallet) combination."""

    id: int
    tokenId: int
    chainId: int
    chainName: str
    chainSlug: str
    explorerUrl: str
    tokenAddress: Address
    tokenSymbol: str
    tokenDecimals: int
    walletAddress: Address
    isDefault: bool


class OnChainState(TypedDict):
    """Live on-chain escrow balances for a payment."""

    exists: bool
    capturableAmount: Uint256String
    refundableAmount: Uint256String


class _PaymentResponseRequired(TypedDict):
    paymentId: Bytes32
    status: str
    mode: str
    amount: Uint256String
    payer: Address
    payee: Address
    token: Address
    chainId: int
    authorizationExpiry: int
    refundExpiry: int


class PaymentResponse(_PaymentResponseRequired, total=False):
    """Returned by payments.get(). Combines DB status with live on-chain balances."""

    onChain: OnChainState


class ReleaseRequest(TypedDict, total=False):
    """Optional body for payments.prepare_release(). Pass callerAddress for buyer-initiated release."""

    callerAddress: Address


class SubmitApproveRequest(TypedDict):
    """Body for payments.submit_approve(). Include amount so the API records it."""

    signedTransaction: str
    amount: Uint256String  # optional but recommended


class ApiErrorBody(TypedDict):
    code: str
    message: str
