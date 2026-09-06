import datetime as dt
import json
from types import SimpleNamespace

import pytest

import ai_uk_macro_reporting.nodes.analyse_inflation as inflation_module
import ai_uk_macro_reporting.nodes.analyse_labour_market as labour_module
import ai_uk_macro_reporting.nodes.analyse_monetary_policy as monetary_module
import ai_uk_macro_reporting.nodes.analyse_output_and_demand as output_module
import ai_uk_macro_reporting.nodes.compute_confidence_profile as confidence_module
from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.tools import ModelRole, get_chat_model

REPORTING_PERIOD = dt.date(2026, 8, 31)


class Dumpable:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self, *, mode):
        assert mode == "json"
        return self.payload


@pytest.mark.parametrize(
    (
        "module",
        "node_name",
        "metric_key",
        "input_key",
        "result_attribute",
        "output_key",
    ),
    [
        (
            output_module,
            "analyse_output_and_demand",
            "output_demand",
            "output_demand_metrics",
            "output_and_demand_report",
            "output_and_demand_report",
        ),
        (
            inflation_module,
            "analyse_inflation",
            "inflation",
            "inflation_metrics",
            "inflation_report",
            "inflation_report",
        ),
        (
            labour_module,
            "analyse_labour_market",
            "labour_market",
            "labour_market_metrics",
            "labour_market_report",
            "labour_market_report",
        ),
        (
            monetary_module,
            "analyse_monetary_policy",
            "monetary_policy",
            "monetary_policy_metrics",
            "monetary_policy_report",
            "monetary_policy_report",
        ),
    ],
)
def test_analysis_node_passes_theme_metrics_and_serializes_result(
    monkeypatch,
    module,
    node_name,
    metric_key,
    input_key,
    result_attribute,
    output_key,
):
    calls = {}
    payload = {"assessment": metric_key}

    def fake_invoke(chain, inputs, **kwargs):
        calls.update(chain=chain, inputs=inputs, kwargs=kwargs)
        return SimpleNamespace(**{result_attribute: Dumpable(payload)})

    monkeypatch.setattr(module, "invoke_chat_model", fake_invoke)
    state = SimpleNamespace(
        metrics={metric_key: {"indicator": 1}},
        reporting_period=REPORTING_PERIOD,
    )

    result = getattr(module, node_name)(state)

    assert result == {output_key: payload}
    assert json.loads(calls["inputs"][input_key]) == {"indicator": 1}
    assert calls["inputs"]["reporting_period"] == REPORTING_PERIOD
    assert calls["kwargs"] == {
        "length_limit_message": LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        "quota_message": LLM_MODEL_QUOTA_MESSAGE,
    }
    assert module.analysis_llm is get_chat_model(ModelRole.ANALYSIS)


def test_analysis_node_uses_empty_metrics_when_theme_is_missing(monkeypatch):
    captured = {}

    def fake_invoke(chain, inputs, **kwargs):
        captured.update(inputs)
        return SimpleNamespace(inflation_report=Dumpable({"assessment": "empty"}))

    monkeypatch.setattr(inflation_module, "invoke_chat_model", fake_invoke)

    inflation_module.analyse_inflation(
        SimpleNamespace(metrics={}, reporting_period=REPORTING_PERIOD)
    )

    assert json.loads(captured["inflation_metrics"]) == {}


def test_analysis_node_propagates_model_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("model failed")

    monkeypatch.setattr(output_module, "invoke_chat_model", fail)

    with pytest.raises(RuntimeError, match="model failed"):
        output_module.analyse_output_and_demand(
            SimpleNamespace(metrics={}, reporting_period=REPORTING_PERIOD)
        )


def test_explain_confidence_profile_builds_complete_model_input(monkeypatch):
    captured = {}
    explanation = Dumpable({"summary": "confidence explanation"})

    def fake_invoke(chain, inputs, **kwargs):
        captured.update(inputs)
        return explanation

    monkeypatch.setattr(confidence_module, "invoke_chat_model", fake_invoke)
    state = SimpleNamespace(
        reporting_period=REPORTING_PERIOD,
        monthly_change_analysis={"comparison_available": True},
        output_and_demand_report={"theme": "output"},
        inflation_report={"theme": "inflation"},
        labour_market_report={"theme": "labour"},
        monetary_policy_report={"theme": "monetary"},
    )
    metrics = {
        "overall_confidence_score": 0.75,
        "overall_confidence": "medium",
        "theme_confidence_metrics": {"inflation": {"score": 0.6}},
    }

    result = confidence_module.explain_confidence_profile(state, metrics)

    assert result is explanation
    assert captured["overall_confidence_score"] == 0.75
    assert captured["overall_confidence"] == "medium"
    assert json.loads(captured["theme_confidence_metrics"]) == {
        "inflation": {"score": 0.6}
    }
    assert captured["reporting_period"] == REPORTING_PERIOD


def test_compute_confidence_profile_combines_metrics_and_explanation(monkeypatch):
    metrics = {
        "overall_confidence_score": 1.0,
        "overall_confidence": "high",
        "theme_confidence_metrics": {},
    }
    explanation = Dumpable({"summary": "high confidence"})
    state = SimpleNamespace()
    monkeypatch.setattr(
        confidence_module,
        "calculate_confidence_metrics",
        lambda received: metrics,
    )
    monkeypatch.setattr(
        confidence_module,
        "explain_confidence_profile",
        lambda state, confidence_metrics: explanation,
    )

    result = confidence_module.compute_confidence_profile(state)

    assert result == {
        "confidence_profile": {
            "metrics": metrics,
            "explanation": {"summary": "high confidence"},
        }
    }
