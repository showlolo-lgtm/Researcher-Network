import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.semanticscholar.org/graph/v1"

AUTHOR_FIELDS = "name,affiliations,homepage,hIndex,citationCount,paperCount"
PAPER_FIELDS = "title,year,venue,citationCount,abstract,fieldsOfStudy,authors"


class SemanticScholarClient:
    def __init__(self):
        headers = {}
        if settings.s2_api_key:
            headers["x-api-key"] = settings.s2_api_key
        self._client = httpx.AsyncClient(
            base_url=BASE_URL, headers=headers, timeout=30.0
        )
        # Rate limiting: 1 request per second for free tier
        self._semaphore = asyncio.Semaphore(1)
        self._last_request = 0.0

    async def _request(self, method: str, url: str, **kwargs) -> dict | None:
        async with self._semaphore:
            now = asyncio.get_event_loop().time()
            wait = max(0, 1.0 - (now - self._last_request))
            if wait > 0:
                await asyncio.sleep(wait)

            for attempt in range(3):
                try:
                    resp = await self._client.request(method, url, **kwargs)
                    self._last_request = asyncio.get_event_loop().time()

                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", 5))
                        logger.warning(f"Rate limited, retrying in {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    if resp.status_code == 404:
                        return None

                    resp.raise_for_status()
                    return resp.json()
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error {e.response.status_code}: {e}")
                    if attempt == 2:
                        raise
                    await asyncio.sleep(2 ** attempt)
                except httpx.RequestError as e:
                    logger.error(f"Request error: {e}")
                    if attempt == 2:
                        raise
                    await asyncio.sleep(2 ** attempt)
        return None

    async def get_author(self, author_id: str) -> dict | None:
        return await self._request("GET", f"/author/{author_id}", params={"fields": AUTHOR_FIELDS})

    async def get_author_papers(
        self, author_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        resp = await self._request(
            "GET",
            f"/author/{author_id}/papers",
            params={"fields": PAPER_FIELDS, "limit": limit, "offset": offset},
        )
        return resp.get("data", []) if resp else []

    async def search_author(self, query: str, limit: int = 5) -> list[dict]:
        resp = await self._request(
            "GET",
            "/author/search",
            params={"query": query, "limit": limit, "fields": AUTHOR_FIELDS},
        )
        return resp.get("data", []) if resp else []

    async def get_paper(self, paper_id: str) -> dict | None:
        return await self._request("GET", f"/paper/{paper_id}", params={"fields": PAPER_FIELDS})

    async def close(self):
        await self._client.aclose()


s2_client = SemanticScholarClient()
