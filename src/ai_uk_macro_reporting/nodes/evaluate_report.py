import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.evaluate_report import evaluate_report_prompt
from ai_uk_macro_reporting.report_context import (
    build_evaluation_inputs,
    get_authoritative_metadata,
)
from ai_uk_macro_reporting.report_safeguards import (
    validate_evaluation_consistency,
)
from ai_uk_macro_reporting.schemas.evaluation import MonthlyReportEvaluationResponse
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)

log = logging.getLogger(__name__)

editorial_llm = get_chat_model(ModelRole.EDITORIAL)
evaluate_report_chain = evaluate_report_prompt | (
    editorial_llm.with_structured_output(MonthlyReportEvaluationResponse)
)


def evaluate_report(
    state: MonthlyReport,
) -> dict[str, Any]:
    """Evaluate the composed report against authoritative evidence."""

    metadata = get_authoritative_metadata(state)

    evaluation_inputs = build_evaluation_inputs(
        state,
        metadata,
    )

    # --------------------------------------------------
    # Run evaluator
    # --------------------------------------------------

    result = invoke_chat_model(
        evaluate_report_chain,
        evaluation_inputs,
        length_limit_message=(LLM_MODEL_LENGTH_LIMIT_MESSAGE),
        quota_message=(LLM_MODEL_QUOTA_MESSAGE),
    )

    evaluation = result.evaluate_report

    evaluation_data = evaluation.model_dump(mode="json")
    evaluation_data["reporting_period"] = state.reporting_period.isoformat()

    # --------------------------------------------------
    # Defensive validation
    # --------------------------------------------------

    validate_evaluation_consistency(evaluation_data)

    log.info("Evaluation of report completed successfully.")
    log.info(
        "Evaluated score: %s",
        evaluation_data["overall_evaluation"]["score"],
    )
    return {"report_evaluation": (evaluation_data)}
