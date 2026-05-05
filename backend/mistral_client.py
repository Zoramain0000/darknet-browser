#!/usr/bin/env python3
"""
Robin AI - Mistral AI Client Module
Real API integration with Mistral AI for LLM-powered OSINT analysis.
Connects to api.mistral.ai/v1/chat/completions using mistralai SDK v2.4.4.
No mocks, no simulators - real production API calls.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from mistralai import Mistral
from mistralai.models import UserMessage, AssistantMessage, SystemMessage

logger = logging.getLogger(__name__)


class MistralClient:
    """
    Mistral AI client for real LLM-powered analysis.
    Uses Mistral's chat completion API with real models.
    """

    MODELS = {
        "mistral-small-latest": "Mistral Small 4 (119B MoE, 256k ctx, $0.15/M)",
        "mistral-medium-latest": "Mistral Medium (optimized for analysis)",
        "mistral-large-latest": "Mistral Large 3 (675B, best for OSINT, $0.50/M)",
        "codestral-latest": "Codestral (code generation)",
        "ministral-3b-latest": "Ministral 3B (fast, lightweight)",
        "mistral-nemo-latest": "Mistral Nemo (multilingual, 128k ctx)",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistral-large-latest",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "MISTRAL_API_KEY is required. Set it in .env file or pass directly."
            )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize the real Mistral AI client (SDK v2.4.4)
        # This connects to api.mistral.ai/v1/chat/completions
        self.client = Mistral(api_key=self.api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Send a chat completion request to the REAL Mistral AI API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt to prepend
            
        Returns:
            The model's response text from the real API
        """
        formatted_messages = []

        if system_prompt:
            formatted_messages.append(
                SystemMessage(content=system_prompt).model_dump()
            )

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                formatted_messages.append(
                    UserMessage(content=content).model_dump()
                )
            elif role == "assistant":
                formatted_messages.append(
                    AssistantMessage(content=content).model_dump()
                )
            elif role == "system":
                formatted_messages.append(
                    SystemMessage(content=content).model_dump()
                )

        try:
            response = self.client.chat.complete(
                model=kwargs.get("model", self.model),
                messages=formatted_messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                stream=False,
            )

            if response and response.choices:
                return response.choices[0].message.content
            return ""

        except Exception as e:
            logger.error(f"Mistral API call failed: {e}")
            raise

    def analyze_search_results(
        self, query: str, search_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Use Mistral AI to analyze dark web search results.
        Extracts relevant intelligence, identifies threats, and summarizes findings.
        Returns structured JSON with analysis.
        """
        system_prompt = (
            "You are Robin AI, an elite OSINT analysis engine. "
            "Analyze dark web search results and extract actionable intelligence. "
            "Identify threats, data leaks, credential exposures, and relevant information. "
            "Respond in JSON format with keys: summary, threats_found, severity, "
            "key_findings, recommendations, relevant_sources."
        )

        results_text = json.dumps(search_results[:100], indent=2)
        user_message = (
            f"Dark Web Search Query: {query}\n\n"
            f"Search Results (first 100):\n{results_text}\n\n"
            "Analyze these results for intelligence value. "
            "Identify any threats, leaked data, credential exposures, or relevant findings. "
            "Return ONLY valid JSON."
        )

        response = self.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "summary": response,
                "threats_found": [],
                "severity": "unknown",
                "key_findings": [],
                "recommendations": [],
                "relevant_sources": [],
            }

    def refine_search_query(self, raw_query: str) -> str:
        """
        Use Mistral AI to refine a raw search query for better dark web results.
        Returns ONLY the optimized query text.
        """
        system_prompt = (
            "You are a dark web search query optimizer. "
            "Refine the given query to maximize relevant results from "
            "dark web search engines. Return ONLY the optimized query text, nothing else."
        )

        response = self.chat(
            messages=[
                {
                    "role": "user",
                    "content": f"Optimize this dark web search query for maximum relevant results: {raw_query}",
                }
            ],
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=200,
        )

        return response.strip()

    def generate_report(
        self, query: str, all_results: List[Dict], analysis: Dict
    ) -> str:
        """
        Generate a comprehensive investigation report using Mistral AI.
        Returns detailed markdown report.
        """
        system_prompt = (
            "You are Robin AI, generating a professional OSINT investigation report. "
            "Format as a detailed markdown report with: "
            "1. Executive Summary\n"
            "2. Investigation Scope\n"
            "3. Methodology\n"
            "4. Key Findings\n"
            "5. Threat Analysis\n"
            "6. Source References\n"
            "7. Recommendations\n"
            "8. Conclusion"
        )

        results_summary = json.dumps(
            {
                "query": query,
                "total_sources": len(all_results),
                "analysis": analysis,
                "sources": all_results[:20],
            },
            indent=2,
        )

        response = self.chat(
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Generate a comprehensive investigation report "
                        f"based on this data:\n\n{results_summary}"
                    ),
                }
            ],
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=8192,
        )

        return response


# Singleton
_default_client = None


def get_mistral_client(
    api_key: Optional[str] = None, model: str = "mistral-large-latest"
) -> MistralClient:
    """Get or create the default Mistral client instance."""
    global _default_client
    if _default_client is None or api_key:
        _default_client = MistralClient(
            api_key=api_key or os.getenv("MISTRAL_API_KEY"),
            model=model,
        )
    return _default_client