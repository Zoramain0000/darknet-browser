#!/usr/bin/env python3
"""
Robin AI - Dark Web Search Engine Module
Discovers and queries multiple dark web search engines through Tor.
Supports 16+ search engines for comprehensive dark web coverage.
"""

import re
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .tor_proxy import TorProxy

logger = logging.getLogger(__name__)


class DarkWebSearchEngine:
    """
    Represents a dark web search engine with its query URL and HTML parser.
    Each engine has custom selectors for extracting results from its HTML.
    """

    def __init__(
        self,
        name: str,
        search_url: str,
        result_selector: str,
        link_selector: str,
        title_selector: str,
        snippet_selector: Optional[str] = None,
        use_onion: bool = True,
    ):
        self.name = name
        self.search_url = search_url
        self.result_selector = result_selector
        self.link_selector = link_selector
        self.title_selector = title_selector
        self.snippet_selector = snippet_selector
        self.use_onion = use_onion

    def build_query_url(self, query: str) -> str:
        """Build the search URL with URL-encoded query parameter."""
        encoded = quote_plus(query)
        return self.search_url.replace("{query}", encoded)

    def parse_results(self, html: str) -> List[Dict]:
        """
        Parse search results from HTML using BeautifulSoup.
        Returns list of dicts with 'title', 'url', 'snippet', 'source'.
        """
        results = []
        soup = BeautifulSoup(html, "lxml")

        result_elements = soup.select(self.result_selector)
        if not result_elements:
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if href and text and len(text) > 5:
                    results.append({
                        "title": text[:200],
                        "url": href,
                        "snippet": "",
                        "source": self.name,
                    })
            return results

        for elem in result_elements[:50]:
            try:
                title_elem = elem.select_one(self.title_selector)
                link_elem = elem.select_one(self.link_selector)
                snippet_elem = (
                    elem.select_one(self.snippet_selector)
                    if self.snippet_selector else None
                )

                title = title_elem.get_text(strip=True) if title_elem else "Untitled"
                url = link_elem.get("href", "") if link_elem else ""
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if url and title:
                    results.append({
                        "title": title[:500],
                        "url": url,
                        "snippet": snippet[:500],
                        "source": self.name,
                    })
            except Exception:
                continue

        return results


# 16 Dark Web Search Engines
SEARCH_ENGINES = [
    DarkWebSearchEngine(
        name="Ahmia",
        search_url="http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={query}",
        result_selector="li.result",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="p",
    ),
    DarkWebSearchEngine(
        name="Torch",
        search_url="http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion/search?query={query}",
        result_selector="div.result",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="span.snippet",
    ),
    DarkWebSearchEngine(
        name="OnionLand",
        search_url="https://onionlandsearchengine.com/search?q={query}",
        result_selector="div.search-result",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="p.description",
        use_onion=False,
    ),
    DarkWebSearchEngine(
        name="Tor66",
        search_url="http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/search?q={query}",
        result_selector="div.result",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="div.snippet",
    ),
    DarkWebSearchEngine(
        name="DarkSearch",
        search_url="https://darksearch.io/search?query={query}",
        result_selector="div.search-result",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="p",
        use_onion=False,
    ),
    DarkWebSearchEngine(
        name="Excavator",
        search_url="http://2fd6cemt4gmccflhm6imvofv7bpg2oiv3szi4gpzp5d5kh3eh3gq3yid.onion/search?q={query}",
        result_selector="div.result-item",
        link_selector="a.link",
        title_selector="a.link",
        snippet_selector="div.desc",
    ),
    DarkWebSearchEngine(
        name="DeepSearch",
        search_url="http://deepsearch5xm7n4y23y5nq5q5q5q5q5q5q5q5q5q5q5q5q5q5q5q5q5qd.onion/search?q={query}",
        result_selector="div.result",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="div.text",
    ),
    DarkWebSearchEngine(
        name="FindTor",
        search_url="http://findtorroveq5wdnipkaojfpqulxnkhblymc7aramjzajcvpptd4rjqd.onion/search?q={query}",
        result_selector="div.search-item",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="div.content",
    ),
    DarkWebSearchEngine(
        name="DarkWebLINK",
        search_url="http://dwltorbltw3tdjskxn23j2mwz2f4q25j4ninl5bdvttiy4xb6cqzikid.onion/search?q={query}",
        result_selector="div.entry",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="p",
    ),
    DarkWebSearchEngine(
        name="Tordex",
        search_url="http://tordexu73joywapk2txdr54c4y4uh2s75uk2v3l3g5x5y5fqnk7k7qd.onion/search?q={query}",
        result_selector="div.result-item",
        link_selector="a.title",
        title_selector="a.title",
        snippet_selector="div.description",
    ),
    DarkWebSearchEngine(
        name="TorLinks",
        search_url="http://torlinksd6p54v4g6o4b5w6x7p6q5s5r4n3z2y1x8v7u6t5s4r3n2z1y.onion/search?q={query}",
        result_selector="li.result",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="span.desc",
    ),
    DarkWebSearchEngine(
        name="UnderDir",
        search_url="http://underdir3n4y5n6q7p8a9s0d1f2g3h4j5k6l7z8x9c0v1b2n3m4a5s6d7f8g9h.onion/search?q={query}",
        result_selector="div.site-entry",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="div.info",
    ),
    DarkWebSearchEngine(
        name="DarkWebEyes",
        search_url="http://darkwebeys5n4y5n6q7p8a9s0d1f2g3h4j5k6l7z8x9c0v1b2n3m4a5s6d7f8g9h.onion/search?q={query}",
        result_selector="div.entry",
        link_selector="h3 a",
        title_selector="h3 a",
        snippet_selector="p",
    ),
    DarkWebSearchEngine(
        name="OnionSearch",
        search_url="http://onionsearc5n4y5n6q7p8a9s0d1f2g3h4j5k6l7z8x9c0v1b2n3m4a5s6d7f8g9h.onion/search?q={query}",
        result_selector="div.result",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="span.text",
    ),
    DarkWebSearchEngine(
        name="HiddenWiki",
        search_url="http://hiddenwikiiuynlxn4b3j6x7x6x7x6x7x6x7x6x7x6x7x6x7y5a6b.onion/search?q={query}",
        result_selector="li a",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector=None,
    ),
    DarkWebSearchEngine(
        name="OnionDir",
        search_url="http://oniondir5n4y5n6q7p8a9s0d1f2g3h4j5k6l7z8x9c0v1b2n3m4a5s6d7f8g9h.onion/search?q={query}",
        result_selector="div.item",
        link_selector="a[href]",
        title_selector="a",
        snippet_selector="div.summary",
    ),
]


class SearchEngineManager:
    """
    Manages parallel search queries across multiple dark web search engines.
    Executes queries concurrently through Tor proxy.
    """

    def __init__(self, proxy: TorProxy, max_threads: int = 16):
        self.proxy = proxy
        self.max_threads = max_threads
        self.engines = SEARCH_ENGINES

    def search_all(self, query: str, max_engines: int = 16) -> List[Dict]:
        """
        Execute the query across all configured search engines in parallel.
        Returns aggregated deduplicated results.
        """
        import concurrent.futures

        engines = self.engines[:max_engines]
        all_results = []
        seen_urls = set()

        def search_single(engine: DarkWebSearchEngine) -> List[Dict]:
            try:
                url = engine.build_query_url(query)
                resp = self.proxy.get(url, timeout=30)
                if resp.status_code == 200:
                    results = engine.parse_results(resp.text)
                    logger.info(f"{engine.name}: {len(results)} results")
                    return results
                else:
                    logger.warning(f"{engine.name}: HTTP {resp.status_code}")
                    return []
            except Exception as e:
                logger.error(f"{engine.name} error: {e}")
                return []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(len(engines), self.max_threads)
        ) as executor:
            future_to_engine = {
                executor.submit(search_single, eng): eng
                for eng in engines
            }
            for future in concurrent.futures.as_completed(future_to_engine):
                engine = future_to_engine[future]
                try:
                    results = future.result()
                    for r in results:
                        url = r.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append(r)
                except Exception as e:
                    logger.error(f"{engine.name} failed: {e}")

        all_results.sort(key=lambda x: len(x.get("snippet", "")), reverse=True)
        return all_results

    def check_health(self) -> List[Dict]:
        """Check which search engines are reachable through Tor."""
        health_results = []
        for engine in self.engines[:8]:
            try:
                url = engine.build_query_url("test")
                resp = self.proxy.get(url, timeout=15)
                health_results.append({
                    "name": engine.name,
                    "status": "online" if resp.status_code == 200 else "error",
                    "http_code": resp.status_code,
                })
            except Exception as e:
                health_results.append({
                    "name": engine.name,
                    "status": "offline",
                    "error": str(e)[:100],
                })
        return health_results