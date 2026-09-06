import warnings

from ai_uk_macro_reporting.common import Confidence, CounterVerdict, MacroRegime
from ai_uk_macro_reporting.schemas.compose_monthly_report import (
    ExecutiveSummary,
    OverallAssessment,
    RisksToCentralInterpretation,
)
from ai_uk_macro_reporting.schemas.cross_theme import (
    CrossThemeConfidenceAssessment,
    HeadlineAssessment,
    OverallConfidence,
)


def test_authoritative_confidence_serializes_without_warnings():
    authoritative_confidence = Confidence("medium")
    headline = HeadlineAssessment(signal="Mixed", confidence="low")
    overall = OverallConfidence(level="low", rationale="Limited evidence")
    assessment = CrossThemeConfidenceAssessment(
        classification="low",
        assessment="Mixed evidence",
        main_support="Broad coverage",
        main_limitation="Timing differences",
    )

    headline.confidence = authoritative_confidence
    overall.level = authoritative_confidence
    assessment.classification = authoritative_confidence

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert headline.model_dump(mode="json")["confidence"] == "medium"
        assert overall.model_dump(mode="json")["level"] == "medium"
        assert assessment.model_dump(mode="json")["classification"] == "medium"


def test_authoritative_composition_enums_serialize_without_warnings():
    executive_summary = ExecutiveSummary(
        summary="Summary",
        macro_regime="soft_landing",
        confidence="low",
        confidence_explanation="Explanation",
        central_outlook="Outlook",
        main_qualification="Qualification",
    )
    risks = RisksToCentralInterpretation(
        counter_analysis_verdict="survives",
        assessment="Assessment",
        key_risks=[{"risk": "Risk", "significance": "Significance"}],
        strongest_counter_case="Counter case",
    )
    overall = OverallAssessment(
        assessment="Assessment",
        confidence="low",
        main_uncertainties=["Uncertainty"],
    )

    executive_summary.macro_regime = MacroRegime("mixed_transition")
    executive_summary.confidence = Confidence("medium")
    risks.counter_analysis_verdict = CounterVerdict("survives_with_qualifications")
    overall.confidence = Confidence("medium")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert executive_summary.model_dump(mode="json") == {
            "summary": "Summary",
            "macro_regime": "mixed_transition",
            "confidence": "medium",
            "confidence_explanation": "Explanation",
            "central_outlook": "Outlook",
            "main_qualification": "Qualification",
        }
        assert risks.model_dump(mode="json")["counter_analysis_verdict"] == (
            "survives_with_qualifications"
        )
        assert overall.model_dump(mode="json")["confidence"] == "medium"
