# GENERATED — DO NOT EDIT. Run `python gen/generate.py` to regenerate.
from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ..core.http import HttpClient
from .types import PageMeta, PaginatedResponse, PaymentMethod, WalletToken


class AccountsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def payment_methods(self, account_id: str) -> List[PaymentMethod]:
        """Return the active payment methods (chain + token + wallet) for the given account."""
        return self._http.get(f"/accounts/{account_id}/payment-methods")

    def wallets(
        self,
        account_id: str,
        *,
        chain_id: Optional[int] = None,
        chain_slug: Optional[str] = None,
        token_symbol: Optional[str] = None,
        active: Optional[bool] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> PaginatedResponse:
        """List wallet tokens for an account. Public — no JWT required."""
        params: Dict[str, Any] = {}
        if chain_id is not None:
            params["chain_id"] = chain_id
        if chain_slug is not None:
            params["chain_slug"] = chain_slug
        if token_symbol is not None:
            params["token_symbol"] = token_symbol
        if active is not None:
            params["active"] = "true" if active else "false"
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        qs = ("?" + urlencode(params)) if params else ""
        return self._http.get(f"/accounts/{account_id}/wallets{qs}")

    def wallet(self, account_id: str, wallet_id: str) -> WalletToken:
        """Fetch a single wallet token by id for the given account."""
        return self._http.get(f"/accounts/{account_id}/wallets/{wallet_id}")
