import logging
from typing import Any

from ai_uk_macro_reporting.calculation.compare_metric import (
    calculate_confidence_metrics,
)
from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.explain_confidence_profile import (
    explain_confidence_profile_prompt,
)
from ai_uk_macro_reporting.report_context import serialize_prompt_data
from ai_uk_macro_reporting.schemas.explain_confidence_profile import (
    ConfidenceProfileExplanation,
)
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)

log = logging.getLogger(__name__)

analysis_llm = get_chat_model(ModelRole.ANALYSIS)
explain_confidence_profile_chain = (
    explain_confidence_profile_prompt
    | analysis_llm.with_structured_output(ConfidenceProfileExplanation)
)


def explain_confidence_profile(
    state: MonthlyReport,
    confidence_metrics: dict[str, Any],
) -> ConfidenceProfileExplanation:
    """Ask the analysis model to explain deterministic confidence metrics."""
    inputs = {
        "reporting_period": state.reporting_period,
        "overall_confidence_score": confidence_metrics["overall_confidence_score"],
        "overall_confidence": confidence_metrics["overall_confidence"],
        "theme_confidence_metrics": serialize_prompt_data(
            confidence_metrics["theme_confidence_metrics"]
        ),
        "monthly_change_analysis": serialize_prompt_data(state.monthly_change_analysis),
        "output_demand_report": serialize_prompt_data(state.output_and_demand_report),
        "inflation_report": serialize_prompt_data(state.inflation_report),
        "labour_market_report": serialize_prompt_data(state.labour_market_report),
        "monetary_policy_report": serialize_prompt_data(state.monetary_policy_report),
    }

    result = invoke_chat_model(
        explain_confidence_profile_chain,
        inputs,
        length_limit_message=LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        quota_message=LLM_MODEL_QUOTA_MESSAGE,
    )

    log.info("Explanation of confidence profile generated successfully.")
    return result


def compute_confidence_profile(
    state: MonthlyReport,
) -> dict[str, Any]:
    """Combine deterministic confidence scores with a narrative explanation."""
    confidence_metrics = calculate_confidence_metrics(state)

    confidence_explanation = explain_confidence_profile(
        state=state,
        confidence_metrics=confidence_metrics,
    )

    log.info("Confidence profile computed successfully.")
    return {
        "confidence_profile": {
            "metrics": confidence_metrics,
            "explanation": confidence_explanation.model_dump(mode="json"),
        }
    }
