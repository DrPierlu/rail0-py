from __future__ import annotations

from typing import Optional

from ..core.http import HttpClient
from .types import (
    ApproveRequest,
    ApproveResponse,
    AuthorizePaymentResponse,
    Bytes32,
    CapturePaymentRequest,
    CapturePaymentResponse,
    ChargePaymentResponse,
    CreatePaymentRequest,
    CreatePaymentResponse,
    PayerSignatureRequest,
    PayerSignatureResponse,
    PaymentResponse,
    PrepareTransactionResponse,
    RefundPaymentRequest,
    RefundPaymentResponse,
    ReleasePaymentResponse,
    ReleaseRequest,
    SubmitApproveRequest,
    SubmitTransactionRequest,
    VoidPaymentResponse,
)


class PaymentsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get(self, payment_id: Bytes32) -> PaymentResponse:
        """Fetch current payment state (DB status + live on-chain escrow balances)."""
        return self._http.get(f"/payments/{payment_id}")

    def create_payment(self, params: CreatePaymentRequest) -> CreatePaymentResponse:
        """Create a payment intent. Returns the EIP-712 signingPayload for the payer to sign."""
        return self._http.post("/payments", dict(params))

    def sign(self, payment_id: Bytes32, params: PayerSignatureRequest) -> PayerSignatureResponse:
        """Submit the payer's EIP-712 signature (v, r, s)."""
        return self._http.put(f"/payments/{payment_id}/sign", dict(params))

    def authorize(self, payment_id: Bytes32) -> PrepareTransactionResponse:
        """Prepare the unsigned authorize() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/authorize")

    def submit_authorize(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> AuthorizePaymentResponse:
        """Broadcast a signed authorize transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/authorize/submit", dict(params))

    def charge(self, payment_id: Bytes32) -> ChargePaymentResponse:
        """Relay the stored EIP-3009 signature to the RAIL0 charge() function (one-shot). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/charge")

    def prepare_capture(self, payment_id: Bytes32, params: CapturePaymentRequest) -> PrepareTransactionResponse:
        """Build the unsigned capture() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/capture", dict(params))

    def submit_capture(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> CapturePaymentResponse:
        """Broadcast a signed capture transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/capture/submit", dict(params))

    def prepare_void(self, payment_id: Bytes32) -> PrepareTransactionResponse:
        """Build the unsigned void() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/void")

    def submit_void(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> VoidPaymentResponse:
        """Broadcast a signed void transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/void/submit", dict(params))

    def prepare_release(self, payment_id: Bytes32, params: Optional[ReleaseRequest] = None) -> PrepareTransactionResponse:
        """Build the unsigned release() transaction.
        Pass params with callerAddress to build the tx for the buyer (payer).
        release() can only succeed after authorizationExpiry has passed on-chain.
        """
        return self._http.post(f"/payments/{payment_id}/release", dict(params) if params else None)

    def submit_release(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> ReleasePaymentResponse:
        """Broadcast a signed release transaction."""
        return self._http.post(f"/payments/{payment_id}/release/submit", dict(params))

    def prepare_approve(self, payment_id: Bytes32, params: ApproveRequest) -> PrepareTransactionResponse:
        """Build the unsigned ERC-20 approve() transaction needed before a refund. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/approve", dict(params))

    def submit_approve(self, payment_id: Bytes32, params: SubmitApproveRequest) -> ApproveResponse:
        """Broadcast a signed ERC-20 approve transaction. Called by the payee.
        Include amount in params so the API records it in the transaction log.
        """
        return self._http.post(f"/payments/{payment_id}/approve/submit", dict(params))

    def prepare_refund(self, payment_id: Bytes32, params: RefundPaymentRequest) -> PrepareTransactionResponse:
        """Build the unsigned refund() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/refund", dict(params))

    def submit_refund(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> RefundPaymentResponse:
        """Broadcast a signed refund transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/refund/submit", dict(params))
