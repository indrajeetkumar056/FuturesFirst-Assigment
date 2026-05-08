from __future__ import annotations

import logging

from dataclasses import dataclass

from openai import APIError, OpenAI

from app.core.config import settings

log = logging.getLogger("app.llm")


@dataclass(frozen=True)
class LlmChoice:
    provider: str
    base_url: str
    api_key: str
    model: str


def _resolve_choice() -> LlmChoice:
    provider = settings.llm_provider.lower().strip()
    if provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        return LlmChoice(
            provider="groq",
            base_url=settings.groq_base_url,
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        )
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return LlmChoice(
            provider="openai",
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    raise ValueError("LLM_PROVIDER must be 'groq' or 'openai'")


def get_client() -> tuple[OpenAI, str, str]:
    choice = _resolve_choice()
    client = OpenAI(api_key=choice.api_key, base_url=choice.base_url)
    return client, choice.model, choice.provider


def chat_completion(*, system: str, user: str) -> str:
    client, model, _provider = get_client()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""
    except APIError as e:
        log.warning("LLM API error (model=%s): %s", model, e, exc_info=True)
        raise
    except Exception as e:
        log.exception("LLM unexpected error (model=%s)", model)
        raise

