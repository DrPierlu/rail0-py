from __future__ import annotations

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
    PrepareTransactionResponse,
    RefundPaymentRequest,
    RefundPaymentResponse,
    ReleasePaymentResponse,
    SubmitTransactionRequest,
    VoidPaymentResponse,
)


class PaymentsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create_payment(self, params: CreatePaymentRequest) -> CreatePaymentResponse:
        """Create a payment intent. Returns the EIP-712 signingPayload for the payer to sign."""
        return self._http.post("/payments", dict(params))

    def sign(self, payment_id: Bytes32, params: PayerSignatureRequest) -> PayerSignatureResponse:
        """Submit the payer's EIP-712 signature (v, r, s)."""
        return self._http.put(f"/payments/{payment_id}/sign", dict(params))

    def authorize(self, payment_id: Bytes32) -> AuthorizePaymentResponse:
        """Relay the stored EIP-3009 signature to the RAIL0 authorize() function. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/authorize")

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

    def release(self, payment_id: Bytes32) -> ReleasePaymentResponse:
        """Release escrowed funds back to the payer after authorizationExpiry. Permissionless."""
        return self._http.post(f"/payments/{payment_id}/release")

    def prepare_approve(self, payment_id: Bytes32, params: ApproveRequest) -> PrepareTransactionResponse:
        """Build the unsigned ERC-20 approve() transaction needed before a refund. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/approve", dict(params))

    def submit_approve(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> ApproveResponse:
        """Broadcast a signed ERC-20 approve transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/approve/submit", dict(params))

    def prepare_refund(self, payment_id: Bytes32, params: RefundPaymentRequest) -> PrepareTransactionResponse:
        """Build the unsigned refund() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/refund", dict(params))

    def submit_refund(self, payment_id: Bytes32, params: SubmitTransactionRequest) -> RefundPaymentResponse:
        """Broadcast a signed refund transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/refund/submit", dict(params))
