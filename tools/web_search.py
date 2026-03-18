"""
Web search tool using Tavily API.
Supports both search and content fetching from URLs.
"""

from typing import List, Optional
from tavily import TavilyClient
from core.base_tool import BaseTool
from core.logger import get_logger
from core.exceptions import WebSearchException
from config.settings import settings

logger = get_logger(__name__)


class WebSearchTool(BaseTool):
    """
    Web search tool powered by Tavily API.
    Supports keyword search and URL content fetching.
    """

    def __init__(self):
        """Initialize web search tool with Tavily client."""
        super().__init__(
            name        = "web_search",
            description = "Search the web for current information using Tavily"
        )
        self.client      = TavilyClient(api_key=settings.tavily_api_key)
        self.max_results = settings.tavily_max_results
        logger.info("WebSearchTool initialized")

    def execute(
        self,
        input_data  : str,
        max_results : int  = None,
        search_depth: str  = "basic",
        **kwargs
    ) -> dict:
        """
        Execute web search for a query.

        Args:
            input_data  : Search query string
            max_results : Number of results to return
            search_depth: basic or advanced

        Returns:
            Dict with results list and formatted string
        """
        max_results = max_results or self.max_results

        try:
            logger.info(f"Web search: {input_data[:60]}")
            response = self.client.search(
                query        = input_data,
                max_results  = max_results,
                search_depth = search_depth
            )

            results = response.get("results", [])
            if not results:
                return self._success_response(
                    result   = "No results found",
                    metadata = {"raw_results": [], "count": 0}
                )

            formatted = self._format_results(results)
            logger.info(f"Web search returned {len(results)} results")

            return self._success_response(
                result   = formatted,
                metadata = {
                    "raw_results": results,
                    "count"      : len(results),
                    "query"      : input_data
                }
            )

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            raise WebSearchException(f"Search failed: {e}")

    def fetch_url(self, url: str) -> dict:
        """
        Fetch and extract content from a specific URL.

        Args:
            url: URL to fetch content from

        Returns:
            Dict with extracted content
        """
        try:
            logger.info(f"Fetching URL: {url}")
            response = self.client.extract(urls=[url])
            results  = response.get("results", [])

            if not results:
                return self._error_response(f"No content extracted from {url}")

            content = results[0].get("raw_content", "")
            return self._success_response(
                result   = content[:3000],
                metadata = {"url": url, "length": len(content)}
            )

        except Exception as e:
            logger.error(f"URL fetch failed: {e}")
            return self._error_response(f"URL fetch failed: {e}")

    def search_and_fetch(
        self,
        query      : str,
        max_results: int = 3
    ) -> dict:
        """
        Search web and fetch full content from top results.

        Args:
            query      : Search query
            max_results: Number of pages to fetch

        Returns:
            Dict with combined content from all fetched pages
        """
        try:
            search_result = self.execute(query, max_results=max_results)
            if not search_result["success"]:
                return search_result

            raw_results = search_result.get("raw_results", [])
            urls        = [r.get("url") for r in raw_results if r.get("url")]

            combined = []
            for url in urls[:max_results]:
                fetch = self.fetch_url(url)
                if fetch["success"]:
                    combined.append(
                        f"URL: {url}\n{fetch['result'][:500]}"
                    )

            full_content = "\n\n---\n\n".join(combined)
            return self._success_response(
                result   = full_content or search_result["result"],
                metadata = {"urls": urls, "pages_fetched": len(combined)}
            )

        except Exception as e:
            logger.error(f"Search and fetch failed: {e}")
            return self._error_response(str(e))

    def _format_results(self, results: list) -> str:
        """Format raw Tavily results into readable string."""
        formatted = []
        for i, r in enumerate(results):
            formatted.append(
                f"[{i+1}] Title  : {r.get('title', 'N/A')}\n"
                f"     URL    : {r.get('url', 'N/A')}\n"
                f"     Content: {r.get('content', 'N/A')[:300]}"
            )
        return "\n\n".join(formatted)


# ── Singleton instance ────────────────────────────────────
web_search_tool = WebSearchTool()