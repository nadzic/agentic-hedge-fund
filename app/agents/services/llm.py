import os
from typing import Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langfuse.langchain import CallbackHandler

_ = load_dotenv()
_langfuse_callback_handler: CallbackHandler | None = None


def _tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def _get_langfuse_callbacks() -> list[Any]:
    global _langfuse_callback_handler
    if not _tracing_enabled():
        return []

    if _langfuse_callback_handler is None:
        _langfuse_callback_handler = CallbackHandler()
    return [_langfuse_callback_handler]


def get_llm() -> BaseChatModel:
    model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
    provider = os.getenv("LLM_PROVIDER", "openai")  # openai | anthropic | ...
    provider_key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_key = provider_key_map.get(provider)
    if env_key and not os.getenv(env_key):
        raise OSError(f"{env_key} is not set in environment/.env")

    callbacks = _get_langfuse_callbacks()
    return init_chat_model(
        model=model_name,
        model_provider=provider,
        callbacks=callbacks,
    )