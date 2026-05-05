#!/usr/bin/env python3
"""
Robin AI - Orchestration Engine
The core pipeline orchestrator that coordinates:
Query Refinement → Tor Check → Parallel Search → Scraping → LLM Analysis → Report
"""

import os
import time
import logging
from typing import List, Dict, Optional, Callable

from .tor_proxy import TorProxy, get_proxy
from .mistral_client import MistralClient, get_mistral_client
from .search_engine import SearchEngineManager
from .scraper import OnionScraper
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class RobinEngine:
    """
    Core orchestrator for the Robin OSINT investigation pipeline.
    Coordinates all modules in the correct sequence with progress tracking.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistral-large-latest",
        tor_host: str = "127.0.0.1",
        tor_port: int = 9050,
        max_threads: int = 16,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "")
        self.model = model
        self.max_threads = max_threads
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize components
        self.proxy = TorProxy(
            host=tor_host,
            port=tor_port,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.mistral = get_mistral_client(api_key=self.api_key, model=model)
        self.search_manager = SearchEngineManager(
            proxy=self.proxy,
            max_threads=max_threads,
        )
        self.scraper = OnionScraper(
            proxy=self.proxy,
            timeout=timeout,
        )
        self.report_generator = ReportGenerator()

        self._progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates."""
        self._progress_callback = callback

    def _update_progress(self, stage: str, progress: float, status: str):
        """Emit progress update if callback is set."""
        if self._progress_callback:
            self._progress_callback({
                "stage": stage,
                "progress": progress,
                "status": status,
            })

    def run_investigation(self, query: str) -> Dict:
        """
        Execute the full investigation pipeline.
        
        Pipeline stages:
        1. LLM Query Refinement (Mistral AI)
        2. Tor Connection Check
        3. Parallel Search (16 engines)
        4. Onion Content Scraping
        5. LLM Analysis (Mistral AI)
        6. Report Generation
        
        Returns dict with all results, analysis, and report path.
        """
        start_time = time.time()
        timings = {}

        self._update_progress("initializing", 0.0, "Starting investigation...")

        # Stage 1: Query Refinement
        self._update_progress("refining_query", 0.05, "Refining search query with Mistral AI...")
        t0 = time.time()
        try:
            refined_query = self.mistral.refine_search_query(query)
        except Exception as e:
            logger.warning(f"Query refinement failed: {e}")
            refined_query = query
        timings["query_refinement"] = time.time() - t0

        # Stage 2: Tor Check
        self._update_progress("checking_tor", 0.10, "Verifying Tor proxy connection...")
        t0 = time.time()
        tor_ok, tor_ip = self.proxy.check_connection()
        timings["tor_check"] = time.time() - t0
        if not tor_ok:
            logger.warning(f"Tor proxy check failed: {tor_ip}")
            tor_ip = "Unavailable"

        # Stage 3: Parallel Search
        self._update_progress("searching", 0.15, f"Searching {self.max_threads} dark web engines...")
        t0 = time.time()
        search_results = self.search_manager.search_all(
            refined_query,
            max_engines=self.max_threads,
        )
        timings["search"] = time.time() - t0
        total_results = len(search_results)

        if not search_results:
            self._update_progress("complete", 1.0, "No results found.")
            return {
                "query": query,
                "refined_query": refined_query,
                "total_results": 0,
                "search_results": [],
                "scraped_content": [],
                "analysis": {
                    "summary": "No search results found. Try broadening the query.",
                    "threats_found": [],
                    "severity": "none",
                    "key_findings": [],
                    "recommendations": ["Broaden search query", "Check Tor proxy status"],
                    "relevant_sources": [],
                },
                "report_path": None,
                "timings": timings,
                "total_time": time.time() - start_time,
                "tor_ip": tor_ip,
            }

        # Stage 4: Scrape discovered .onion pages
        self._update_progress("scraping", 0.35, f"Scraping {min(total_results, 50)} onion sites...")
        t0 = time.time()
        onion_urls = [r["url"] for r in search_results if ".onion" in r.get("url", "")]
        scraped_content = self.scraper.scrape_batch(onion_urls, max_pages=50)
        timings["scraping"] = time.time() - t0

        # Stage 5: LLM Analysis
        self._update_progress("analyzing", 0.65, "Analyzing results with Mistral AI...")
        t0 = time.time()
        try:
            analysis = self.mistral.analyze_search_results(query, search_results)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            analysis = {
                "summary": f"Analysis failed: {e}",
                "threats_found": [],
                "severity": "unknown",
                "key_findings": ["Analysis error occurred"],
                "recommendations": ["Retry analysis", "Check API key"],
                "relevant_sources": [],
            }
        timings["analysis"] = time.time() - t0

        # Stage 6: Report Generation
        self._update_progress("reporting", 0.85, "Generating investigation report...")
        t0 = time.time()
        try:
            report_markdown = self.report_generator.generate_markdown(
                query=query,
                refined_query=refined_query,
                results=search_results,
                analysis=analysis,
                scraped_content=scraped_content,
                timing=timings,
                tor_ip=tor_ip,
            )
            report_path = self.report_generator.save_report(query, report_markdown)
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            report_markdown = f"# Investigation Report\n\nQuery: {query}\n\nReport generation failed: {e}"
            report_path = None
        timings["report"] = time.time() - t0

        total_time = time.time() - start_time
        self._update_progress("complete", 1.0, f"Investigation complete in {total_time:.1f}s")

        return {
            "query": query,
            "refined_query": refined_query,
            "total_results": total_results,
            "search_results": search_results[:200],
            "scraped_content": scraped_content[:20],
            "analysis": analysis,
            "report_markdown": report_markdown,
            "report_path": report_path,
            "timings": timings,
            "total_time": total_time,
            "tor_ip": tor_ip,
            "tor_ok": tor_ok,
        }