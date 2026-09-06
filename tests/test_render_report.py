import json

import pytest

from ai_uk_macro_reporting.presentation.render_report import (
    export_report,
    render_report_html,
)


def sample_report() -> dict:
    return {
        "reporting_period": "2026-08-31",
        "executive_summary": {
            "summary": "Activity was stable while <script>alert('x')</script>.",
            "macro_regime": "balanced_stability",
            "confidence": "medium",
            "confidence_explanation": "The evidence is reasonably broad.",
            "central_outlook": "Conditions are expected to remain stable.",
            "main_qualification": "Several indicators remain volatile.",
        },
        "current_conditions": {
            "output_and_demand": {
                "direction": "neutral",
                "assessment": "Output was broadly stable.",
                "key_qualification": "Construction was weaker.",
            },
            "inflation": {
                "direction": "disinflationary",
                "assessment": "Inflation pressure eased.",
                "key_qualification": "Services inflation remained elevated.",
            },
            "labour_market": {
                "classification": "easing_tightness",
                "assessment": "Labour demand softened.",
                "key_qualification": "Wage growth remained firm.",
            },
            "monetary_and_financial_conditions": {
                "classification": "broadly_stable",
                "assessment": "Financial conditions changed little.",
                "key_qualification": "Long-term yields were volatile.",
            },
        },
        "cross_theme_assessment": {
            "assessment": "The themes point to broad stability.",
            "key_relationships": [
                "Softer demand reduced inflation pressure.",
                "Wage growth limited the pace of disinflation.",
            ],
            "regime_interpretation": "The economy remained broadly stable.",
        },
        "risks_to_central_interpretation": {
            "counter_analysis_verdict": "credible_but_not_dominant",
            "assessment": "The central interpretation has meaningful risks.",
            "key_risks": [
                {
                    "risk": "Inflation persistence",
                    "significance": "Services prices could remain elevated.",
                }
            ],
            "strongest_counter_case": "Demand could weaken more rapidly.",
        },
        "conditional_outlook": {
            "horizon": "next 3 to 6 months",
            "scenarios": [
                {
                    "scenario_type": "central",
                    "title": "Gradual stabilization",
                    "outlook": "Activity and inflation change gradually.",
                    "confirmation_to_watch": ["Monthly GDP"],
                },
                {
                    "scenario_type": "upside",
                    "title": "Demand strengthens",
                    "outlook": "Household demand improves.",
                    "confirmation_to_watch": ["Retail sales"],
                },
                {
                    "scenario_type": "downside",
                    "title": "Activity weakens",
                    "outlook": "Output loses momentum.",
                    "confirmation_to_watch": ["Vacancies"],
                },
            ],
        },
        "what_to_watch": [
            {
                "indicator": "CPI Services Inflation",
                "development_to_watch": "Whether inflation continues to ease.",
                "significance": "It indicates domestic price persistence.",
            },
            {
                "indicator": "Monthly GDP Index",
                "development_to_watch": "Whether output regains momentum.",
                "significance": "It summarizes broad activity.",
            },
            {
                "indicator": "UK Vacancies",
                "development_to_watch": "Whether labour demand weakens.",
                "significance": "It can lead changes in employment.",
            },
        ],
        "overall_assessment": {
            "assessment": "The economy was stable but uncertainty remained.",
            "confidence": "medium",
            "main_uncertainties": ["Data revisions", "Inflation persistence"],
        },
    }


def test_render_report_html_renders_sections_and_escapes_content():
    html = render_report_html(sample_report())

    assert "UK Monthly Economic Report" in html
    assert "Balanced Stability" in html
    assert "Gradual stabilization" in html
    assert "CPI Services Inflation" in html
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_export_report_writes_json_and_html(tmp_path):
    paths = export_report(
        sample_report(),
        output_directory=tmp_path,
        basename="test-report",
        formats=("json", "html"),
    )

    assert paths == {
        "json": tmp_path / "test-report.json",
        "html": tmp_path / "test-report.html",
    }
    assert json.loads(paths["json"].read_text())["reporting_period"] == ("2026-08-31")
    assert "Executive summary" in paths["html"].read_text()


def test_export_report_writes_long_pdf(tmp_path):
    pytest.importorskip("weasyprint")
    report = sample_report()
    long_text = "Economic conditions require careful interpretation. " * 40

    for section in report["current_conditions"].values():
        section["assessment"] = long_text
        section["key_qualification"] = long_text

    for scenario in report["conditional_outlook"]["scenarios"]:
        scenario["outlook"] = long_text

    paths = export_report(
        report,
        output_directory=tmp_path,
        basename="long-report",
        formats=("pdf",),
    )

    assert paths == {"pdf": tmp_path / "long-report.pdf"}
    assert paths["pdf"].read_bytes().startswith(b"%PDF")


def test_export_report_rejects_unknown_format(tmp_path):
    with pytest.raises(ValueError, match="Unsupported report format"):
        export_report(
            sample_report(),
            output_directory=tmp_path,
            formats=("markdown",),
        )
