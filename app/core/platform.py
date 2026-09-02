from __future__ import annotations

from typing import Any


def resolve_originating_platform(
    explicit_platform: str | None = None,
    headers: dict[str, str] | Any = None,
) -> str:
    """Dynamically resolves the calling AI host / client platform without hardcoding.

    Priority:
    1. Explicit parameter passed by tool/API caller (e.g. 'claude', 'chatgpt', 'gemini', 'whatsapp', 'cli').
    2. Explicit HTTP header: 'x-client-platform' or 'x-host'.
    3. HTTP User-Agent heuristics:
       - 'anthropic' / 'claude' -> 'claude'
       - 'openai' / 'chatgpt' -> 'chatgpt'
       - 'google' / 'gemini' -> 'gemini'
       - 'python-requests' / 'curl' / 'postman' -> 'api'
       - 'mozilla' / 'chrome' / 'safari' / 'edge' -> 'web'
    4. Fallback -> 'api'
    """
    if explicit_platform and explicit_platform.strip():
        return explicit_platform.strip().lower()

    if headers:
        if hasattr(headers, "get"):
            custom_hdr = headers.get("x-client-platform") or headers.get("x-host")
            if custom_hdr and custom_hdr.strip():
                return custom_hdr.strip().lower()

            user_agent = (headers.get("user-agent") or "").lower()
            if "claude" in user_agent or "anthropic" in user_agent:
                return "claude"
            if "chatgpt" in user_agent or "openai" in user_agent:
                return "chatgpt"
            if "gemini" in user_agent or "google" in user_agent:
                return "gemini"
            if any(tool in user_agent for tool in ("curl", "python-requests", "httpx", "postman")):
                return "api"
            if any(b in user_agent for b in ("mozilla", "chrome", "safari", "edge")):
                return "web"

    return "api"
