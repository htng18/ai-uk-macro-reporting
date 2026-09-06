"""Tests for shared report context and publication safeguards."""

import datetime as dt
import json
from types import SimpleNamespace

import pytest

import ai_uk_macro_reporting.report_safeguards as safeguards_module
from ai_uk_macro_reporting.common import Confidence, CounterVerdict, MacroRegime
from ai_uk_macro_reporting.prompts.compose_monthly_report import (
    compose_monthly_report_prompt,
)
from ai_uk_macro_reporting.report_context import (
    build_compose_inputs,
    build_evaluation_inputs,
    build_numeric_evidence_packet,
    build_revision_inputs,
    get_authoritative_metadata,
    serialize_prompt_data,
)
from ai_uk_macro_reporting.report_safeguards import (
    cleanup_public_prose,
    restore_authoritative_metadata,
    validate_evaluation_consistency,
)


def _metadata():
    return {
        "reporting_period": "2026-08-31",
        "regime": MacroRegime.SOFT_LANDING,
        "regime_display_name": "a soft-landing configuration",
        "verdict": CounterVerdict.SURVIVES,
        "output_direction": "positive",
        "inflation_direction": "disinflationary",
        "labour_classification": "balanced",
        "monetary_classification": "easing",
        "confidence": Confidence.HIGH,
    }


def _prompt_state():
    return SimpleNamespace(
        reporting_period=dt.date(2026, 8, 31),
        metrics={
            "output_demand": {
                "output": {
                    "overall_signal": {},
                    "GDP": {
                        "signal_score": 4,
                        "latest_value": 101,
                        "direction": "positive",
                    },
                }
            }
        },
        output_and_demand_report={"section": "output"},
        inflation_report={"section": "inflation"},
        labour_market_report={"section": "labour"},
        monetary_policy_report={"section": "monetary"},
        cross_theme_report={"section": "cross-theme"},
        counter_analysis_report={"section": "counter"},
        outlook_scenarios_report={"section": "outlook"},
        confidence_profile={"overall": "high"},
        monthly_change_analysis={"change": "stable"},
        compose_monthly_report={"report": "draft"},
        report_evaluation={"score": 7.5},
        prose_leakage_issues=[{"path": "executive_summary"}],
        prose_style_warnings=[
            {
                "field": "executive_summary.summary",
                "type": "classifier-like neutral wording",
                "matched_text": "remains neutral",
            }
        ],
        revision_count=2,
    )


def _unnormalized_report():
    return SimpleNamespace(
        reporting_period="2026-09-01",
        executive_summary=SimpleNamespace(
            macro_regime="mixed_transition",
            confidence="low",
        ),
        overall_assessment=SimpleNamespace(confidence="low"),
        risks_to_central_interpretation=SimpleNamespace(
            counter_analysis_verdict="materially_weakened"
        ),
        current_conditions=SimpleNamespace(
            output_and_demand=SimpleNamespace(direction="negative"),
            inflation=SimpleNamespace(direction="inflationary"),
            labour_market=SimpleNamespace(classification="increasing_slack"),
            monetary_and_financial_conditions=SimpleNamespace(
                classification="tightening"
            ),
        ),
    )


def test_serialize_prompt_data_preserves_unicode_and_stringifies_unsupported_values():
    result = serialize_prompt_data(
        {
            "label": "UK’s outlook",
            "date": dt.date(2026, 8, 31),
        }
    )

    assert "UK’s outlook" in result
    assert json.loads(result) == {
        "label": "UK’s outlook",
        "date": "2026-08-31",
    }


def test_get_authoritative_metadata_validates_and_extracts_state_values():
    state = SimpleNamespace(
        reporting_period=dt.date(2026, 8, 31),
        cross_theme_report=SimpleNamespace(
            overall_macro_regime=SimpleNamespace(classification="soft_landing")
        ),
        counter_analysis_report=SimpleNamespace(
            verdict=SimpleNamespace(classification="survives")
        ),
        metrics={
            "output_demand": {
                "output": {
                    "overall_signal": {
                        "status": "available",
                        "direction": "positive",
                    }
                }
            }
        },
        inflation_report=SimpleNamespace(
            inflation_pressure_relationship=SimpleNamespace(direction="disinflationary")
        ),
        labour_market_report=SimpleNamespace(
            labour_market_relationship=SimpleNamespace(classification="balanced")
        ),
        monetary_policy_report=SimpleNamespace(
            monetary_policy_relationship=SimpleNamespace(classification="easing")
        ),
        confidence_profile={"metrics": {"overall_confidence": "high"}},
    )

    assert get_authoritative_metadata(state) == _metadata()


def test_get_authoritative_metadata_preserves_insufficient_output_evidence():
    state = SimpleNamespace(
        reporting_period=dt.date(2026, 8, 31),
        cross_theme_report=SimpleNamespace(
            overall_macro_regime=SimpleNamespace(classification="insufficient_evidence")
        ),
        counter_analysis_report=SimpleNamespace(
            verdict=SimpleNamespace(classification="insufficient_evidence")
        ),
        metrics={
            "output_demand": {
                "output": {"overall_signal": {"status": "insufficient_data"}}
            }
        },
        inflation_report=SimpleNamespace(
            inflation_pressure_relationship=SimpleNamespace(direction="unclear")
        ),
        labour_market_report=SimpleNamespace(
            labour_market_relationship=SimpleNamespace(
                classification="insufficient_evidence"
            )
        ),
        monetary_policy_report=SimpleNamespace(
            monetary_policy_relationship=SimpleNamespace(
                classification="insufficient_evidence"
            )
        ),
        confidence_profile={"metrics": {"overall_confidence": "low"}},
    )

    metadata = get_authoritative_metadata(state)

    assert metadata["output_direction"] == "insufficient_evidence"


@pytest.mark.parametrize(
    ("field", "invalid_value", "expected_exception"),
    [
        ("regime", "unknown", ValueError),
        ("verdict", "unknown", ValueError),
        ("confidence", "unknown", ValueError),
    ],
)
def test_get_authoritative_metadata_rejects_invalid_enums(
    field,
    invalid_value,
    expected_exception,
):
    state = SimpleNamespace(
        reporting_period=dt.date(2026, 8, 31),
        cross_theme_report=SimpleNamespace(
            overall_macro_regime=SimpleNamespace(classification="soft_landing")
        ),
        counter_analysis_report=SimpleNamespace(
            verdict=SimpleNamespace(classification="survives")
        ),
        metrics={
            "output_demand": {
                "output": {
                    "overall_signal": {
                        "status": "available",
                        "direction": "positive",
                    }
                }
            }
        },
        inflation_report=SimpleNamespace(
            inflation_pressure_relationship=SimpleNamespace(direction="disinflationary")
        ),
        labour_market_report=SimpleNamespace(
            labour_market_relationship=SimpleNamespace(classification="balanced")
        ),
        monetary_policy_report=SimpleNamespace(
            monetary_policy_relationship=SimpleNamespace(classification="easing")
        ),
        confidence_profile={"metrics": {"overall_confidence": "high"}},
    )

    if field == "regime":
        state.cross_theme_report.overall_macro_regime.classification = invalid_value
    elif field == "verdict":
        state.counter_analysis_report.verdict.classification = invalid_value
    else:
        state.confidence_profile["metrics"]["overall_confidence"] = invalid_value

    with pytest.raises(expected_exception):
        get_authoritative_metadata(state)


def test_build_numeric_evidence_packet_ranks_limits_and_skips_reserved_entries():
    metrics = {
        "output": {
            "overall_breadth": {"classification": "mixed"},
            "activity": {
                "overall_signal": {"direction": "positive"},
                "GDP": {"signal_score": 2, "latest_value": 100},
                "Services": {"signal_score": 5, "latest_value": 110},
                "metadata": "ignored",
            },
            "malformed_sector": [],
            "demand": {
                "Retail": {"signal_score": 3, "latest_value": 90},
            },
        }
    }

    evidence = build_numeric_evidence_packet(metrics, max_indicators_per_theme=2)

    assert [item["indicator"] for item in evidence["output"]] == [
        "Services",
        "Retail",
    ]
    assert evidence["output"][0]["sector"] == "activity"
    assert evidence["output"][0]["signal_score"] == 5


def test_build_numeric_evidence_packet_defaults_missing_scores_to_zero():
    metrics = {
        "output": {
            "activity": {
                "GDP": {"latest_value": 100},
            }
        }
    }

    assert build_numeric_evidence_packet(metrics)["output"][0]["signal_score"] == 0


def test_build_numeric_evidence_packet_deduplicates_equivalent_signal_groups():
    metrics = {
        "output_demand": {
            "output": {
                "Monthly GDP Index": {"signal_score": 5},
                "Monthly GDP Growth Rate": {"signal_score": 6},
                "Construction output index": {"signal_score": 4},
            }
        }
    }

    evidence = build_numeric_evidence_packet(metrics, max_indicators_per_theme=2)

    assert [item["indicator"] for item in evidence["output_demand"]] == [
        "Monthly GDP Growth Rate",
        "Construction output index",
    ]


def test_restore_authoritative_metadata_restores_every_authoritative_field():
    report = _unnormalized_report()

    result = restore_authoritative_metadata(report, _metadata())

    assert result is report
    assert report.reporting_period == "2026-08-31"
    assert report.executive_summary.macro_regime == MacroRegime.SOFT_LANDING
    assert report.executive_summary.confidence == Confidence.HIGH
    assert report.overall_assessment.confidence == Confidence.HIGH
    assert (
        report.risks_to_central_interpretation.counter_analysis_verdict
        == CounterVerdict.SURVIVES
    )
    assert report.current_conditions.output_and_demand.direction == "positive"
    assert report.current_conditions.inflation.direction == "disinflationary"
    assert report.current_conditions.labour_market.classification == "balanced"
    assert (
        report.current_conditions.monetary_and_financial_conditions.classification
        == "easing"
    )


def test_cleanup_public_prose_returns_original_when_no_leakage(monkeypatch):
    report = SimpleNamespace(model_dump=lambda mode: {"summary": "Public prose"})
    monkeypatch.setattr(safeguards_module, "find_public_prose_leakage", lambda data: [])

    def unexpected_invoke(*args, **kwargs):
        raise AssertionError("model should not be invoked without leakage")

    monkeypatch.setattr(safeguards_module, "invoke_chat_model", unexpected_invoke)

    assert cleanup_public_prose(report, _metadata()) is report


def test_cleanup_public_prose_invokes_model_and_normalizes_result(monkeypatch):
    report = SimpleNamespace(
        model_dump=lambda mode: {"summary": "Internal confidence terminology"}
    )
    cleaned_report = object()
    calls = {}
    monkeypatch.setattr(
        safeguards_module,
        "find_public_prose_leakage",
        lambda data: [{"path": "summary", "term": "confidence"}],
    )

    def fake_invoke(chain, inputs, **kwargs):
        calls["chain"] = chain
        calls["inputs"] = inputs
        calls["kwargs"] = kwargs
        return cleaned_report

    monkeypatch.setattr(safeguards_module, "invoke_chat_model", fake_invoke)
    monkeypatch.setattr(
        safeguards_module,
        "restore_authoritative_metadata",
        lambda cleaned, metadata: (cleaned, metadata),
    )

    result = cleanup_public_prose(report, _metadata())

    assert result == (cleaned_report, _metadata())
    assert calls["chain"] is safeguards_module.public_prose_cleanup_chain
    assert json.loads(calls["inputs"]["current_report"]) == {
        "summary": "Internal confidence terminology"
    }
    assert json.loads(calls["inputs"]["leakage_findings"]) == [
        {"path": "summary", "term": "confidence"}
    ]


def test_cleanup_public_prose_invokes_model_for_style_warning_alone(monkeypatch):
    report = SimpleNamespace(
        model_dump=lambda mode: {"summary": "Demand remains neutral."}
    )
    cleaned_report = object()
    calls = {}
    warning = {
        "field": "summary",
        "type": "classifier-like neutral wording",
        "matched_text": "remains neutral",
    }
    monkeypatch.setattr(
        safeguards_module,
        "find_public_prose_leakage",
        lambda data: [],
    )
    monkeypatch.setattr(
        safeguards_module,
        "find_public_prose_style_warnings",
        lambda data: [warning],
    )

    def fake_invoke(chain, inputs, **kwargs):
        calls["inputs"] = inputs
        return cleaned_report

    monkeypatch.setattr(safeguards_module, "invoke_chat_model", fake_invoke)
    monkeypatch.setattr(
        safeguards_module,
        "restore_authoritative_metadata",
        lambda cleaned, metadata: cleaned,
    )

    assert cleanup_public_prose(report, _metadata()) is cleaned_report
    assert json.loads(calls["inputs"]["leakage_findings"]) == []
    assert json.loads(calls["inputs"]["style_warnings"]) == [warning]
    assert json.loads(calls["inputs"]["authoritative_metadata"])["regime"] == (
        "soft_landing"
    )


def test_build_compose_inputs_includes_metadata_reports_and_numeric_evidence():
    inputs = build_compose_inputs(_prompt_state(), _metadata())

    assert inputs["reporting_period"] == dt.date(2026, 8, 31)
    assert inputs["central_regime"] == MacroRegime.SOFT_LANDING
    assert inputs["regime_display_name"] == "a soft-landing configuration"
    assert inputs["overall_confidence"] == Confidence.HIGH
    assert json.loads(inputs["output_demand_report"]) == {"section": "output"}
    assert (
        json.loads(inputs["numeric_evidence"])["output_demand"][0]["indicator"] == "GDP"
    )


def test_build_compose_inputs_matches_prompt_contract():
    inputs = build_compose_inputs(_prompt_state(), _metadata())

    assert set(inputs) == set(compose_monthly_report_prompt.input_variables)


def test_build_revision_inputs_increments_iteration_and_serializes_context():
    inputs = build_revision_inputs(_prompt_state(), _metadata())

    assert inputs["reporting_period"] == dt.date(2026, 8, 31)
    assert inputs["revision_iteration"] == 3
    assert inputs["outlook_horizon"] == "next 3 to 6 months"
    assert json.loads(inputs["composed_monthly_report"]) == {"report": "draft"}
    assert json.loads(inputs["report_evaluation"]) == {"score": 7.5}


def test_build_evaluation_inputs_includes_report_and_prose_findings():
    inputs = build_evaluation_inputs(_prompt_state(), _metadata())

    assert inputs["reporting_period"] == dt.date(2026, 8, 31)
    assert inputs["counter_verdict"] == CounterVerdict.SURVIVES
    assert json.loads(inputs["composed_monthly_report"]) == {"report": "draft"}
    assert json.loads(inputs["prose_leakage_issues"]) == [{"path": "executive_summary"}]
    assert json.loads(inputs["prose_style_warnings"]) == [
        {
            "field": "executive_summary.summary",
            "type": "classifier-like neutral wording",
            "matched_text": "remains neutral",
        }
    ]


@pytest.mark.parametrize(
    ("issues", "verdict", "score", "message"),
    [
        ([{"severity": "critical"}], "pass", 7.0, "critical issues"),
        ([{"severity": "critical"}], "revise", 8.0, "score above 7.9"),
        ([{"severity": "major"}], "pass_with_minor_edits", 7.0, "major issues"),
    ],
)
def test_validate_evaluation_consistency_rejects_conflicting_results(
    issues,
    verdict,
    score,
    message,
):
    evaluation = {
        "issues": issues,
        "overall_evaluation": {
            "publication_verdict": verdict,
            "score": score,
        },
    }

    with pytest.raises(ValueError, match=message):
        validate_evaluation_consistency(evaluation)


@pytest.mark.parametrize(
    ("issues", "verdict", "score"),
    [
        ([], "pass", 10.0),
        ([{"severity": "minor"}], "pass_with_minor_edits", 9.0),
        ([{"severity": "major"}], "revise", 8.0),
        ([{"severity": "critical"}], "fail", 7.9),
    ],
)
def test_validate_evaluation_consistency_accepts_compatible_results(
    issues,
    verdict,
    score,
):
    evaluation = {
        "issues": issues,
        "overall_evaluation": {
            "publication_verdict": verdict,
            "score": score,
        },
    }

    assert validate_evaluation_consistency(evaluation) is None
