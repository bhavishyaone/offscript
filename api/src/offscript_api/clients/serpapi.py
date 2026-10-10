"""SerpApi client for Google Search lookups (AGENTS.md B2 & B3).

Time budget: 10 seconds per call.
Handles organic results extraction and honest failure modes.
"""

from typing import Any

import httpx

from offscript_contract.route_dto import SearchSource


class SerpApiError(Exception):
    """Base exception for SerpApi failures."""


class SerpApiTimeoutError(SerpApiError):
    """SerpApi call timed out (budget exceeded)."""


class SerpApiQuotaError(SerpApiError):
    """SerpApi rate limit or quota exceeded (429)."""


class SerpApiNotConfiguredError(SerpApiError):
    """SerpApi key is not set."""


class SerpApiClient:
    """Async client for SerpApi Google Search engine."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://serpapi.com",
        timeout: float = 10.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = http_client

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def aclose(self) -> None:
        """Close the underlying HTTP client if opened."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def search(self, query: str, num_results: int = 3) -> list[SearchSource]:
        """Execute a Google Search query via SerpApi and return organic search sources.

        Reuses a single shared HTTP client session.
        Extracts title, url, and snippet for each result.

        Raises SerpApiNotConfiguredError if api_key is empty.
        Raises SerpApiTimeoutError if timeout occurs.
        Raises SerpApiQuotaError if rate limited.
        Raises SerpApiError for other HTTP or parsing errors.
        """
        if not self.is_configured:
            raise SerpApiNotConfiguredError("SerpApi API key is not configured.")

        params: dict[str, Any] = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
        }

        client = await self._get_client()

        try:
            response = await client.get(f"{self.base_url}/search", params=params)
        except httpx.TimeoutException as err:
            raise SerpApiTimeoutError(f"SerpApi query timed out after {self.timeout}s") from err
        except httpx.RequestError as err:
            raise SerpApiError(f"SerpApi network request error: {err}") from err

        if response.status_code == 429:
            raise SerpApiQuotaError("SerpApi quota or rate limit exceeded (429).")

        if response.status_code != 200:
            raise SerpApiError(f"SerpApi returned status code {response.status_code}")

        try:
            data = response.json()
        except Exception as err:
            raise SerpApiError(f"Failed to parse SerpApi JSON response: {err}") from err

        sources: list[SearchSource] = []
        organic_results = data.get("organic_results", [])
        for item in organic_results[:num_results]:
            title = (item.get("title") or "").strip()
            link = (item.get("link") or "").strip()
            snippet = (item.get("snippet") or "").strip()
            if title and link:
                sources.append(SearchSource(title=title, url=link, snippet=snippet))

        return sources
