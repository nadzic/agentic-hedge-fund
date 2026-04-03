import pytest

from app.agents.services import llm


@pytest.fixture(autouse=True)
def reset_langfuse_handler_fixture() -> None:
    llm._langfuse_callback_handler = None


@pytest.mark.unit
def test_tracing_enabled_requires_both_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert llm._tracing_enabled() is False

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    assert llm._tracing_enabled() is False

    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    assert llm._tracing_enabled() is True


@pytest.mark.unit
def test_get_langfuse_callbacks_reuses_single_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    created: list[object] = []

    class FakeHandler:
        def __init__(self) -> None:
            created.append(self)

    monkeypatch.setattr(llm, "CallbackHandler", FakeHandler)

    callbacks_first = llm._get_langfuse_callbacks()
    callbacks_second = llm._get_langfuse_callbacks()

    assert len(created) == 1
    assert callbacks_first == callbacks_second
    assert callbacks_first[0] is created[0]


@pytest.mark.unit
def test_get_llm_raises_when_required_provider_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(OSError, match="OPENAI_API_KEY is not set"):
        llm.get_llm()


@pytest.mark.unit
def test_get_llm_calls_init_chat_model_with_normalized_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", " OpenAI ")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.setenv("LLM_MODEL_NAME", " gpt-4o-mini ")
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    captured: dict[str, object] = {}

    def _fake_init_chat_model(
        *,
        model: str,
        model_provider: str,
        callbacks: list[object],
    ) -> object:
        captured["model"] = model
        captured["provider"] = model_provider
        captured["callbacks"] = callbacks
        return object()

    monkeypatch.setattr(llm, "init_chat_model", _fake_init_chat_model)

    result = llm.get_llm()

    assert result is not None
    assert captured == {"model": "gpt-4o-mini", "provider": "openai", "callbacks": []}
