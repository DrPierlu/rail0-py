# GENERATED — DO NOT EDIT. Run `python gen/generate.py` to regenerate.
from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ..core.http import HttpClient
from .types import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    CapturePaymentRequest,
    PageMeta,
    PaginatedResponse,
    PayerSignatureRequest,
    PayerSignatureResponse,
    PrepareTransactionResponse,
    RefundPhase1Response,
    RefundPhase2Response,
    ReleaseRequest,
    SubmitTransactionRequest,
    SubmitTransactionAcceptedResponse,
    WalletToken,
)


class PaymentsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        *,
        status: Optional[str] = None,
        mode: Optional[str] = None,
        payer: Optional[str] = None,
        payee: Optional[str] = None,
        token: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> PaginatedResponse:
        """List payments for the authenticated wallet (requires JWT)."""
        params: Dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if mode is not None:
            params["mode"] = mode
        if payer is not None:
            params["payer"] = payer
        if payee is not None:
            params["payee"] = payee
        if token is not None:
            params["token"] = token
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        qs = ("?" + urlencode(params)) if params else ""
        return self._http.get(f"/payments{qs}")

    def create(self, params: CreatePaymentRequest) -> CreatePaymentResponse:
        """Create a payment intent. Returns the EIP-712 signingPayload for the payer to sign."""
        return self._http.post("/payments", dict(params))

    def get(self, rail0_id: str) -> Any:
        """Fetch current payment state (DB status + live on-chain amounts)."""
        return self._http.get(f"/payments/{rail0_id}")

    def transactions(
        self,
        rail0_id: str,
        *,
        operation: Optional[str] = None,
        status: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> PaginatedResponse:
        """List on-chain transactions for a payment."""
        params: Dict[str, Any] = {}
        if operation is not None:
            params["operation"] = operation
        if status is not None:
            params["status"] = status
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        qs = ("?" + urlencode(params)) if params else ""
        return self._http.get(f"/payments/{rail0_id}/transactions{qs}")

    def sign(self, payment_id: str, params: PayerSignatureRequest) -> PayerSignatureResponse:
        """Submit the payer's EIP-712 signature (v, r, s)."""
        return self._http.put(f"/payments/{payment_id}/sign", dict(params))

    # ── Authorize ────────────────────────────────────────────────────────

    def authorize_prepare(self, payment_id: str) -> PrepareTransactionResponse:
        """Prepare the unsigned authorize() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/authorize/prepare")

    def authorize(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed authorize transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/authorize", dict(params))

    # ── Charge ───────────────────────────────────────────────────────────

    def charge_prepare(self, payment_id: str) -> PrepareTransactionResponse:
        """Prepare the unsigned charge() transaction (one-shot, no escrow). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/charge/prepare")

    def charge(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed charge transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/charge", dict(params))

    # ── Capture ──────────────────────────────────────────────────────────

    def capture_prepare(self, payment_id: str, params: CapturePaymentRequest) -> PrepareTransactionResponse:
        """Build the unsigned capture() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/capture/prepare", dict(params))

    def capture(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed capture transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/capture", dict(params))

    # ── Void ─────────────────────────────────────────────────────────────

    def void_prepare(self, payment_id: str) -> PrepareTransactionResponse:
        """Build the unsigned void() transaction. Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/void/prepare")

    def void(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed void transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/void", dict(params))

    # ── Release ──────────────────────────────────────────────────────────

    def release_prepare(self, payment_id: str, params: Optional[ReleaseRequest] = None) -> PrepareTransactionResponse:
        """Build the unsigned release() transaction."""
        return self._http.post(f"/payments/{payment_id}/release/prepare", dict(params) if params else None)

    def release(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed release transaction (HTTP 202, async)."""
        return self._http.post(f"/payments/{payment_id}/release", dict(params))

    # ── Refund (EIP-3009) ────────────────────────────────────────────────

    def refund_prepare(self, payment_id: str, amount: str, *, signature: Optional[str] = None):
        """Two-phase EIP-3009 refund flow.

        Phase 1 — pass only amount: returns a signing payload (RefundPhase1Response).
        Phase 2 — pass amount + signature (0x-prefixed hex): returns unsigned refund transaction (RefundPhase2Response).
        """
        params: Dict[str, Any] = {"amount": amount}
        if signature is not None:
            params["signature"] = signature
        return self._http.post(f"/payments/{payment_id}/refund/prepare", params)

    def refund(self, payment_id: str, params: SubmitTransactionRequest) -> SubmitTransactionAcceptedResponse:
        """Broadcast a signed refund transaction (HTTP 202, async). Called by the payee."""
        return self._http.post(f"/payments/{payment_id}/refund", dict(params))
