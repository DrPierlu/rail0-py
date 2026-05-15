from __future__ import annotations

from ..core.http import HttpClient
from .types import Address, TokenStatusResponse


class TokensResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def is_accepted(self, address: Address) -> TokenStatusResponse:
        """Returns whether the given ERC-20 token is in this deployment's allowlist."""
        return self._http.get(f"/tokens/{address}")
