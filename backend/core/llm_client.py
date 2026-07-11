"""
Unified LLM Client
Supports: OpenAI, Anthropic, Groq, Google Gemini, Cohere, Ollama (local)

Usage:
    client = LLMClient(provider="openai", api_key="sk-...", model="gpt-4o")
    response = await client.complete("Your prompt here")
"""

import httpx
import json
import asyncio
from typing import Optional, List, Dict, AsyncGenerator
from enum import Enum
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GEMINI = "gemini"
    COHERE = "cohere"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


# Default models per provider
PROVIDER_DEFAULTS = {
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.ANTHROPIC: "claude-3-haiku-20240307",
    LLMProvider.GROQ: "llama-3.3-70b-versatile",
    LLMProvider.GEMINI: "gemini-1.5-flash",
    LLMProvider.COHERE: "command-r",
    LLMProvider.OLLAMA: "llama3.2",
    LLMProvider.OPENROUTER: "meta-llama/llama-3.1-8b-instruct:free",
}

# Available models per provider (for UI display)
PROVIDER_MODELS = {
    LLMProvider.OPENAI: [
        {"id": "gpt-4o", "name": "GPT-4o (Best)", "context": "128k"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Fast, Cheap)", "context": "128k"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": "128k"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo (Fastest)", "context": "16k"},
    ],
    LLMProvider.ANTHROPIC: [
        {"id": "claude-opus-4-5", "name": "Claude Opus 4.5 (Best)", "context": "200k"},
        {"id": "claude-sonnet-4-5", "name": "Claude Sonnet 4.5 (Balanced)", "context": "200k"},
        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku (Fast)", "context": "200k"},
    ],
    LLMProvider.GROQ: [
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B (Best)", "context": "128k"},
        {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "name": "Llama 4 Scout 17B", "context": "128k"},
        {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B (Fastest)", "context": "128k"},
        {"id": "qwen/qwen3-32b", "name": "Qwen3 32B", "context": "128k"},
    ],
    LLMProvider.GEMINI: [
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro (Best)", "context": "1M"},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash (Fast)", "context": "1M"},
        {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro", "context": "32k"},
    ],
    LLMProvider.COHERE: [
        {"id": "command-r-plus", "name": "Command R+ (Best)", "context": "128k"},
        {"id": "command-r", "name": "Command R (Balanced)", "context": "128k"},
        {"id": "command", "name": "Command (Fast)", "context": "4k"},
    ],
    LLMProvider.OLLAMA: [],  # Populated dynamically
    LLMProvider.OPENROUTER: [
        {"id": "meta-llama/llama-3.1-8b-instruct:free", "name": "Llama 3.1 8B (Free)", "context": "128k"},
        {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B (Free)", "context": "32k"},
        {"id": "google/gemma-2-9b-it:free", "name": "Gemma 2 9B (Free)", "context": "8k"},
        {"id": "microsoft/phi-3-mini-128k-instruct:free", "name": "Phi-3 Mini (Free)", "context": "128k"},
    ],
}


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(
        self,
        provider: str = "ollama",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        user_id: Optional[str] = None,
    ):
        self.provider = LLMProvider(provider)
        self.api_key = api_key
        self.model = model or PROVIDER_DEFAULTS.get(self.provider, "llama3.2")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.user_id = user_id  # for usage logging

        # Base URLs
        self.base_urls = {
            LLMProvider.OPENAI: "https://api.openai.com/v1",
            LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
            LLMProvider.GROQ: "https://api.groq.com/openai/v1",
            LLMProvider.GEMINI: "https://generativelanguage.googleapis.com/v1beta",
            LLMProvider.COHERE: "https://api.cohere.ai/v1",
            LLMProvider.OLLAMA: base_url or "http://localhost:11434",
            LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
        }

        if base_url and self.provider == LLMProvider.OLLAMA:
            self.base_urls[LLMProvider.OLLAMA] = base_url.rstrip("/")

    # ── Cost tracking ─────────────────────────────────────────────────────────────
    # USD per 1M tokens (prompt, completion) — approximate, update as needed
    MODEL_COSTS = {
        "openai": {
            "gpt-4o": (2.50, 10.00),
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4-turbo": (10.00, 30.00),
            "gpt-3.5-turbo": (0.50, 1.50),
        },
        "anthropic": {
            "claude-opus-4-5": (15.00, 75.00),
            "claude-sonnet-4-5": (3.00, 15.00),
            "claude-3-haiku-20240307": (0.25, 1.25),
        },
        "groq": {
            "llama-3.3-70b-versatile": (0.59, 0.79),
            "meta-llama/llama-4-scout-17b-16e-instruct": (0.11, 0.34),
            "llama-3.1-8b-instant": (0.05, 0.08),
            "qwen/qwen3-32b": (0.30, 0.30),
        },
        "gemini": {
            "gemini-1.5-pro": (1.25, 5.00),
            "gemini-1.5-flash": (0.075, 0.30),
            "gemini-1.0-pro": (0.50, 1.50),
        },
        "cohere": {
            "command-r-plus": (3.00, 15.00),
            "command-r": (0.50, 1.50),
        },
        "openrouter": {
            "meta-llama/llama-3.1-8b-instruct:free": (0.0, 0.0),
            "mistralai/mistral-7b-instruct:free": (0.0, 0.0),
            "google/gemma-2-9b-it:free": (0.0, 0.0),
            "microsoft/phi-3-mini-128k-instruct:free": (0.0, 0.0),
        },
    }

    # ── Energy tracking ────────────────────────────────────────────────────────
    # Watt-hours per 1M tokens (prompt, completion) — estimates based on model size
    # Sources: ML CO2 Impact research, datacenter PUE ~1.2, GPU TDP extrapolations
    # Local Ollama: actual GPU wattage / throughput — estimated ~0.5 Wh/1M tokens
    MODEL_ENERGY_WH = {
        "openai": {
            "gpt-4o":       (3.0,  6.0),   # Large MoE model, shared inference
            "gpt-4o-mini":  (0.5,  1.0),
            "gpt-4-turbo":  (4.0,  8.0),
            "gpt-3.5-turbo":(0.3,  0.6),
        },
        "anthropic": {
            "claude-opus-4-5":       (5.0, 10.0),
            "claude-sonnet-4-5":     (2.0,  4.0),
            "claude-3-haiku-20240307":(0.4,  0.8),
        },
        "groq": {
            # Groq LPU is ~10x more efficient than GPU
            "llama-3.3-70b-versatile":                    (0.4, 0.8),
            "meta-llama/llama-4-scout-17b-16e-instruct":  (0.15, 0.3),
            "llama-3.1-8b-instant":                       (0.05, 0.1),
            "qwen/qwen3-32b":                             (0.2, 0.4),
        },
        "gemini": {
            "gemini-1.5-pro":   (3.5, 7.0),
            "gemini-1.5-flash":  (0.5, 1.0),
            "gemini-1.0-pro":    (1.0, 2.0),
        },
        "cohere": {
            "command-r-plus": (3.0, 6.0),
            "command-r":      (1.0, 2.0),
        },
        "openrouter": {
            "meta-llama/llama-3.1-8b-instruct:free": (0.3, 0.6),
            "mistralai/mistral-7b-instruct:free":     (0.3, 0.6),
            "google/gemma-2-9b-it:free":              (0.3, 0.6),
            "microsoft/phi-3-mini-128k-instruct:free":(0.1, 0.2),
        },
        "ollama": {},  # dynamically ~0.5 Wh/1M tokens for local GPU
    }
    OLLAMA_ENERGY_WH_PER_1M = (0.5, 0.5)  # conservative local GPU estimate

    def _get_cost_per_million(self) -> tuple[float, float]:
        """Return (prompt_cost_per_1m, completion_cost_per_1m) for current model."""
        provider_costs = self.MODEL_COSTS.get(self.provider.value, {})
        return provider_costs.get(self.model, (0.0, 0.0))

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        prompt_cost_per_1m, completion_cost_per_1m = self._get_cost_per_million()
        return (prompt_tokens / 1_000_000) * prompt_cost_per_1m + (completion_tokens / 1_000_000) * completion_cost_per_1m

    def _calculate_energy(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Return estimated energy in Wh for this call."""
        provider_energy = self.MODEL_ENERGY_WH.get(self.provider.value, {})
        if self.provider == LLMProvider.OLLAMA:
            p_wh, c_wh = self.OLLAMA_ENERGY_WH_PER_1M
        else:
            p_wh, c_wh = provider_energy.get(self.model, (1.0, 2.0))
        return (prompt_tokens / 1_000_000) * p_wh + (completion_tokens / 1_000_000) * c_wh

    def _should_retry(self, e: httpx.HTTPStatusError) -> bool:
        """Determine if an HTTP error should be retried."""
        status = e.response.status_code
        # Retry on rate limit (429) and server errors (5xx)
        return status == 429 or 500 <= status < 600

    async def _complete_with_retry(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> tuple[str, dict]:
        """Generate a completion with retry logic. Returns (content, usage_dict)."""
        dispatcher = {
            LLMProvider.OPENAI: self._openai_complete,
            LLMProvider.ANTHROPIC: self._anthropic_complete,
            LLMProvider.GROQ: self._openai_complete,
            LLMProvider.GEMINI: self._gemini_complete,
            LLMProvider.COHERE: self._cohere_complete,
            LLMProvider.OLLAMA: self._ollama_complete,
            LLMProvider.OPENROUTER: self._openai_complete,
        }
        handler = dispatcher.get(self.provider)
        if not handler:
            raise ValueError(f"Unsupported provider: {self.provider}")

        last_exc = None
        for attempt in range(5):
            try:
                content, usage = await handler(prompt, system, json_mode)
                # Enrich usage with cost/energy but do NOT log here — caller handles logging
                if self.user_id:
                    usage["energy_wh"] = self._calculate_energy(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
                    usage["cost_usd"] = self._calculate_cost(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
                return content, usage
            except httpx.HTTPStatusError as e:
                last_exc = e
                if not self._should_retry(e):
                    status = e.response.status_code
                    if status == 401:
                        raise ValueError(f"LLM authentication failed (401): Invalid API key for {self.provider.value}")
                    elif status == 403:
                        raise ValueError(f"LLM access forbidden (403): Check API key permissions for {self.provider.value}")
                    elif status == 404:
                        raise ValueError(f"LLM model not found (404): Model '{self.model}' may not exist for {self.provider.value}")
                    elif status == 422:
                        raise ValueError(f"LLM request invalid (422): {e.response.text[:200]}")
                    raise ValueError(f"LLM request failed with HTTP {status}: {e.response.text[:200]}")
                wait = min(2 ** attempt * 2, 30)
                await asyncio.sleep(wait)
            except Exception as e:
                last_exc = e
                wait = min(2 ** attempt * 2, 30)
                await asyncio.sleep(wait)

        if last_exc:
            if isinstance(last_exc, httpx.HTTPStatusError):
                status = last_exc.response.status_code
                raise ValueError(f"LLM request failed after 5 retries (HTTP {status}): {last_exc.response.text[:200]}")
            raise ValueError(f"LLM request failed after 5 retries: {last_exc}")
        raise ValueError("LLM request failed: unknown error")

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> str:
        """Generate a completion. Returns the text response (backward compatible)."""
        content, usage = await self._complete_with_retry(prompt, system, json_mode)
        if self.user_id:
            _log_usage_background(self.user_id, self.provider.value, self.model, usage)
        return content

    async def complete_with_usage(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> dict:
        """Generate a completion with token usage info. Returns dict with content and usage."""
        content, usage = await self._complete_with_retry(prompt, system, json_mode)
        if self.user_id:
            _log_usage_background(self.user_id, self.provider.value, self.model, usage)
        return {"content": content, "usage": usage}

    async def stream_complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion. Yields text chunks."""
        dispatcher = {
            LLMProvider.OPENAI: self._openai_stream,
            LLMProvider.ANTHROPIC: self._anthropic_stream,
            LLMProvider.GROQ: self._openai_stream,
            LLMProvider.GEMINI: self._gemini_stream,
            LLMProvider.COHERE: self._cohere_stream,
            LLMProvider.OLLAMA: self._ollama_stream,
            LLMProvider.OPENROUTER: self._openai_stream,
        }
        handler = dispatcher.get(self.provider)
        if not handler:
            raise ValueError(f"Unsupported provider for streaming: {self.provider}")
        async for chunk in handler(prompt, system, json_mode):
            yield chunk

    # ── OpenAI / Groq / OpenRouter ────────────────────────────────────────────

    async def _openai_complete(
        self, prompt: str, system: Optional[str], json_mode: bool
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider == LLMProvider.OPENROUTER:
            headers["HTTP-Referer"] = "http://localhost:3000"
            headers["X-Title"] = "ResearchIDE"

        base = self.base_urls[self.provider]
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            usage = data.get("usage", {})
            return (
                data["choices"][0]["message"]["content"],
                {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "cost_usd": self._calculate_cost(
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0),
                    ),
                    "energy_wh": self._calculate_energy(
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0),
                    ),
                },
            )

    async def _openai_stream(self, prompt: str, system: Optional[str], json_mode: bool) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": system}] if system else []
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if self.provider == LLMProvider.OPENROUTER:
            headers["HTTP-Referer"] = "http://localhost:3000"
            headers["X-Title"] = "ResearchIDE"

        import asyncio
        base = self.base_urls[self.provider]

        last_exc = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream("POST", f"{base}/chat/completions", headers=headers, json=payload) as resp:
                        if resp.status_code == 429:
                            wait = min(2 ** attempt, 8)
                            await asyncio.sleep(wait)
                            continue
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if line.startswith("data: "):
                                line = line[6:]
                                if line == "[DONE]":
                                    break
                                try:
                                    data = json.loads(line)
                                    if data["choices"][0]["delta"].get("content"):
                                        yield data["choices"][0]["delta"]["content"]
                                except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                                    pass
                        return
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    last_exc = e
                    wait = min(2 ** attempt, 8)
                    await asyncio.sleep(wait)
                    continue
                raise
        if last_exc:
            raise last_exc

    # ── Anthropic ─────────────────────────────────────────────────────────────

    async def _anthropic_complete(
        self, prompt: str, system: Optional[str], json_mode: bool
    ) -> str:
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        if json_mode:
            # Anthropic doesn't have a JSON mode flag, but we can hint in system
            payload["system"] = (system or "") + "\nRespond with valid JSON only."

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        base = self.base_urls[LLMProvider.ANTHROPIC]
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base}/messages",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            usage = data.get("usage", {})
            return (
                data["content"][0]["text"],
                {
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                    "cost_usd": self._calculate_cost(
                        usage.get("input_tokens", 0),
                        usage.get("output_tokens", 0),
                    ),
                    "energy_wh": self._calculate_energy(
                        usage.get("input_tokens", 0),
                        usage.get("output_tokens", 0),
                    ),
                },
            )

    async def _anthropic_stream(self, prompt: str, system: Optional[str], json_mode: bool) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True,
        }
        if system:
            payload["system"] = system

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_urls[LLMProvider.ANTHROPIC]}/messages", headers=headers, json=payload) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("type") == "content_block_delta" and "text" in data.get("delta", {}):
                                yield data["delta"]["text"]
                        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                            pass

    # ── Gemini ─────────────────────────────────────────────────────────

    async def _gemini_complete(
        self, prompt: str, system: Optional[str], json_mode: bool
    ) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        base = self.base_urls[LLMProvider.GEMINI]
        url = f"{base}/models/{self.model}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", 0)
            completion_tokens = usage.get("candidatesTokenCount", 0)
            return (
                data["candidates"][0]["content"]["parts"][0]["text"],
                {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "cost_usd": self._calculate_cost(prompt_tokens, completion_tokens),
                    "energy_wh": self._calculate_energy(prompt_tokens, completion_tokens),
                },
            )

    async def _gemini_stream(self, prompt: str, system: Optional[str], json_mode: bool) -> AsyncGenerator[str, None]:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        url = f"{self.base_urls[LLMProvider.GEMINI]}/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "candidates" in data and len(data["candidates"]) > 0:
                                parts = data["candidates"][0].get("content", {}).get("parts", [])
                                if parts and "text" in parts[0]:
                                    yield parts[0]["text"]
                        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                            pass

    # ── Cohere ────────────────────────────────────────────────────────────────

    async def _cohere_complete(
        self, prompt: str, system: Optional[str], json_mode: bool
    ) -> str:
        payload = {
            "model": self.model,
            "message": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if system:
            payload["preamble"] = system

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        base = self.base_urls[LLMProvider.COHERE]
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{base}/chat", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            meta = data.get("meta", {}).get("tokens", {})
            prompt_tokens = meta.get("input_tokens", 0)
            completion_tokens = meta.get("output_tokens", 0)
            return (
                data["text"],
                {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "cost_usd": self._calculate_cost(prompt_tokens, completion_tokens),
                    "energy_wh": self._calculate_energy(prompt_tokens, completion_tokens),
                },
            )

    async def _cohere_stream(self, prompt: str, system: Optional[str], json_mode: bool) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "message": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        if system:
            payload["preamble"] = system
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_urls[LLMProvider.COHERE]}/chat", headers=headers, json=payload) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get("event_type") == "text-generation":
                                yield data["text"]
                        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                            pass

    # ── Ollama ────────────────────────────────────────────────────────────────

    async def _ollama_complete(
        self, prompt: str, system: Optional[str], json_mode: bool
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"

        base = self.base_urls[LLMProvider.OLLAMA]
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(f"{base}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            return (
                data["message"]["content"],
                {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "cost_usd": 0.0,
                    "energy_wh": self._calculate_energy(prompt_tokens, completion_tokens),
                },
            )

    async def _ollama_stream(self, prompt: str, system: Optional[str], json_mode: bool) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        if system:
            payload["messages"].insert(0, {"role": "system", "content": system})
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_urls[LLMProvider.OLLAMA]}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                            pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def test_connection(self) -> dict:
        """Test if the LLM provider is reachable and the key is valid."""
        try:
            original_max = self.max_tokens
            self.max_tokens = 10
            # Call the provider handler directly to avoid retry wrapper
            handler = {
                LLMProvider.OPENAI: self._openai_complete,
                LLMProvider.ANTHROPIC: self._anthropic_complete,
                LLMProvider.GROQ: self._openai_complete,
                LLMProvider.GEMINI: self._gemini_complete,
                LLMProvider.COHERE: self._cohere_complete,
                LLMProvider.OLLAMA: self._ollama_complete,
                LLMProvider.OPENROUTER: self._openai_complete,
            }.get(self.provider)
            if not handler:
                return {"success": False, "error": f"Unsupported provider: {self.provider}"}
            result = await handler("Say 'OK' in exactly one word.", None, False)
            self.max_tokens = original_max
            # Handle both old string return and new tuple return
            if isinstance(result, tuple):
                return {"success": True, "response": result[0][:50]}
            return {"success": True, "response": result[:50]}
        except Exception as e:
            self.max_tokens = original_max if 'original_max' in locals() else 2048
            error_msg = str(e)
            if "RetryError" in type(e).__name__:
                if hasattr(e, 'last_attempt') and e.last_attempt.exception():
                    error_msg = str(e.last_attempt.exception())
            return {"success": False, "error": error_msg}


async def get_ollama_models(base_url: str = "http://localhost:11434") -> list:
    """Fetch list of locally available Ollama models."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{base_url.rstrip('/')}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "id": m["name"],
                    "name": m["name"],
                    "size": f"{m.get('size', 0) / 1e9:.1f}GB",
                    "context": "varies",
                }
                for m in data.get("models", [])
            ]
    except Exception:
        return []


def build_llm_client_for_user(user, provider: Optional[str] = None, model: Optional[str] = None, max_tokens: Optional[int] = None) -> LLMClient:
    """
    Build an LLMClient using the user's stored preferences and API keys.
    """
    from core.security import decrypt_api_key

    selected_provider = provider or user.preferred_provider or "ollama"
    selected_model = model or user.preferred_model

    # Decrypt the API key for the selected provider
    api_key = None
    if user.llm_api_keys and selected_provider in user.llm_api_keys:
        api_key = decrypt_api_key(user.llm_api_keys[selected_provider])

    return LLMClient(
        provider=selected_provider,
        api_key=api_key,
        model=selected_model,
        base_url=user.ollama_base_url if selected_provider == "ollama" else None,
        max_tokens=max_tokens or 2048,
        user_id=user.id,
    )


def _log_usage_background(user_id: str, provider: str, model: str, usage: dict) -> None:
    """Fire-and-forget usage logging to DB."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_persist_usage(user_id, provider, model, usage))
    except Exception:
        pass


async def _persist_usage(user_id: str, provider: str, model: str, usage: dict) -> None:
    """Persist a UsageLog row."""
    try:
        from core.database import SessionLocal
        from models.project import UsageLog
        db = SessionLocal()
        try:
            log = UsageLog(
                user_id=user_id,
                provider=provider,
                model=model,
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                total_tokens=int(usage.get("total_tokens", 0)),
                cost_usd=round(float(usage.get("cost_usd", 0.0)), 8),
                energy_wh=round(float(usage.get("energy_wh", 0.0)), 8),
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass  # Never crash the main request due to logging failure
