"""
LLM Client — supports Anthropic Claude, OpenAI, and Ollama.
Gracefully handles missing API keys — agents fall back to rule-based logic.
"""

import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def is_llm_available() -> bool:
    """Returns True if a valid LLM API key or local model is configured."""
    provider = LLM_PROVIDER.lower()
    if provider == "anthropic":
        return bool(ANTHROPIC_API_KEY and not ANTHROPIC_API_KEY.startswith("your_"))
    elif provider == "openai":
        return bool(OPENAI_API_KEY and not OPENAI_API_KEY.startswith("your_"))
    elif provider == "ollama":
        return True  # assume Ollama is running locally
    return False


async def call_llm(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 1500,
    temperature: float = 0.3,
    json_mode: bool = False,
) -> str:
    """
    Unified LLM call. Raises RuntimeError if no provider is configured.
    """
    if not is_llm_available():
        raise RuntimeError("No LLM API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env")

    provider = LLM_PROVIDER.lower()
    if provider == "anthropic":
        return await _call_anthropic(system_prompt, user_message, max_tokens, temperature)
    elif provider == "openai":
        return await _call_openai(system_prompt, user_message, max_tokens, temperature)
    elif provider == "ollama":
        return await _call_ollama(system_prompt, user_message, max_tokens, temperature)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


async def _call_anthropic(system_prompt: str, user_message: str, max_tokens: int, temperature: float) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


async def _call_openai(system_prompt: str, user_message: str, max_tokens: int, temperature: float) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_ollama(system_prompt: str, user_message: str, max_tokens: int, temperature: float) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]


def safe_parse_json(text: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise