# Ollama backend — local/offline fallback provider.
# Uses the Ollama HTTP API (not a subprocess), so it works the same way
# inside a container or against a remote Ollama host.

from __future__ import annotations

import httpx

from copilot.config import Settings
from copilot.llm.providers.base import LLMResponse
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider:
    name = "ollama"

    def __init__(self, settings: Settings):
        self.model = settings.ollama_model
        self._host = settings.ollama_host.rstrip("/")
        self._default_temperature = settings.llm_temperature
        logger.info(
            "ollama provider initialized (model=%s, host=%s)", self.model, self._host
        )

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
                if temperature is not None
                else self._default_temperature,
            },
        }
        if system:
            payload["system"] = system
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{self._host}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

        return LLMResponse(
            text=(data.get("response") or "").strip(),
            model=self.model,
            provider=self.name,
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
        )
