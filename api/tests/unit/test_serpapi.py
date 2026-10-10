"""Unit tests for SerpApiClient (AGENTS.md B2, B3, B10)."""

import asyncio

import httpx
import pytest

from offscript_api.clients.serpapi import (
    SerpApiClient,
    SerpApiError,
    SerpApiNotConfiguredError,
    SerpApiQuotaError,
    SerpApiTimeoutError,
)


def test_serpapi_unconfigured_raises():
    async def _test():
        client = SerpApiClient(api_key="")
        assert not client.is_configured
        with pytest.raises(SerpApiNotConfiguredError):
            await client.search("campus run club")

    asyncio.run(_test())


def test_serpapi_success_parses_results():
    async def _test():
        async def mock_handler(request: httpx.Request) -> httpx.Response:
            assert "engine=google" in str(request.url)
            assert "api_key=valid-key" in str(request.url)
            payload = {
                "organic_results": [
                    {"title": "Campus Run Club Times", "link": "https://example.com/run"},
                    {"title": "Weekend Running Group", "link": "https://example.com/weekend"},
                ]
            }
            return httpx.Response(200, json=payload)

        transport = httpx.MockTransport(mock_handler)
        async with httpx.AsyncClient(transport=transport) as mock_http:
            client = SerpApiClient(api_key="valid-key", http_client=mock_http)
            sources = await client.search("campus run club")

            assert len(sources) == 2
            assert sources[0].title == "Campus Run Club Times"
            assert sources[0].url == "https://example.com/run"
            assert sources[1].title == "Weekend Running Group"
            assert sources[1].url == "https://example.com/weekend"

    asyncio.run(_test())


def test_serpapi_quota_exceeded():
    async def _test():
        async def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, text="Rate limit exceeded")

        transport = httpx.MockTransport(mock_handler)
        async with httpx.AsyncClient(transport=transport) as mock_http:
            client = SerpApiClient(api_key="valid-key", http_client=mock_http)
            with pytest.raises(SerpApiQuotaError):
                await client.search("run club")

    asyncio.run(_test())


def test_serpapi_timeout():
    async def _test():
        async def mock_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Server took too long")

        transport = httpx.MockTransport(mock_handler)
        async with httpx.AsyncClient(transport=transport) as mock_http:
            client = SerpApiClient(api_key="valid-key", http_client=mock_http)
            with pytest.raises(SerpApiTimeoutError):
                await client.search("run club")

    asyncio.run(_test())


def test_serpapi_http_error():
    async def _test():
        async def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="Internal Server Error")

        transport = httpx.MockTransport(mock_handler)
        async with httpx.AsyncClient(transport=transport) as mock_http:
            client = SerpApiClient(api_key="valid-key", http_client=mock_http)
            with pytest.raises(SerpApiError):
                await client.search("run club")

    asyncio.run(_test())
