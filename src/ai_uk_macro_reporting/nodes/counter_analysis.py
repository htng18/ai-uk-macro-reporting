import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
    Confidence,
)
from ai_uk_macro_reporting.prompts.counter_analysis import counter_analysis_prompt
from ai_uk_macro_reporting.report_context import serialize_prompt_data
from ai_uk_macro_reporting.schemas.counter_analysis import CounterAnalysisReportResponse
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)

log = logging.getLogger(__name__)

synthesis_llm = get_chat_model(ModelRole.SYNTHESIS)
counter_analysis_chain = counter_analysis_prompt | (
    synthesis_llm.with_structured_output(CounterAnalysisReportResponse)
)


def counter_analysis(state: MonthlyReport) -> dict[str, Any]:
    """Generate and validate the counter-analysis report."""

    cross_theme_report = state.cross_theme_report

    central_regime = cross_theme_report.overall_macro_regime.classification
    central_thesis = cross_theme_report.overall_macro_regime.assessment
    central_confidence = Confidence(
        state.confidence_profile["metrics"]["overall_confidence"]
    )

    result = invoke_chat_model(
        counter_analysis_chain,
        {
            "reporting_period": state.reporting_period,
            "central_regime": central_regime,
            "central_thesis": central_thesis,
            "central_confidence": central_confidence,
            "output_demand_report": serialize_prompt_data(
                state.output_and_demand_report
            ),
            "inflation_report": serialize_prompt_data(state.inflation_report),
            "labour_market_report": serialize_prompt_data(state.labour_market_report),
            "monetary_policy_report": serialize_prompt_data(
                state.monetary_policy_report
            ),
            "cross_theme_report": serialize_prompt_data(cross_theme_report),
            "confidence_profile": serialize_prompt_data(state.confidence_profile),
        },
        length_limit_message=LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        quota_message=LLM_MODEL_QUOTA_MESSAGE,
    )

    report = result.counter_analysis_report

    # --------------------------------------------------
    # Deterministic consistency check
    # --------------------------------------------------
    if report.central_thesis_under_review.regime != central_regime:
        raise ValueError(
            "Counter-analysis reviewed the wrong regime: "
            f"expected {central_regime!r}, "
            f"got {report.central_thesis_under_review.regime!r}"
        )

    report.central_thesis_under_review.confidence = central_confidence
    report.overall_confidence.level = central_confidence

    log.info(
        "Counter-analysis report generated with overall confidence: %s",
        report.overall_confidence.level,
    )
    return {"counter_analysis_report": report.model_dump(mode="json")}
