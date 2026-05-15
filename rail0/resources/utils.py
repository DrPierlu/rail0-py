from __future__ import annotations

from ..core.http import HttpClient
from .types import DomainSeparatorResponse, VersionResponse


class UtilsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def domain_separator(self) -> DomainSeparatorResponse:
        """Returns the EIP-712 domain separator for the RAIL0 contract on the current chain."""
        return self._http.get("/domain-separator")

    def version(self) -> VersionResponse:
        """Returns the contract version number."""
        return self._http.get("/version")
