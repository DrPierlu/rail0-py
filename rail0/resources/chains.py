from __future__ import annotations
from typing import List, TypedDict
from ..core.http import HttpClient


class Blockchain(TypedDict):
    chain_id: int
    name: str
    slug: str
    network_type: str
    explorer_url: str


class ChainsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> List[Blockchain]:
        return self._http.get("/blockchains")
