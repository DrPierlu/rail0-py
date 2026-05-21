from __future__ import annotations

from typing import List

from ..core.http import HttpClient
from .types import PaymentMethod


class MerchantsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def payment_methods(self, merchant_id: int) -> List[PaymentMethod]:
        """Return the active payment methods (chain + token + wallet) for the given merchant."""
        return self._http.get(f"/merchants/{merchant_id}/payment-methods")
