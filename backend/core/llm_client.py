"""
Unified LLM Client
Supports: OpenAI, Anthropic, Groq, Google Gemini, Cohere, Ollama (local)

Usage:
    client = LLMClient(provider="openai", api_key="sk-...", model="gpt-4o")
    response = await client.complete("Your prompt here")
"""

import httpx
import json
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
    LLMProvider.GROQ: "llama-3.1-70b-versatile",
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
        {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B", "context": "128k"},
        {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B (Fastest)", "context": "128k"},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "context": "32k"},
        {"id": "gemma2-9b-it", "name": "Gemma2 9B", "context": "8k"},
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
    ):
        self.provider = LLMProvider(provider)
        self.api_key = api_key
        self.model = model or PROVIDER_DEFAULTS.get(self.provider, "llama3.2")
        self.temperature = temperature
        self.max_tokens = max_tokens

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

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> str:
        """Generate a completion. Returns the text response."""
        dispatcher = {
            LLMProvider.OPENAI: self._openai_complete,
            LLMProvider.ANTHROPIC: self._anthropic_complete,
            LLMProvider.GROQ: self._openai_complete,   # Groq is OpenAI-compatible
            LLMProvider.GEMINI: self._gemini_complete,
            LLMProvider.COHERE: self._cohere_complete,
            LLMProvider.OLLAMA: self._ollama_complete,
            LLMProvider.OPENROUTER: self._openai_complete,  # OpenRouter is OpenAI-compatible
        }
        handler = dispatcher.get(self.provider)
        if not handler:
            raise ValueError(f"Unsupported provider: {self.provider}")
        return await handler(prompt, system, json_mode)

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
            return data["choices"][0]["message"]["content"]

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

        base = self.base_urls[self.provider]
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{base}/chat/completions", headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        line = line[6:]
                        if line == "[DONE]":
                            break
                        try:
                            import json
                            data = json.loads(line)
                            if data["choices"][0]["delta"].get("content"):
                                yield data["choices"][0]["delta"]["content"]
                        except:
                            pass

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
            return data["content"][0]["text"]

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
                        except:
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
            return data["candidates"][0]["content"]["parts"][0]["text"]

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
                        except:
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
            return data["text"]

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
                        except:
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
            return data["message"]["content"]

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
                        except:
                            pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def test_connection(self) -> dict:
        """Test if the LLM provider is reachable and the key is valid."""
        try:
            result = await self.complete("Say 'OK' in exactly one word.", max_tokens=10 if hasattr(self, 'max_tokens') else None)
            return {"success": True, "response": result[:50]}
        except Exception as e:
            return {"success": False, "error": str(e)}


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


def build_llm_client_for_user(user, provider: Optional[str] = None, model: Optional[str] = None) -> LLMClient:
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
    )
