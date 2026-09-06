import datetime as dt
from types import SimpleNamespace

import pytest

import ai_uk_macro_reporting.nodes.compare_monthly as compare_monthly_module
import ai_uk_macro_reporting.nodes.compute_metrics as compute_metrics_module
from ai_uk_macro_reporting.common import MAX_REVISION_ITERATIONS
from ai_uk_macro_reporting.nodes.route_after_evaluation import route_after_evaluation


def test_compute_metrics_builds_current_and_previous_snapshots(monkeypatch):
    calls = []

    def fake_snapshot(*, observations, observation_offset):
        calls.append((observations.copy(), observation_offset))
        return {"offset": observation_offset}

    monkeypatch.setattr(
        compute_metrics_module,
        "calculate_metrics_snapshot",
        fake_snapshot,
    )
    rows = [
        {"full_name": "GDP", "date": "2026-01-01", "value": 100},
        {"full_name": "GDP", "date": "2026-02-01", "value": 101},
    ]

    result = compute_metrics_module.compute_metrics(SimpleNamespace(rows=rows))

    assert result == {
        "metrics": {"offset": 0},
        "previous_metrics": {"offset": 1},
    }
    assert [offset for _, offset in calls] == [0, 1]
    assert calls[0][0].to_dict(orient="records") == rows


@pytest.mark.parametrize(
    ("previous_metrics", "previous_period"),
    [({}, "2026-01"), ({"output": {}}, None)],
)
def test_compare_monthly_state_marks_unavailable_history(
    previous_metrics,
    previous_period,
):
    state = SimpleNamespace(
        metrics={"output": {}},
        previous_metrics=previous_metrics,
        previous_reporting_period=previous_period,
        reporting_period=dt.date(2026, 8, 31),
    )

    result = compare_monthly_module.compare_monthly_state(state)[
        "monthly_change_analysis"
    ]

    assert result["comparison_available"] is False
    assert result["previous_reporting_period"] is None
    assert result["current_reporting_period"] == "2026-08-31"
    assert result["themes"] == []


def test_compare_monthly_state_delegates_available_comparison(monkeypatch):
    captured = {}

    def fake_compare(**kwargs):
        captured.update(kwargs)
        return {"themes": ["output"]}

    monkeypatch.setattr(
        compare_monthly_module,
        "compare_metric_snapshots",
        fake_compare,
    )
    state = SimpleNamespace(
        metrics={"current": True},
        previous_metrics={"previous": True},
        previous_reporting_period="2026-01-31",
        reporting_period=dt.date(2026, 8, 31),
    )

    result = compare_monthly_module.compare_monthly_state(state)[
        "monthly_change_analysis"
    ]

    assert captured["previous_metrics"] == {"previous": True}
    assert captured["current_metrics"] == {"current": True}
    assert captured["previous_reporting_period"] == "2026-01-31"
    assert captured["current_reporting_period"] == "2026-08-31"
    assert result == {"themes": ["output"], "comparison_available": True}


@pytest.mark.parametrize(
    ("verdict", "score", "issues", "revision_count", "expected"),
    [
        ("pass", 9.0, [], 0, "end"),
        ("pass", 8.99, [], 0, "revise_report"),
        ("pass", 9.5, [{"severity": "major"}], 0, "revise_report"),
        ("pass_with_minor_edits", 8.5, [], 0, "end"),
        ("pass_with_minor_edits", 8.49, [], 0, "revise_report"),
        ("revise", 5.0, [], MAX_REVISION_ITERATIONS, "end"),
        ("fail", 2.0, [{"severity": "critical"}], 0, "revise_report"),
    ],
)
def test_route_after_evaluation_covers_all_decisions(
    verdict,
    score,
    issues,
    revision_count,
    expected,
):
    state = SimpleNamespace(
        report_evaluation={
            "overall_evaluation": {
                "publication_verdict": verdict,
                "score": score,
            },
            "issues": issues,
        },
        revision_count=revision_count,
    )

    assert route_after_evaluation(state) == expected
