"""Render the final monthly report for people and downstream applications."""

import json
from collections.abc import Iterable, Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from pydantic import BaseModel

type ExportFormat = Literal["json", "html", "pdf"]

TEMPLATE_DIRECTORY = Path(__file__).with_name("templates")
DEFAULT_TEMPLATE = "monthly_report.html.j2"
SUPPORTED_FORMATS: frozenset[str] = frozenset({"json", "html", "pdf"})


def _normalise_report(report: BaseModel | Mapping[str, Any]) -> dict[str, Any]:
    """Convert a Pydantic model or mapping into JSON-compatible report data."""
    if isinstance(report, BaseModel):
        data: Mapping[str, Any] = report.model_dump(mode="json")
    elif isinstance(report, Mapping):
        data = report
    else:
        raise TypeError("report must be a Pydantic model or mapping")

    return json.loads(
        json.dumps(
            dict(data),
            ensure_ascii=False,
            default=str,
        )
    )


def _humanise(value: object) -> str:
    """Turn an enum-style value into a readable label."""
    if value is None:
        return "Not available"

    return str(value).replace("_", " ").strip().title()


@lru_cache(maxsize=1)
def _template_environment() -> Environment:
    """Return the cached, autoescaping Jinja environment for report templates."""
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIRECTORY),
        autoescape=select_autoescape(
            enabled_extensions=("html", "htm", "xml", "j2"),
            default_for_string=True,
        ),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["humanise"] = _humanise
    return environment


def render_report_html(
    report: BaseModel | Mapping[str, Any],
    *,
    template_name: str = DEFAULT_TEMPLATE,
) -> str:
    """Render a complete report as a self-contained HTML document."""
    template = _template_environment().get_template(template_name)
    return template.render(report=_normalise_report(report))


def export_report(
    report: BaseModel | Mapping[str, Any],
    *,
    output_directory: Path,
    basename: str = "monthly-report",
    formats: Iterable[ExportFormat] = ("json", "html"),
) -> dict[str, Path]:
    """Export the final report to one or more presentation formats.

    JSON is the canonical machine-readable result. HTML is the primary human-
    readable format. PDF is generated from the same HTML template when the
    optional ``weasyprint`` dependency is installed.
    """
    if not basename or Path(basename).name != basename:
        raise ValueError("basename must be a filename without directory components")

    requested_formats = tuple(dict.fromkeys(str(item).lower() for item in formats))

    if not requested_formats:
        raise ValueError("At least one export format is required")

    unsupported = set(requested_formats) - SUPPORTED_FORMATS
    if unsupported:
        raise ValueError("Unsupported report format: " + ", ".join(sorted(unsupported)))

    output_directory.mkdir(parents=True, exist_ok=True)
    report_data = _normalise_report(report)
    written_files: dict[str, Path] = {}

    if "json" in requested_formats:
        json_path = output_directory / f"{basename}.json"
        json_path.write_text(
            json.dumps(
                report_data,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        written_files["json"] = json_path

    html: str | None = None
    if "html" in requested_formats or "pdf" in requested_formats:
        html = render_report_html(report_data)

    if "html" in requested_formats:
        html_path = output_directory / f"{basename}.html"
        html_path.write_text(html or "", encoding="utf-8")
        written_files["html"] = html_path

    if "pdf" in requested_formats:
        try:
            from weasyprint import HTML
        except ImportError as exc:
            raise RuntimeError(
                "PDF export requires the optional PDF dependencies. "
                "Run the command with: uv run --extra pdf uk-macro-report ..."
            ) from exc

        pdf_path = output_directory / f"{basename}.pdf"
        try:
            HTML(
                string=html or "",
                base_url=str(TEMPLATE_DIRECTORY),
            ).write_pdf(pdf_path)
        except Exception as exc:
            raise RuntimeError(f"PDF export failed: {exc}") from exc
        written_files["pdf"] = pdf_path

    return written_files
