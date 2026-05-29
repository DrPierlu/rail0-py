from __future__ import annotations

from typing import List

from ..core.http import HttpClient
from .types import PaymentMethod


class AccountsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def payment_methods(self, account_id: int) -> List[PaymentMethod]:
        """Return the active payment methods (chain + token + wallet) for the given merchant."""
        return self._http.get(f"/accounts/{account_id}/payment-methods")
