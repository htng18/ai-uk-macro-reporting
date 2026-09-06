import datetime as dt
import logging
from types import SimpleNamespace

import pytest

import ai_uk_macro_reporting.nodes.compose_monthly_report as compose_module
import ai_uk_macro_reporting.nodes.evaluate_report as evaluate_module
import ai_uk_macro_reporting.nodes.revise_report as revise_module
from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.tools import ModelRole, get_chat_model


class Report:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self, *, mode):
        assert mode == "json"
        return self.payload


def test_report_nodes_use_expected_model_roles():
    assert compose_module.synthesis_llm is get_chat_model(ModelRole.SYNTHESIS)
    assert evaluate_module.editorial_llm is get_chat_model(ModelRole.EDITORIAL)
    assert revise_module.editorial_llm is get_chat_model(ModelRole.EDITORIAL)


def _patch_compose_setup(monkeypatch):
    metadata = {"regime": "soft_landing"}
    inputs = {"source": "upstream reports"}
    monkeypatch.setattr(
        compose_module,
        "get_authoritative_metadata",
        lambda state: metadata,
    )
    monkeypatch.setattr(
        compose_module,
        "build_compose_inputs",
        lambda state, received_metadata: inputs,
    )
    monkeypatch.setattr(
        compose_module,
        "restore_authoritative_metadata",
        lambda report, received_metadata: report,
    )
    return metadata, inputs


def _patch_revision_setup(monkeypatch):
    metadata = {"regime": "soft_landing"}
    inputs = {"source": "evaluation"}
    monkeypatch.setattr(
        revise_module,
        "get_authoritative_metadata",
        lambda state: metadata,
    )
    monkeypatch.setattr(
        revise_module,
        "build_revision_inputs",
        lambda state, received_metadata: inputs,
    )
    monkeypatch.setattr(
        revise_module,
        "restore_authoritative_metadata",
        lambda report, received_metadata: report,
    )
    return metadata, inputs


def test_compose_monthly_report_happy_path_cleans_and_reports_leakage(monkeypatch):
    metadata, inputs = _patch_compose_setup(monkeypatch)
    generated = Report({"summary": "generated."})
    cleaned = Report({"summary": "cleaned."})
    calls = {}

    def fake_invoke(chain, received_inputs, **kwargs):
        calls.update(chain=chain, inputs=received_inputs, kwargs=kwargs)
        return SimpleNamespace(compose_monthly_report=generated)

    monkeypatch.setattr(compose_module, "invoke_chat_model", fake_invoke)
    monkeypatch.setattr(compose_module, "find_truncated_strings", lambda data: [])
    monkeypatch.setattr(
        compose_module,
        "cleanup_public_prose",
        lambda report, received_metadata: cleaned,
    )
    monkeypatch.setattr(
        compose_module,
        "find_public_prose_leakage",
        lambda data: [{"path": "summary"}],
    )

    result = compose_module.compose_monthly_report(SimpleNamespace())

    assert calls["chain"] is compose_module.compose_monthly_report_chain
    assert calls["inputs"] is inputs
    assert calls["kwargs"] == {
        "length_limit_message": LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        "quota_message": LLM_MODEL_QUOTA_MESSAGE,
    }
    assert result == {
        "compose_monthly_report": {"summary": "cleaned."},
        "prose_leakage_issues": [{"path": "summary"}],
        "prose_style_warnings": [],
    }
    assert metadata == {"regime": "soft_landing"}


def test_compose_monthly_report_retries_once_with_truncated_fields(monkeypatch):
    _, inputs = _patch_compose_setup(monkeypatch)
    first = Report({"summary": "incomplete"})
    second = Report({"summary": "complete."})
    invocations = []
    truncation_results = iter([["executive_summary.summary"], [], []])

    def fake_invoke(chain, received_inputs, **kwargs):
        invocations.append((chain, received_inputs))
        report = first if len(invocations) == 1 else second
        return SimpleNamespace(compose_monthly_report=report)

    monkeypatch.setattr(compose_module, "invoke_chat_model", fake_invoke)
    monkeypatch.setattr(
        compose_module,
        "find_truncated_strings",
        lambda data: next(truncation_results),
    )
    monkeypatch.setattr(
        compose_module,
        "cleanup_public_prose",
        lambda report, metadata: report,
    )
    monkeypatch.setattr(
        compose_module,
        "find_public_prose_leakage",
        lambda data: [],
    )

    class FakeReportModel:
        @staticmethod
        def model_validate(data):
            assert data == {"summary": "complete."}
            return second

    monkeypatch.setattr(compose_module, "ComposedMonthlyReport", FakeReportModel)

    result = compose_module.compose_monthly_report(SimpleNamespace())

    assert len(invocations) == 2
    assert invocations[1][0] is compose_module.compose_monthly_report_retry_chain
    assert invocations[1][1] == {
        **inputs,
        "truncated_fields": "executive_summary.summary",
    }
    assert result["compose_monthly_report"] == {"summary": "complete."}


def test_compose_monthly_report_validates_trimmed_retry(monkeypatch):
    _patch_compose_setup(monkeypatch)
    first = Report({"summary": "incomplete"})
    retry = Report({"summary": "still incomplete"})
    validated = Report({"summary": "trimmed."})
    invocations = iter(
        [
            SimpleNamespace(compose_monthly_report=first),
            SimpleNamespace(compose_monthly_report=retry),
        ]
    )
    truncation_results = iter([["summary"], ["summary"], [], []])
    captured = {}

    monkeypatch.setattr(
        compose_module,
        "invoke_chat_model",
        lambda *args, **kwargs: next(invocations),
    )
    monkeypatch.setattr(
        compose_module,
        "find_truncated_strings",
        lambda data: next(truncation_results),
    )

    def fake_trim(data):
        captured["trimmed"] = data
        return {"summary": "trimmed."}

    class FakeReportModel:
        @staticmethod
        def model_validate(data):
            captured["validated"] = data
            return validated

    monkeypatch.setattr(compose_module, "trim_incomplete_trailing_prose", fake_trim)
    monkeypatch.setattr(compose_module, "ComposedMonthlyReport", FakeReportModel)
    monkeypatch.setattr(
        compose_module,
        "cleanup_public_prose",
        lambda report, metadata: report,
    )
    monkeypatch.setattr(
        compose_module,
        "find_public_prose_leakage",
        lambda data: [],
    )

    result = compose_module.compose_monthly_report(SimpleNamespace())

    assert captured["trimmed"] == {"summary": "still incomplete"}
    assert captured["validated"] == {"summary": "trimmed."}
    assert result["compose_monthly_report"] == {"summary": "trimmed."}


def test_compose_monthly_report_rejects_persistent_truncation(monkeypatch):
    _patch_compose_setup(monkeypatch)
    response = SimpleNamespace(compose_monthly_report=Report({"summary": "incomplete"}))
    monkeypatch.setattr(
        compose_module,
        "invoke_chat_model",
        lambda *args, **kwargs: response,
    )
    monkeypatch.setattr(
        compose_module,
        "find_truncated_strings",
        lambda data: ["summary"],
    )
    monkeypatch.setattr(
        compose_module,
        "trim_incomplete_trailing_prose",
        lambda data: data,
    )

    with pytest.raises(ValueError, match="after one regeneration: summary"):
        compose_module.compose_monthly_report(SimpleNamespace())


def test_compose_monthly_report_rejects_truncation_introduced_by_cleanup(
    monkeypatch,
):
    _patch_compose_setup(monkeypatch)
    generated = Report({"summary": "complete."})
    cleaned = Report({"summary": "incomplete"})
    truncation_results = iter([[], ["summary"], ["summary"]])

    monkeypatch.setattr(
        compose_module,
        "invoke_chat_model",
        lambda *args, **kwargs: SimpleNamespace(compose_monthly_report=generated),
    )
    monkeypatch.setattr(
        compose_module,
        "cleanup_public_prose",
        lambda report, metadata: cleaned,
    )
    monkeypatch.setattr(
        compose_module,
        "find_truncated_strings",
        lambda data: next(truncation_results),
    )
    monkeypatch.setattr(
        compose_module,
        "trim_incomplete_trailing_prose",
        lambda data: data,
    )

    with pytest.raises(ValueError, match="after public prose cleanup: summary"):
        compose_module.compose_monthly_report(SimpleNamespace())


def test_evaluate_report_builds_invokes_validates_and_returns(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=evaluate_module.__name__)
    metadata = {"confidence": "high"}
    inputs = {"report": "draft"}
    evaluation_data = {
        "issues": [],
        "overall_evaluation": {"publication_verdict": "pass", "score": 9.0},
    }
    validated = []
    captured = {}
    monkeypatch.setattr(
        evaluate_module,
        "get_authoritative_metadata",
        lambda state: metadata,
    )
    monkeypatch.setattr(
        evaluate_module,
        "build_evaluation_inputs",
        lambda state, received_metadata: inputs,
    )

    def fake_invoke(chain, received_inputs, **kwargs):
        captured.update(chain=chain, inputs=received_inputs, kwargs=kwargs)
        return SimpleNamespace(evaluate_report=Report(evaluation_data))

    monkeypatch.setattr(evaluate_module, "invoke_chat_model", fake_invoke)
    monkeypatch.setattr(
        evaluate_module,
        "validate_evaluation_consistency",
        lambda data: validated.append(data),
    )

    result = evaluate_module.evaluate_report(
        SimpleNamespace(reporting_period=dt.date(2026, 8, 31))
    )

    assert captured["chain"] is evaluate_module.evaluate_report_chain
    assert captured["inputs"] is inputs
    assert validated == [evaluation_data]
    assert result == {
        "report_evaluation": {
            **evaluation_data,
            "reporting_period": "2026-08-31",
        }
    }
    assert "Evaluated score: 9.0" in caplog.messages


def test_evaluate_report_propagates_consistency_failure(monkeypatch):
    monkeypatch.setattr(
        evaluate_module,
        "get_authoritative_metadata",
        lambda state: {},
    )
    monkeypatch.setattr(
        evaluate_module,
        "build_evaluation_inputs",
        lambda state, metadata: {},
    )
    monkeypatch.setattr(
        evaluate_module,
        "invoke_chat_model",
        lambda *args, **kwargs: SimpleNamespace(
            evaluate_report=Report({"invalid": True})
        ),
    )

    def reject(data):
        raise ValueError("inconsistent evaluation")

    monkeypatch.setattr(evaluate_module, "validate_evaluation_consistency", reject)

    with pytest.raises(ValueError, match="inconsistent evaluation"):
        evaluate_module.evaluate_report(
            SimpleNamespace(reporting_period=dt.date(2026, 8, 31))
        )


def test_revise_report_applies_cleanup_and_refreshes_leakage_findings(monkeypatch):
    metadata, inputs = _patch_revision_setup(monkeypatch)
    revised = Report({"summary": "revised."})
    cleaned = Report({"summary": "cleaned."})
    captured = {}

    def fake_invoke(chain, received_inputs, **kwargs):
        captured.update(chain=chain, inputs=received_inputs)
        return revised

    monkeypatch.setattr(revise_module, "invoke_chat_model", fake_invoke)
    monkeypatch.setattr(revise_module, "find_truncated_strings", lambda data: [])

    def fake_cleanup(report, received_metadata):
        captured["cleanup"] = (report, received_metadata)
        return cleaned

    monkeypatch.setattr(revise_module, "cleanup_public_prose", fake_cleanup)
    monkeypatch.setattr(
        revise_module,
        "find_public_prose_leakage",
        lambda data: [{"path": "summary", "term": "remaining"}],
    )

    result = revise_module.revise_report(SimpleNamespace(revision_count=1))

    assert captured["chain"] is revise_module.revise_report_chain
    assert captured["inputs"] is inputs
    assert captured["cleanup"] == (revised, metadata)
    assert result == {
        "compose_monthly_report": {"summary": "cleaned."},
        "prose_leakage_issues": [{"path": "summary", "term": "remaining"}],
        "prose_style_warnings": [],
        "revision_count": 2,
    }


def test_revise_report_retries_and_trims_incomplete_prose(monkeypatch):
    _, inputs = _patch_revision_setup(monkeypatch)
    first = Report({"summary": "incomplete"})
    second = Report({"summary": "still incomplete"})
    reports = iter([first, second])
    truncation_results = iter([["summary"], ["summary"], [], []])
    invocations = []
    validated = Report({"summary": "validated."})
    captured = {}

    def fake_invoke(chain, received_inputs, **kwargs):
        invocations.append((chain, received_inputs))
        return next(reports)

    monkeypatch.setattr(revise_module, "invoke_chat_model", fake_invoke)
    monkeypatch.setattr(
        revise_module,
        "find_truncated_strings",
        lambda data: next(truncation_results),
    )
    monkeypatch.setattr(
        revise_module,
        "trim_incomplete_trailing_prose",
        lambda data: {"summary": "trimmed."},
    )

    class FakeReportModel:
        @staticmethod
        def model_validate(data):
            captured["validated"] = data
            return validated

    monkeypatch.setattr(revise_module, "ComposedMonthlyReport", FakeReportModel)
    monkeypatch.setattr(
        revise_module,
        "cleanup_public_prose",
        lambda report, metadata: report,
    )
    monkeypatch.setattr(
        revise_module,
        "find_public_prose_leakage",
        lambda data: [],
    )

    result = revise_module.revise_report(SimpleNamespace(revision_count=0))

    assert invocations[1][0] is revise_module.revise_report_retry_chain
    assert invocations[1][1] == {**inputs, "truncated_fields": "summary"}
    assert captured["validated"] == {"summary": "trimmed."}
    assert result == {
        "compose_monthly_report": {"summary": "validated."},
        "prose_leakage_issues": [],
        "prose_style_warnings": [],
        "revision_count": 1,
    }


def test_revise_report_rejects_persistent_truncation(monkeypatch):
    _patch_revision_setup(monkeypatch)
    monkeypatch.setattr(
        revise_module,
        "invoke_chat_model",
        lambda *args, **kwargs: Report({"summary": "incomplete"}),
    )
    monkeypatch.setattr(
        revise_module,
        "find_truncated_strings",
        lambda data: ["summary"],
    )
    monkeypatch.setattr(
        revise_module,
        "trim_incomplete_trailing_prose",
        lambda data: data,
    )

    with pytest.raises(ValueError, match="after one regeneration: summary"):
        revise_module.revise_report(SimpleNamespace(revision_count=0))


def test_revise_report_rejects_truncation_introduced_by_cleanup(monkeypatch):
    _patch_revision_setup(monkeypatch)
    revised = Report({"summary": "complete."})
    cleaned = Report({"summary": "incomplete"})
    truncation_results = iter([[], ["summary"], ["summary"]])

    monkeypatch.setattr(
        revise_module,
        "invoke_chat_model",
        lambda *args, **kwargs: revised,
    )
    monkeypatch.setattr(
        revise_module,
        "cleanup_public_prose",
        lambda report, metadata: cleaned,
    )
    monkeypatch.setattr(
        revise_module,
        "find_truncated_strings",
        lambda data: next(truncation_results),
    )
    monkeypatch.setattr(
        revise_module,
        "trim_incomplete_trailing_prose",
        lambda data: data,
    )

    with pytest.raises(ValueError, match="after public prose cleanup: summary"):
        revise_module.revise_report(SimpleNamespace(revision_count=0))
