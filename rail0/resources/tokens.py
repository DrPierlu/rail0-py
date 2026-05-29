from __future__ import annotations
from typing import List, Optional, TypedDict
from ..core.http import HttpClient


class Token(TypedDict):
    chain_id: int
    chain_slug: str
    symbol: str
    address: str
    decimals: int


class TokensResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, chain_id: Optional[int] = None) -> List[Token]:
        path = f"/tokens?chain_id={chain_id}" if chain_id else "/tokens"
        return self._http.get(path)
