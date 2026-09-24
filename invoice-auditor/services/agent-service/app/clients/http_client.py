"""
Agent Service - Global HTTP Client

Provides a singleton httpx.AsyncClient for outgoing HTTP requests.
This ensures connection pooling is utilized efficiently.
"""

import httpx

# The global client instance, initialized during startup
http_client: httpx.AsyncClient | None = None


async def start_http_client() -> None:
    """Initialize the global HTTP client."""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=10.0)


async def stop_http_client() -> None:
    """Close the global HTTP client."""
    global http_client
    if http_client is not None:
        await http_client.aclose()
        http_client = None


def get_http_client() -> httpx.AsyncClient:
    """Get the active HTTP client."""
    if http_client is None:
        raise RuntimeError("HTTP client is not initialized. Call start_http_client() first.")
    return http_client
