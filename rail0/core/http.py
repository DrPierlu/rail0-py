from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import httpx

from .error import Rail0ApiError


@dataclass
class LogEntry:
    """One log record emitted by the HTTP client per request attempt."""

    method: str
    url: str
    duration_ms: float
    request_body: Any = field(default=None)
    status: Optional[int] = field(default=None)
    response_body: Any = field(default=None)
    error: Optional[BaseException] = field(default=None)
    attempt: Optional[int] = field(default=None)
    will_retry: Optional[bool] = field(default=None)


Logger = Callable[[LogEntry], None]


def debug_logger(entry: LogEntry) -> None:
    """Built-in logger that writes a one-line summary to stdout.

    Pass to Rail0Client as ``logger=debug_logger`` for console output.
    """
    status = f" {entry.status}" if entry.status is not None else ""
    flag = " ERROR" if entry.error is not None else ""
    attempt_info = ""
    if entry.attempt is not None:
        retry_str = ", retrying" if entry.will_retry else ""
        attempt_info = f" [attempt {entry.attempt}{retry_str}]"

    parts = [f"[rail0]{flag}{attempt_info} {entry.method}{status} {entry.url} {entry.duration_ms:.0f}ms"]
    if entry.request_body is not None:
        parts.append(f"→ {entry.request_body}")
    if entry.response_body is not None:
        parts.append(f"← {entry.response_body}")
    if entry.error is not None:
        parts.append(f"! {entry.error}")
    print(" ".join(parts))


class HttpClient:
    def __init__(
        self,
        base_url: str,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
        logger: Optional[Logger] = None,
        max_retries: int = 0,
        retry_delay: float = 0.2,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Content-Type": "application/json", **(headers or {})}
        self._timeout = timeout
        self._logger = logger
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, body: Any = None) -> Any:
        return self._request("POST", path, body)

    def _request(self, method: str, path: str, body: Any = None) -> Any:
        url = f"{self._base_url}{path}"
        max_attempts = self._max_retries + 1
        track_attempts = self._max_retries > 0

        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                time.sleep(self._retry_delay * (2 ** (attempt - 2)))

            start = time.monotonic()
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    if method == "GET":
                        response = client.get(url, headers=self._headers)
                    else:
                        response = client.post(url, json=body, headers=self._headers)
            except (httpx.TimeoutException, httpx.NetworkError) as err:
                duration_ms = (time.monotonic() - start) * 1000
                will_retry = attempt < max_attempts
                if self._logger:
                    entry = LogEntry(
                        method=method,
                        url=url,
                        duration_ms=duration_ms,
                        request_body=body,
                        error=err,
                    )
                    if track_attempts:
                        entry.attempt = attempt
                        entry.will_retry = will_retry
                    self._logger(entry)
                if will_retry:
                    continue
                raise

            duration_ms = (time.monotonic() - start) * 1000

            if not response.is_success:
                try:
                    error_body = response.json()
                    error_name = error_body.get("error", "UnknownError")
                    error_message = error_body.get("message", f"HTTP {response.status_code}")
                except Exception:
                    error_name = "UnknownError"
                    error_message = f"HTTP {response.status_code}"

                api_error = Rail0ApiError(response.status_code, error_name, error_message)
                if self._logger:
                    entry = LogEntry(
                        method=method,
                        url=url,
                        duration_ms=duration_ms,
                        request_body=body,
                        status=response.status_code,
                        response_body={"error": error_name, "message": error_message},
                        error=api_error,
                    )
                    if track_attempts:
                        entry.attempt = attempt
                    self._logger(entry)
                raise api_error

            data = response.json()
            if self._logger:
                entry = LogEntry(
                    method=method,
                    url=url,
                    duration_ms=duration_ms,
                    request_body=body,
                    status=response.status_code,
                    response_body=data,
                )
                if track_attempts:
                    entry.attempt = attempt
                self._logger(entry)
            return data

        raise RuntimeError("unreachable")
