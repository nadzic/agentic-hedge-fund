from typing import Protocol, cast

import pytest

from app.agents.graph import workflow
from app.agents.graph.nodes.request_clarification import (
    request_clarification_node as real_request_clarification_node,
)
from app.agents.graph.nodes.risk_manager import risk_manager_node as real_risk_manager_node
from app.agents.graph.nodes.synthesizer import synthesizer_node as real_synthesizer_node
from app.agents.graph.schemas import (
    AnalystOutput,
    RiskLimits,
    Signal,
    SignalInput,
)
from app.agents.graph.state import HedgeFundState


class _GraphRunner(Protocol):
    def invoke(self, input: HedgeFundState, /) -> HedgeFundState: ...


def _initial_state(
    *,
    query: str = "Please analyze AAPL for swing trading setup.",
    symbol: str = "AAPL",
    horizon: str = "swing",
) -> HedgeFundState:
    return {
        "input": SignalInput(query=query, symbol=symbol, horizon=horizon),
        "risk_limits": RiskLimits(min_confidence=0.60, max_position_size=0.10),
        "analyst_tasks": [],
        "analyst_outputs": [],
        "suggestion": None,
        "warning": None,
        "error": None,
        "rag_context": None,
        "rag_citations": [],
        "is_input_valid": False,
        "missing_fields": [],
        "clarification_question": None,
    }


@pytest.mark.integration
def test_compiled_graph_routes_to_request_clarification_for_invalid_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def _symbol_resolver(state: HedgeFundState) -> dict[str, object | None]:
        called.append("symbol_resolver")
        return {"input": state["input"]}

    def _input_classifier_invalid(_: HedgeFundState) -> dict[str, object | None]:
        called.append("input_classifier")
        return {
            "is_input_valid": False,
            "missing_fields": ["valid horizon (intraday | swing | position)"],
            "clarification_question": "Please provide valid horizon.",
            "warning": "Input classifier: missing fields",
            "error": "input_validation_failed",
        }

    def _route_invalid(_: HedgeFundState) -> str:
        return "request_clarification"

    def _request_clarification(state: HedgeFundState) -> dict[str, object | None]:
        called.append("request_clarification")
        return real_request_clarification_node(state)

    def _must_not_run(_: HedgeFundState) -> dict[str, object | None]:
        raise AssertionError("This node must not run on clarification path.")

    monkeypatch.setattr(workflow, "symbol_resolver_node", _symbol_resolver)
    monkeypatch.setattr(workflow, "input_classifier_node", _input_classifier_invalid)
    monkeypatch.setattr(workflow, "route_after_classification", _route_invalid)
    monkeypatch.setattr(workflow, "request_clarification_node", _request_clarification)
    monkeypatch.setattr(workflow, "market_research_agent", _must_not_run)
    monkeypatch.setattr(workflow, "orchestrator_node", _must_not_run)
    monkeypatch.setattr(workflow, "fundamentals_analyst_node", _must_not_run)
    monkeypatch.setattr(workflow, "technicals_analyst_node", _must_not_run)
    monkeypatch.setattr(workflow, "valuation_analyst_node", _must_not_run)
    monkeypatch.setattr(workflow, "sentiment_analyst_node", _must_not_run)
    monkeypatch.setattr(workflow, "synthesizer_node", _must_not_run)
    monkeypatch.setattr(workflow, "risk_manager_node", _must_not_run)

    graph = cast(_GraphRunner, cast(object, workflow.build_graph()))
    result = graph.invoke(_initial_state(horizon="weekly"))

    assert called == ["symbol_resolver", "input_classifier", "request_clarification"]
    assert result["error"] == "input_validation_failed"
    assert result["suggestion"] is not None
    assert result["suggestion"].signal == Signal.NO_TRADE
    assert "Please provide valid horizon." in (result["warning"] or "")


@pytest.mark.integration
def test_compiled_graph_runs_full_fan_out_and_fan_in_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def _symbol_resolver(state: HedgeFundState) -> dict[str, object | None]:
        called.append("symbol_resolver")
        return {"input": state["input"]}

    def _input_classifier_valid(state: HedgeFundState) -> dict[str, object | None]:
        called.append("input_classifier")
        return {
            "input": state["input"],
            "is_input_valid": True,
            "missing_fields": [],
            "clarification_question": None,
            "warning": None,
            "error": None,
        }

    def _route_valid(_: HedgeFundState) -> str:
        return "market_research_agent"

    def _market_research(_: HedgeFundState) -> dict[str, object | None]:
        called.append("market_research_agent")
        return {
            "rag_context": "Mocked context",
            "rag_citations": ["doc://one"],
            "warning": None,
            "error": None,
        }

    def _fundamentals(_: dict[str, object]) -> dict[str, list[AnalystOutput]]:
        called.append("fundamentals_analyst_node")
        return {
            "analyst_outputs": [
                AnalystOutput(
                    analyst="fundamentals",
                    signal=Signal.BUY,
                    confidence=0.90,
                    reasoning="Fundamentals strong.",
                    metrics={"score": 0.9},
                )
            ]
        }

    def _technicals(_: dict[str, object]) -> dict[str, list[AnalystOutput]]:
        called.append("technicals_analyst_node")
        return {
            "analyst_outputs": [
                AnalystOutput(
                    analyst="technicals",
                    signal=Signal.BUY,
                    confidence=0.85,
                    reasoning="Technicals supportive.",
                    metrics={"score": 0.85},
                )
            ]
        }

    def _valuation(_: dict[str, object]) -> dict[str, list[AnalystOutput]]:
        called.append("valuation_analyst_node")
        return {
            "analyst_outputs": [
                AnalystOutput(
                    analyst="valuation",
                    signal=Signal.BUY,
                    confidence=0.80,
                    reasoning="Valuation attractive.",
                    metrics={"score": 0.8},
                )
            ]
        }

    def _sentiment(_: dict[str, object]) -> dict[str, list[AnalystOutput]]:
        called.append("sentiment_analyst_node")
        return {
            "analyst_outputs": [
                AnalystOutput(
                    analyst="sentiment",
                    signal=Signal.BUY,
                    confidence=0.75,
                    reasoning="Sentiment improving.",
                    metrics={"score": 0.75},
                )
            ]
        }

    def _synthesizer(state: HedgeFundState) -> dict[str, object | None]:
        called.append("synthesizer")
        return cast(dict[str, object | None], real_synthesizer_node(state))

    def _risk_manager(state: HedgeFundState) -> dict[str, object | None]:
        called.append("risk_manager")
        return real_risk_manager_node(state)

    monkeypatch.setattr(workflow, "symbol_resolver_node", _symbol_resolver)
    monkeypatch.setattr(workflow, "input_classifier_node", _input_classifier_valid)
    monkeypatch.setattr(workflow, "route_after_classification", _route_valid)
    monkeypatch.setattr(workflow, "market_research_agent", _market_research)
    monkeypatch.setattr(workflow, "fundamentals_analyst_node", _fundamentals)
    monkeypatch.setattr(workflow, "technicals_analyst_node", _technicals)
    monkeypatch.setattr(workflow, "valuation_analyst_node", _valuation)
    monkeypatch.setattr(workflow, "sentiment_analyst_node", _sentiment)
    monkeypatch.setattr(workflow, "synthesizer_node", _synthesizer)
    monkeypatch.setattr(workflow, "risk_manager_node", _risk_manager)

    graph = cast(_GraphRunner, cast(object, workflow.build_graph()))
    result = graph.invoke(_initial_state())

    expected_workers = {
        "fundamentals_analyst_node",
        "technicals_analyst_node",
        "valuation_analyst_node",
        "sentiment_analyst_node",
    }
    assert set(called).issuperset(
        {
            "symbol_resolver",
            "input_classifier",
            "market_research_agent",
            "synthesizer",
            "risk_manager",
        }
        | expected_workers
    )
    assert len(result["analyst_outputs"]) == 4
    assert result["suggestion"] is not None
    assert result["suggestion"].signal == Signal.BUY
    assert result["suggestion"].symbol == "AAPL"
    assert result["warning"] is None
    assert result["error"] is None
