import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

def get_llm() -> BaseChatModel:
    model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
    provider = os.getenv("LLM_PROVIDER", "openai")  # openai | anthropic | ...
    # Optional: basic key guard per provider
    provider_key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_key = provider_key_map.get(provider)
    if env_key and not os.getenv(env_key):
        raise OSError(f"{env_key} is not set in environment/.env")
    return init_chat_model(
        model=model_name,
        model_provider=provider,
    )