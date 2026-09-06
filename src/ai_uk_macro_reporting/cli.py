"""Command-line interface for generating a monthly report."""

import argparse
import datetime as dt
import json
import logging
import os
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

from ai_uk_macro_reporting.calculation.metric_definitions import SIGNAL_CONFIG
from ai_uk_macro_reporting.presentation.render_report import export_report

log = logging.getLogger(__name__)
REQUIRED_COLUMNS = frozenset({"full_name", "date", "value"})
CONFIGURED_INDICATOR_NAMES = frozenset(SIGNAL_CONFIG)
ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
PASSING_PUBLICATION_VERDICTS = frozenset({"pass", "pass_with_minor_edits"})


def parse_iso_date(value: str) -> dt.date:
    if ISO_DATE_PATTERN.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("Date must use YYYY-MM-DD format")

    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Date must use YYYY-MM-DD format") from exc


def _is_valid_iso_date(value: object) -> bool:
    """Return whether a value is a valid YYYY-MM-DD calendar date string."""
    if not isinstance(value, str) or ISO_DATE_PATTERN.fullmatch(value) is None:
        return False

    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False

    return True


def load_rows(
    input_path: Path,
    *,
    ignore_unknown_indicators: bool = False,
) -> list[dict[str, Any]]:
    """Load and validate observations, optionally ignoring unknown indicators."""
    if not input_path.is_file():
        raise ValueError(f"Input file does not exist: {input_path}")

    suffix = input_path.suffix.casefold()

    if suffix == ".csv":
        dataframe = pd.read_csv(input_path)
    elif suffix == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))

        if isinstance(payload, dict):
            payload = payload.get("rows")

        if not isinstance(payload, list):
            raise ValueError(
                "JSON input must be a list of records or an object "
                "containing a 'rows' list"
            )

        dataframe = pd.DataFrame(payload)
    else:
        raise ValueError("Input must be a .csv or .json file")

    missing_columns = REQUIRED_COLUMNS - set(dataframe.columns)
    if missing_columns:
        raise ValueError(
            "Missing required input columns: " + ", ".join(sorted(missing_columns))
        )

    dataframe = dataframe[["full_name", "date", "value"]].copy()

    if dataframe.empty:
        raise ValueError("Input contains no observations")

    if dataframe["full_name"].isna().any():
        raise ValueError("full_name cannot be null")

    dataframe["full_name"] = dataframe["full_name"].astype(str)
    if dataframe["full_name"].str.strip().eq("").any():
        raise ValueError("full_name cannot be empty")

    unknown_indicators = sorted(
        set(dataframe["full_name"]) - CONFIGURED_INDICATOR_NAMES
    )
    if unknown_indicators:
        unknown_names = ", ".join(repr(name) for name in unknown_indicators)
        if not ignore_unknown_indicators:
            raise ValueError("Unknown full_name indicator(s): " + unknown_names)

        unknown_rows = dataframe["full_name"].isin(unknown_indicators)
        log.warning(
            "Ignoring %s observation(s) for unknown indicator(s): %s",
            int(unknown_rows.sum()),
            unknown_names,
        )
        dataframe = dataframe.loc[~unknown_rows].copy()

        if dataframe.empty:
            raise ValueError("Input contains no configured indicator observations")

    valid_dates = dataframe["date"].map(_is_valid_iso_date)
    if not valid_dates.all():
        invalid_dates = dataframe.loc[~valid_dates, "date"].drop_duplicates().tolist()
        raise ValueError(
            "date must contain valid calendar dates in YYYY-MM-DD format; "
            "invalid value(s): " + ", ".join(repr(value) for value in invalid_dates)
        )

    dataframe["value"] = pd.to_numeric(dataframe["value"], errors="raise")

    duplicate_rows = dataframe.duplicated(
        subset=["full_name", "date"],
        keep=False,
    )
    if duplicate_rows.any():
        duplicate_value_counts = (
            dataframe.loc[duplicate_rows]
            .groupby(["full_name", "date"], dropna=False)["value"]
            .nunique(dropna=False)
        )

        if (duplicate_value_counts > 1).any():
            raise ValueError(
                "Input contains conflicting values for the same full_name/date record"
            )

        dataframe = dataframe.drop_duplicates(
            subset=["full_name", "date"],
            keep="first",
        )

    return dataframe.to_dict(orient="records")


def generate_report(
    rows: list[dict[str, Any]],
    *,
    reporting_period: dt.date | None = None,
    previous_reporting_period: str | None = None,
) -> dict[str, Any]:
    """Invoke the report graph with caller-provided observations."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY is not configured. Copy .env.example to .env "
            "and add a valid API key."
        )

    from ai_uk_macro_reporting.graph import build_monthly_report

    initial_state: dict[str, Any] = {"rows": rows}

    if reporting_period is not None:
        initial_state["reporting_period"] = reporting_period

    if previous_reporting_period is not None:
        initial_state["previous_reporting_period"] = previous_reporting_period

    graph = build_monthly_report()
    return graph.invoke(initial_state)


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate a UK monthly macroeconomic report from a user-provided "
            "CSV or JSON file."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the user's CSV or JSON observations.",
    )
    parser.add_argument(
        "--reporting-period",
        type=parse_iso_date,
        help=(
            "Report as-of date in YYYY-MM-DD format. Defaults to the current UTC date."
        ),
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("output"),
        help="Directory for generated report files (default: output).",
    )
    parser.add_argument(
        "--name",
        default="monthly-report",
        help="Output filename without an extension (default: monthly-report).",
    )
    parser.add_argument(
        "--format",
        dest="formats",
        choices=("json", "html", "pdf"),
        nargs="+",
        default=("json", "html"),
        help="One or more output formats (default: json html).",
    )
    parser.add_argument(
        "--previous-reporting-period",
        help="Optional previous reporting period in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--ignore-unknown-indicators",
        action="store_true",
        help=(
            "Ignore rows whose full_name is not configured, logging every "
            "ignored indicator (default: reject them)."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Generate and export a report from command-line arguments."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    arguments = parse_arguments(argv)

    try:
        rows = load_rows(
            arguments.input,
            ignore_unknown_indicators=arguments.ignore_unknown_indicators,
        )
        log.info("Loaded %s observations", len(rows))
        result = generate_report(
            rows,
            reporting_period=arguments.reporting_period,
            previous_reporting_period=arguments.previous_reporting_period,
        )

        report = result.get("compose_monthly_report")
        if report is None:
            raise RuntimeError("The graph completed without a composed report")

        overall_evaluation = result.get("report_evaluation", {}).get(
            "overall_evaluation", {}
        )
        final_verdict = overall_evaluation.get("publication_verdict", "unavailable")
        final_score = overall_evaluation.get("score", "unavailable")
        revision_count = result.get("revision_count", 0)

        if final_verdict in PASSING_PUBLICATION_VERDICTS:
            log.info("FINAL PUBLICATION VERDICT: %s", str(final_verdict).upper())
        else:
            log.warning(
                "FINAL PUBLICATION VERDICT: %s — the report did not pass final "
                "evaluation and is being exported for review, not as "
                "publication-ready output.",
                str(final_verdict).upper(),
            )

        written_files = export_report(
            report,
            output_directory=arguments.output_directory,
            basename=arguments.name,
            formats=arguments.formats,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        log.error("%s", exc)
        raise SystemExit(1) from exc

    for report_format, path in written_files.items():
        log.info("Saved %s report: %s", report_format.upper(), path)

    log.info("Revisions: %s", revision_count)
    log.info("Final evaluation score: %s", final_score)
