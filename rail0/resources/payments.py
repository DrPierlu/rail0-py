from __future__ import annotations

from typing import List, Optional

from ..core.http import HttpClient
from .types import (
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
    RefundPaymentResponse,
    ReleasePaymentResponse,
    ReleaseRequest,
    SubmitTransactionRequest,
    VoidPaymentResponse,
)


class PaymentsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> List[PaymentResponse]:
        """List payments for the authenticated account. Requires authentication."""
        return self._http.get("/payments")

    def get(self, payment_id: Bytes32) -> PaymentResponse:
        """Fetch current payment state (DB status + live on-chain escrow balances)."""
        return self._http.get(f"/payments/{payment_id}")

    def create_payment(self, params: CreatePaymentRequest) -> CreatePaymentResponse:
        """Create a payment intent. Returns the EIP-712 signingPayload for the payer to sign."""
        return self._http.post("/payments", dict(params))

    def sign(self, payment_id: Bytes32, params: PayerSignatureRequest) -> PayerSignatureResponse:
        """Submit the payer's EIP-712 signature (v, r, s)."""
        return self._http.put(f"/payments/{payment_id}/sign", dict(params))

    def authorize_payload(self, payment_id: Bytes32) -> PrepareTransactionResponse:
        """Prepare the unsigned authorize() transaction. Called by the payee.
        Sign unsignedTransaction with the payee's key and pass to authorize().
        """
        return self._http.post(f"/payments/{payment_id}/authorize/payload")

    def authorize(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> AuthorizePaymentResponse:
        """Broadcast a signed authorize transaction (HTTP 202, async). Called by the payee.
        Poll get() until status leaves 'submitting'.
        """
        return self._http.post(f"/payments/{payment_id}/authorize", dict(params))

    def charge_payload(self, payment_id: Bytes32) -> PrepareTransactionResponse:
        """Prepare the unsigned charge() transaction (one-shot, no escrow). Called by the payee.
        The payer signature must have been submitted first via sign().
        """
        return self._http.post(f"/payments/{payment_id}/charge/payload")

    def charge(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> ChargePaymentResponse:
        """Broadcast a signed charge transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/charge", dict(params))

    def capture_payload(self, payment_id: Bytes32, params: CapturePaymentRequest) -> PrepareTransactionResponse:
        """Build the unsigned capture() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/capture/payload", dict(params))

    def capture(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> CapturePaymentResponse:
        """Broadcast a signed capture transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/capture", dict(params))

    def void_payload(self, payment_id: Bytes32) -> PrepareTransactionResponse:
        """Build the unsigned void() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/void/payload")

    def void(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> VoidPaymentResponse:
        """Broadcast a signed void transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/void", dict(params))

    def release_payload(self, payment_id: Bytes32, params: Optional[ReleaseRequest] = None) -> PrepareTransactionResponse:
        """Build the unsigned release() transaction.
        Pass params with callerAddress to build the tx for the buyer (payer).
        release() can only succeed after authorizationExpiry has passed on-chain.
        """
        return self._http.post(f"/payments/{payment_id}/release/payload", dict(params) if params else None)

    def release(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> ReleasePaymentResponse:
        """Broadcast a signed release transaction (HTTP 202, async)."""
        return self._http.post(f"/payments/{payment_id}/release", dict(params))

    def refund_payload(self, payment_id: Bytes32, params: dict) -> PrepareTransactionResponse:
        """Two-phase EIP-3009 receiveWithAuthorization refund payload. Called by the payee.

        Phase 1 — pass {"amount": "..."} only:
            Returns the EIP-3009 signing payload. Sign off-chain to obtain v, r, s.

        Phase 2 — pass {"amount": "...", "v": ..., "r": "...", "s": "..."}:
            Returns the unsigned on-chain refund transaction ready to sign and submit.

        No ERC-20 approve step is required (uses EIP-3009).
        """
        return self._http.post(f"/payments/{payment_id}/refund/payload", params)

    def refund(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> RefundPaymentResponse:
        """Broadcast a signed refund transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/refund", dict(params))
