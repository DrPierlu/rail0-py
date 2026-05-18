from __future__ import annotations

from ..core.http import HttpClient
from .types import (
    AuthorizeParams,
    Bytes32,
    CaptureParams,
    ChargeParams,
    HashResponse,
    NonceResponse,
    Payment,
    PaymentResponse,
    RefundParams,
    ReleaseParams,
    TransactionResponse,
    VoidParams,
)


class PaymentsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get(self, payment_id: Bytes32) -> PaymentResponse:
        """Returns the current on-chain state and config hash for a payment."""
        return self._http.get(f"/payments/{payment_id}")

    def authorize(self, payment_id: Bytes32, params: AuthorizeParams) -> TransactionResponse:
        """Pull amount from the payer into escrow using an EIP-3009 transferWithAuthorization signature."""
        return self._http.post(f"/payments/{payment_id}/authorize", dict(params))

    def charge(self, payment_id: Bytes32, params: ChargeParams) -> TransactionResponse:
        """Authorize and immediately capture in a single transaction. Uses an EIP-3009 signature."""
        return self._http.post(f"/payments/{payment_id}/charge", dict(params))

    def capture(self, payment_id: Bytes32, params: CaptureParams) -> TransactionResponse:
        """Capture escrowed funds. Caller must be the payee."""
        return self._http.post(f"/payments/{payment_id}/capture", dict(params))

    def void(self, payment_id: Bytes32, params: VoidParams) -> TransactionResponse:
        """Cancel an authorization, returning escrowed funds to the payer. Caller must be the payee."""
        return self._http.post(f"/payments/{payment_id}/void", dict(params))

    def release(self, payment_id: Bytes32, params: ReleaseParams) -> TransactionResponse:
        """Return escrowed funds to the payer after authorizationExpiry. Permissionless."""
        return self._http.post(f"/payments/{payment_id}/release", dict(params))

    def refund(self, payment_id: Bytes32, params: RefundParams) -> TransactionResponse:
        """Refund a previously captured amount from the payee to the payer. Caller must be the payee."""
        return self._http.post(f"/payments/{payment_id}/refund", dict(params))

    def authorize_nonce(self, payment_id: Bytes32, config_hash: Bytes32) -> NonceResponse:
        """Returns the EIP-3009 nonce the payer must use when signing an authorize call.

        config_hash is the EIP-712 digest of the Payment configuration (from payments.hash()).
        """
        return self._http.get(f"/payments/{payment_id}/authorize-nonce?configHash={config_hash}")

    def charge_nonce(self, payment_id: Bytes32, config_hash: Bytes32) -> NonceResponse:
        """Returns the EIP-3009 nonce the payer must use when signing a charge call.

        config_hash is the EIP-712 digest of the Payment configuration (from payments.hash()).
        """
        return self._http.get(f"/payments/{payment_id}/charge-nonce?configHash={config_hash}")

    def hash(self, payment: Payment) -> HashResponse:
        """Compute the canonical EIP-712 digest of a Payment configuration."""
        return self._http.post("/payments/hash", dict(payment))
