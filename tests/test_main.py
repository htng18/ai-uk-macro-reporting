import datetime as dt
import logging

import pandas as pd
import pytest

import ai_uk_macro_reporting.cli as cli_module
from main import load_rows

ADDITIONAL_CONFIGURED_INDICATORS = [
    "Construction output monthly growth",
    "Job Vacancies",
    "Manufacturing output monthly growth",
    "Monthly Consumer Price Index Rate",
    "Monthly GDP Growth Rate",
    "Producer Price Input Index",
    "Producer Price Output Index",
    "Production output monthly growth",
    "Services output monthly growth",
    "UK EMU M2 Money Supply",
    "UK EMU M3 Money Supply",
    "UK House Price Index",
    "UK M4 Money Supply",
]


def test_parse_arguments_accepts_reporting_period():
    arguments = cli_module.parse_arguments(
        ["--input", "input.csv", "--reporting-period", "2026-08-31"]
    )

    assert arguments.reporting_period == dt.date(2026, 8, 31)


@pytest.mark.parametrize("invalid_date", ["20260831", "2026-W36-1", "2026-02-30"])
def test_parse_arguments_rejects_non_iso_reporting_period(invalid_date):
    with pytest.raises(SystemExit):
        cli_module.parse_arguments(
            ["--input", "input.csv", "--reporting-period", invalid_date]
        )


def test_load_rows_collapses_matching_duplicates(tmp_path):
    input_path = tmp_path / "input.csv"
    pd.DataFrame(
        [
            {"full_name": "Bank Rate", "date": "2026-08-01", "value": 4.0},
            {"full_name": "Bank Rate", "date": "2026-08-01", "value": 4.0},
        ]
    ).to_csv(input_path, index=False)

    assert load_rows(input_path) == [
        {"full_name": "Bank Rate", "date": "2026-08-01", "value": 4.0}
    ]


def test_load_rows_rejects_conflicting_duplicates(tmp_path):
    input_path = tmp_path / "input.csv"
    pd.DataFrame(
        [
            {"full_name": "Bank Rate", "date": "2026-08-01", "value": 4.0},
            {"full_name": "Bank Rate", "date": "2026-08-01", "value": 4.25},
        ]
    ).to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="conflicting values"):
        load_rows(input_path)


@pytest.mark.parametrize("invalid_date", ["09/03/2026", "2026-2-03", "2026-02-30"])
def test_load_rows_requires_valid_yyyy_mm_dd_dates(tmp_path, invalid_date):
    input_path = tmp_path / "input.csv"
    pd.DataFrame(
        [{"full_name": "Bank Rate", "date": invalid_date, "value": 4.0}]
    ).to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        load_rows(input_path)


@pytest.mark.parametrize(
    "unknown_name",
    ["Unknown indicator", "bank rate", " Bank Rate"],
)
def test_load_rows_rejects_unconfigured_indicator_names(tmp_path, unknown_name):
    input_path = tmp_path / "input.csv"
    pd.DataFrame(
        [{"full_name": unknown_name, "date": "2026-08-01", "value": 4.0}]
    ).to_csv(input_path, index=False)

    with pytest.raises(
        ValueError, match=rf"Unknown full_name indicator.*{unknown_name}"
    ):
        load_rows(input_path)


def test_load_rows_accepts_additional_configured_indicators(tmp_path):
    input_path = tmp_path / "input.csv"
    pd.DataFrame(
        [
            {"full_name": name, "date": "2026-08-01", "value": 1.0}
            for name in ADDITIONAL_CONFIGURED_INDICATORS
        ]
    ).to_csv(input_path, index=False)

    rows = load_rows(input_path)

    assert {row["full_name"] for row in rows} == set(ADDITIONAL_CONFIGURED_INDICATORS)


def test_load_rows_can_explicitly_ignore_unconfigured_indicators(
    tmp_path,
    caplog,
):
    input_path = tmp_path / "input.csv"
    pd.DataFrame(
        [
            {"full_name": "Bank Rate", "date": "2026-08-01", "value": 4.0},
            {
                "full_name": "Unconfigured GDP series",
                "date": "2026-08-01",
                "value": 0.3,
            },
        ]
    ).to_csv(input_path, index=False)

    with caplog.at_level(logging.WARNING):
        rows = load_rows(input_path, ignore_unknown_indicators=True)

    assert rows == [{"full_name": "Bank Rate", "date": "2026-08-01", "value": 4.0}]
    assert "Ignoring 1 observation(s)" in caplog.text
    assert "Unconfigured GDP series" in caplog.text


def test_load_rows_rejects_input_with_only_ignored_indicators(tmp_path):
    input_path = tmp_path / "input.csv"
    pd.DataFrame(
        [
            {
                "full_name": "Unconfigured GDP series",
                "date": "2026-08-01",
                "value": 0.3,
            }
        ]
    ).to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="no configured indicator observations"):
        load_rows(input_path, ignore_unknown_indicators=True)


def test_main_warns_before_exporting_report_that_requires_revision(
    monkeypatch,
    caplog,
    tmp_path,
):
    events = []
    result = {
        "compose_monthly_report": {"report": "draft"},
        "report_evaluation": {
            "overall_evaluation": {
                "publication_verdict": "revise",
                "score": 7.5,
            }
        },
        "revision_count": 2,
    }

    monkeypatch.setattr(
        cli_module,
        "load_rows",
        lambda path, **kwargs: [{"row": True}],
    )
    monkeypatch.setattr(
        cli_module,
        "generate_report",
        lambda rows, reporting_period=None, previous_reporting_period=None: result,
    )

    def fake_export(*args, **kwargs):
        events.append(caplog.text)
        return {"json": tmp_path / "report.json"}

    monkeypatch.setattr(cli_module, "export_report", fake_export)

    with caplog.at_level(logging.INFO):
        cli_module.main(["--input", str(tmp_path / "input.csv")])

    assert "FINAL PUBLICATION VERDICT: REVISE" in events[0]
    assert "not as publication-ready output" in events[0]
    assert any(
        record.levelno == logging.WARNING
        and "FINAL PUBLICATION VERDICT: REVISE" in record.message
        for record in caplog.records
    )
