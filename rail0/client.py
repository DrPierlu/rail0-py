from __future__ import annotations

from typing import Optional

from .core.http import HttpClient, Logger
from .resources.payments import PaymentsResource
from .resources.tokens import TokensResource
from .resources.utils import UtilsResource


class Rail0Client:
    """Entry point for the RAIL0 SDK.

    ```python
    client = Rail0Client(base_url="https://api.rail0.xyz")
    state = client.payments.get(payment_id)
    ```
    """

    payments: PaymentsResource
    """Payment lifecycle operations: authorize, charge, capture, void, release, refund."""

    tokens: TokensResource
    """Token allowlist queries."""

    utils: UtilsResource
    """Contract introspection: domain separator, version."""

    def __init__(
        self,
        base_url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
        logger: Optional[Logger] = None,
        max_retries: int = 0,
        retry_delay: float = 0.2,
    ) -> None:
        """
        Args:
            base_url: Base URL of the RAIL0 API, e.g. "https://api.rail0.xyz".
            headers: Default headers merged into every request.
            timeout: Timeout in seconds. Default: 30.
            logger: Optional logger. Pass debug_logger for built-in output.
            max_retries: Number of additional attempts after the first failure.
                Only network errors and timeouts are retried — HTTP errors are not. Default: 0.
            retry_delay: Base delay in seconds between retries.
                Doubles with each subsequent attempt (exponential backoff). Default: 0.2.
        """
        http = HttpClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            logger=logger,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        self.payments = PaymentsResource(http)
        self.tokens = TokensResource(http)
        self.utils = UtilsResource(http)
