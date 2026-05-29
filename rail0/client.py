from __future__ import annotations

from typing import Optional

from .core.http import HttpClient, Logger
from .resources.accounts import AccountsResource
from .resources.chains import ChainsResource
from .resources.tokens import TokensResource
from .resources.payments import PaymentsResource


class Rail0Client:
    """Entry point for the RAIL0 SDK.

    ```python
    client = Rail0Client(base_url="https://api.rail0.xyz")
    methods = client.accounts.payment_methods(1)
    resp = client.payments.create_payment({"payment": config, "chainId": 84532, "mode": "authorize"})
    ```
    """

    accounts: AccountsResource
    """Account configuration operations: payment_methods."""

    chains: ChainsResource
    """Supported blockchain catalog: list."""

    tokens: TokensResource
    """Supported token catalog: list."""

    payments: PaymentsResource
    """Payment lifecycle operations: get, create_payment, sign, authorize, submit_authorize,
    charge, prepare_capture, submit_capture, prepare_void, submit_void, prepare_release,
    submit_release, prepare_approve, submit_approve, prepare_refund, submit_refund."""

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
        self.accounts = AccountsResource(http)
        self.chains = ChainsResource(http)
        self.tokens = TokensResource(http)
        self.payments = PaymentsResource(http)
