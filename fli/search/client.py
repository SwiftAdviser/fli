"""HTTP client implementation with impersonation, rate limiting and retry functionality.

This module provides a robust HTTP client that handles:
- User agent impersonation (to mimic a browser)
- Rate limiting (10 requests per second)
- Automatic retries with exponential backoff
- Session management
- Error handling
"""

import os
from typing import Any

from curl_cffi import requests
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential

client = None


class Client:
    """HTTP client with built-in rate limiting, retry and user agent impersonation functionality."""

    DEFAULT_HEADERS = {
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "accept-language": "en-US,en;q=0.9",
    }
    DEFAULT_PARAMS = {
        "hl": "en-US",
        "gl": "US",
        "curr": "USD",
    }

    def __init__(self):
        """Initialize a new client session with default headers."""
        self._client = requests.Session()
        self._client.headers.update(self._headers())

    def __del__(self):
        """Clean up client session on deletion."""
        if hasattr(self, "_client"):
            self._client.close()

    @sleep_and_retry
    @limits(calls=10, period=1)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(), reraise=True)
    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a rate-limited GET request with automatic retries.

        Args:
            url: Target URL for the request
            **kwargs: Additional arguments passed to requests.get()

        Returns:
            Response object from the server

        Raises:
            Exception: If request fails after all retries

        """
        try:
            response = self._client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            raise Exception(f"GET request failed: {str(e)}") from e

    @sleep_and_retry
    @limits(calls=10, period=1)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(), reraise=True)
    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a rate-limited POST request with automatic retries.

        Args:
            url: Target URL for the request
            **kwargs: Additional arguments passed to requests.post()

        Returns:
            Response object from the server

        Raises:
            Exception: If request fails after all retries

        """
        try:
            response = self._client.post(url, **self._with_default_params(kwargs))
            response.raise_for_status()
            return response
        except Exception as e:
            raise Exception(f"POST request failed: {str(e)}") from e

    @classmethod
    def _headers(cls) -> dict[str, str]:
        """Build request headers, allowing deployment-specific locale overrides."""
        language = os.getenv("FLI_GOOGLE_LANGUAGE", cls.DEFAULT_PARAMS["hl"])
        return {**cls.DEFAULT_HEADERS, "accept-language": f"{language},en;q=0.9"}

    @classmethod
    def _default_params(cls) -> dict[str, str]:
        """Build Google Flights locale params.

        Google determines result currency from request locale/IP. Explicit locale params keep
        server-side MCP deployments from inheriting the VPS region, e.g. GBP on UK-hosted servers.
        """
        return {
            "hl": os.getenv("FLI_GOOGLE_LANGUAGE", cls.DEFAULT_PARAMS["hl"]),
            "gl": os.getenv("FLI_GOOGLE_REGION", cls.DEFAULT_PARAMS["gl"]),
            "curr": os.getenv("FLI_GOOGLE_CURRENCY", cls.DEFAULT_PARAMS["curr"]).upper(),
        }

    @classmethod
    def _with_default_params(cls, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Merge caller params with locale defaults."""
        params = {**cls._default_params(), **(kwargs.get("params") or {})}
        return {**kwargs, "params": params}


def get_client() -> Client:
    """Get or create a shared HTTP client instance.

    Returns:
        Singleton instance of the HTTP client

    """
    global client
    if not client:
        client = Client()
    return client
