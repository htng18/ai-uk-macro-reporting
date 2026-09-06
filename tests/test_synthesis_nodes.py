import datetime as dt
import json
from types import SimpleNamespace

import pytest

import ai_uk_macro_reporting.nodes.counter_analysis as counter_module
import ai_uk_macro_reporting.nodes.cross_theme_synthesis as cross_theme_module
import ai_uk_macro_reporting.nodes.outlook_scenarios as outlook_module
from ai_uk_macro_reporting.common import Confidence
from ai_uk_macro_reporting.tools import ModelRole, get_chat_model


class CrossThemeReport:
    def __init__(self):
        self.headline_assessment = SimpleNamespace(confidence="low")
        self.overall_confidence = SimpleNamespace(level="low")
        self.confidence_assessment = SimpleNamespace(classification="low")

    def model_dump(self, *, mode):
        assert mode == "json"
        return {
            "headline_confidence": self.headline_assessment.confidence,
            "overall_confidence": self.overall_confidence.level,
            "assessment_confidence": self.confidence_assessment.classification,
        }


class CounterReport:
    def __init__(self, regime="soft_landing"):
        self.central_thesis_under_review = SimpleNamespace(
            regime=regime,
            confidence="low",
        )
        self.overall_confidence = SimpleNamespace(level="low")

    def model_dump(self, *, mode):
        assert mode == "json"
        return {
            "regime": self.central_thesis_under_review.regime,
            "thesis_confidence": self.central_thesis_under_review.confidence,
            "overall_confidence": self.overall_confidence.level,
        }


class Dumpable:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self, *, mode):
        assert mode == "json"
        return self.payload


def _synthesis_state():
    return SimpleNamespace(
        reporting_period=dt.date(2026, 8, 31),
        output_and_demand_report={"theme": "output"},
        inflation_report={"theme": "inflation"},
        labour_market_report={"theme": "labour"},
        monetary_policy_report={"theme": "monetary"},
        monthly_change_analysis={"comparison_available": True},
        confidence_profile={
            "metrics": {"overall_confidence": "high"},
            "explanation": {},
        },
        cross_theme_report=SimpleNamespace(
            overall_macro_regime=SimpleNamespace(
                classification="soft_landing",
                assessment="Activity and inflation are broadly balanced.",
            )
        ),
        counter_analysis_report={"verdict": "survives"},
    )


def test_cross_theme_synthesis_restores_authoritative_confidence(monkeypatch):
    report = CrossThemeReport()
    captured = {}

    def fake_invoke(chain, inputs, **kwargs):
        captured.update(inputs)
        return SimpleNamespace(cross_theme_report=report)

    monkeypatch.setattr(cross_theme_module, "invoke_chat_model", fake_invoke)

    result = cross_theme_module.cross_theme_synthesis(_synthesis_state())

    assert result["cross_theme_report"] == {
        "headline_confidence": Confidence.HIGH,
        "overall_confidence": Confidence.HIGH,
        "assessment_confidence": Confidence.HIGH,
    }
    assert json.loads(captured["monthly_change_analysis"]) == {
        "comparison_available": True
    }
    assert captured["reporting_period"] == dt.date(2026, 8, 31)
    assert cross_theme_module.synthesis_llm is get_chat_model(ModelRole.SYNTHESIS)


def test_counter_analysis_restores_confidence_and_checks_regime(monkeypatch):
    report = CounterReport()
    captured = {}

    def fake_invoke(chain, inputs, **kwargs):
        captured.update(inputs)
        return SimpleNamespace(counter_analysis_report=report)

    monkeypatch.setattr(counter_module, "invoke_chat_model", fake_invoke)

    result = counter_module.counter_analysis(_synthesis_state())

    assert captured["central_regime"] == "soft_landing"
    assert captured["central_confidence"] == Confidence.HIGH
    assert captured["reporting_period"] == dt.date(2026, 8, 31)
    assert result["counter_analysis_report"]["thesis_confidence"] == Confidence.HIGH
    assert result["counter_analysis_report"]["overall_confidence"] == Confidence.HIGH


def test_counter_analysis_rejects_response_for_wrong_regime(monkeypatch):
    monkeypatch.setattr(
        counter_module,
        "invoke_chat_model",
        lambda *args, **kwargs: SimpleNamespace(
            counter_analysis_report=CounterReport("broad_cooling")
        ),
    )

    with pytest.raises(ValueError, match="reviewed the wrong regime"):
        counter_module.counter_analysis(_synthesis_state())


def test_outlook_scenarios_passes_horizon_and_serializes_result(monkeypatch):
    captured = {}

    def fake_invoke(chain, inputs, **kwargs):
        captured.update(inputs)
        return SimpleNamespace(
            outlook_scenarios_report=Dumpable({"scenarios": ["central"]})
        )

    monkeypatch.setattr(outlook_module, "invoke_chat_model", fake_invoke)

    result = outlook_module.outlook_scenarios(_synthesis_state())

    assert result == {"outlook_scenarios_report": {"scenarios": ["central"]}}
    assert captured["outlook_horizon"] == "next 3 to 6 months"
    assert captured["reporting_period"] == dt.date(2026, 8, 31)
    assert json.loads(captured["counter_analysis_report"]) == {"verdict": "survives"}
    assert outlook_module.synthesis_llm is get_chat_model(ModelRole.SYNTHESIS)
