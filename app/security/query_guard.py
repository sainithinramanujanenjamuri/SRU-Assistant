"""Query Safety and Prompt Injection Defense for SRU Assistant (Phase 11).

Protects against prompt injection attempts, malicious payloads, malformed inputs,
and denial-of-service query floods.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


class QuerySecurityError(ValueError):
    """Raised when an incoming query fails safety or integrity policies."""
    pass


@dataclass
class QueryGuardResult:
    """Outcome of query security inspection."""

    is_safe: bool
    sanitized_query: str
    original_query: str
    threat_type: Optional[str] = None
    refusal_message: Optional[str] = None
    details: Optional[str] = None
    is_conversational: bool = False
    conversational_response: Optional[str] = None


class QueryGuard:
    """Security guard verifying query length, sanitizing input, and detecting prompt injections."""

    # Patterns indicating prompt injection, jailbreaking, or system prompt exfiltration
    PROMPT_INJECTION_PATTERNS = [
        r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|commands)\b",
        r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|commands)\b",
        r"(?i)\b(system\s+prompt|developer\s+mode|jailbreak|dan\s+mode)\b",
        r"(?i)\byou\s+are\s+now\s+(an\s+unrestricted|a\s+different|in\s+god\s+mode|dan)\b",
        r"(?i)\b(reveal|output|display|show|leak|print)\s+(your\s+)?(system\s+prompt|instructions|initial\s+prompt)\b",
        r"(?i)\b(pretend|act\s+as\s+if)\s+you\s+have\s+no\s+(rules|restrictions|guidelines)\b",
        r"(?i)\bbypass\s+(all\s+)?(filters|safety|guardrails)\b",
    ]

    # Conversational Greeting Patterns
    GREETING_PATTERNS = [
        r"(?i)^\s*(hello|hi|hey|good\s+morning|good\s+afternoon|good\s+evening|greetings|howdy)\b[!?.]*\s*$",
        r"(?i)^\s*how\s+are\s+you\b[!?.]*\s*$",
    ]

    # University Identity & Bot Metadata Patterns
    IDENTITY_PATTERNS = [
        r"(?i)\b(your\s+college\s+name|what\s+is\s+your\s+college|which\s+college|which\s+university|your\s+university|what\s+college|who\s+are\s+you|what\s+is\s+your\s+name|tell\s+me\s+about\s+yourself)\b",
    ]

    # Regex for dangerous HTML/Script tags
    HTML_SCRIPT_PATTERN = r"(?i)<\s*script[^>]*>.*?<\s*/\s*script\s*>"

    SAFE_REFUSAL_MESSAGE = (
        "I am SRU Assistant, an academic query resolution framework for SR University. "
        "I am designed to answer academic questions strictly based on verified university documents "
        "(such as regulations, calendars, and syllabi) and cannot process system override, jailbreak, "
        "or unrestricted prompt commands."
    )

    GREETING_RESPONSE = (
        "Hello! I am SRU Assistant, your AI academic advisor for SR University. "
        "I can answer your queries about B.Tech R23 academic regulations, attendance rules, "
        "course syllabi, examination dates, credits, and capstone project details."
    )

    IDENTITY_RESPONSE = (
        "I am SRU Assistant, built for **SR University (Warangal, Telangana)** by "
        "Capstone Project Team 235 in the School of Computer Science & Artificial Intelligence (CS&AI). "
        "How can I assist you with your academic inquiries today?"
    )

    def __init__(self, min_length: int = 2, max_length: int = 1000) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self._compiled_injections = [re.compile(p) for p in self.PROMPT_INJECTION_PATTERNS]
        self._compiled_greetings = [re.compile(p) for p in self.GREETING_PATTERNS]
        self._compiled_identities = [re.compile(p) for p in self.IDENTITY_PATTERNS]
        self._script_regex = re.compile(self.HTML_SCRIPT_PATTERN, re.DOTALL)


    def inspect_query(self, query: str) -> QueryGuardResult:
        """Inspect and sanitize an incoming academic user query.
        
        Args:
            query: Raw user query string.
            
        Returns:
            QueryGuardResult with safety determination and sanitized query text.
            
        Raises:
            QuerySecurityError: If query is empty, whitespace-only, or exceeds max length.
        """
        if not query or not query.strip():
            raise QuerySecurityError("Query cannot be empty or contain only whitespace.")

        raw_query = query.strip()

        if len(raw_query) < self.min_length:
            raise QuerySecurityError(
                f"Query is too short ({len(raw_query)} chars). Minimum length is {self.min_length} characters."
            )

        if len(raw_query) > self.max_length:
            raise QuerySecurityError(
                f"Query exceeds maximum permitted length of {self.max_length} characters (received {len(raw_query)} chars)."
            )

        # 1. Sanitize control characters and script tags
        sanitized = self._sanitize(raw_query)

        # 2. Check for Prompt Injection / Jailbreak attempts
        for pattern in self._compiled_injections:
            match = pattern.search(sanitized)
            if match:
                return QueryGuardResult(
                    is_safe=False,
                    sanitized_query=sanitized,
                    original_query=raw_query,
                    threat_type="prompt_injection",
                    refusal_message=self.SAFE_REFUSAL_MESSAGE,
                    details=f"Query matched injection signature: '{match.group(0)}'",
                )

        # 3. Check for Conversational Greeting intent
        for pattern in self._compiled_greetings:
            if pattern.search(sanitized):
                return QueryGuardResult(
                    is_safe=True,
                    sanitized_query=sanitized,
                    original_query=raw_query,
                    is_conversational=True,
                    conversational_response=self.GREETING_RESPONSE,
                )

        # 4. Check for University Identity & Bot Metadata intent
        for pattern in self._compiled_identities:
            if pattern.search(sanitized):
                return QueryGuardResult(
                    is_safe=True,
                    sanitized_query=sanitized,
                    original_query=raw_query,
                    is_conversational=True,
                    conversational_response=self.IDENTITY_RESPONSE,
                )

        return QueryGuardResult(
            is_safe=True,
            sanitized_query=sanitized,
            original_query=raw_query,
        )


    def _sanitize(self, text: str) -> str:
        """Strip control characters, dangerous script tags, and excessive repetitive whitespace."""
        # Remove script tags
        text = self._script_regex.sub("", text)
        # Remove non-printable control characters (keep \n and \t)
        text = "".join(ch for ch in text if ch >= " " or ch in "\n\t")
        # Normalize excessive whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
