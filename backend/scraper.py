#!/usr/bin/env python3
"""
Robin AI - Dark Web Scraper Module
Scrapes and extracts intelligence from .onion sites discovered during searches.
Extracts text, metadata, emails, crypto addresses, and potential data leaks.
"""

import re
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from .tor_proxy import TorProxy

logger = logging.getLogger(__name__)


class OnionScraper:
    """
    Scrapes content from .onion websites through Tor proxy.
    Extracts text, emails, BTC/ETH addresses, and metadata.
    """

    def __init__(self, proxy: TorProxy, max_pages: int = 50, timeout: int = 30):
        self.proxy = proxy
        self.max_pages = max_pages
        self.timeout = timeout

    def extract_content(self, url: str) -> Optional[Dict]:
        """
        Fetch and extract content from a single URL through Tor.
        Returns structured data or None if fetch fails.
        """
        try:
            resp = self.proxy.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            title = soup.title.get_text(strip=True) if soup.title else ""
            body = soup.find("body")
            text = body.get_text(separator="\n", strip=True) if body else ""

            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("http") or href.startswith("/"):
                    links.append({
                        "url": href,
                        "text": a.get_text(strip=True)[:200],
                    })

            emails = list(set(re.findall(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text
            )))
            btc = list(set(re.findall(
                r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b", text
            )))
            eth = list(set(re.findall(
                r"\b0x[a-fA-F0-9]{40}\b", text
            )))

            return {
                "url": url,
                "title": title[:500],
                "content": text[:10000],
                "content_length": len(text),
                "links": links[:100],
                "emails": emails[:50],
                "btc_addresses": btc[:20],
                "eth_addresses": eth[:20],
                "status_code": resp.status_code,
            }

        except Exception as e:
            logger.error(f"Scrape failed for {url}: {e}")
            return None

    def scrape_batch(self, urls: List[str], max_pages: int = 50) -> List[Dict]:
        """
        Scrape multiple URLs in parallel through Tor proxy.
        Returns list of extracted content dicts.
        """
        import concurrent.futures

        urls = [u for u in urls if u.startswith("http")][:max_pages]
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(urls), 10)) as executor:
            future_to_url = {executor.submit(self.extract_content, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    continue

        results.sort(key=lambda x: x.get("content_length", 0), reverse=True)
        return results

    def search_for_leaks(
        self, content_list: List[Dict], keywords: List[str]
    ) -> List[Dict]:
        """
        Search scraped content for specific keywords/patterns.
        Returns matches with surrounding context.
        """
        findings = []
        for content in content_list:
            text = content.get("content", "").lower()
            url = content.get("url", "")
            for kw in keywords:
                kw_lower = kw.lower()
                positions = [m.start() for m in re.finditer(re.escape(kw_lower), text)]
                for pos in positions[:5]:
                    start = max(0, pos - 100)
                    end = min(len(text), pos + len(kw) + 100)
                    context = text[start:end]
                    findings.append({
                        "keyword": kw,
                        "url": url,
                        "context": context,
                        "position": pos,
                    })

        return findings