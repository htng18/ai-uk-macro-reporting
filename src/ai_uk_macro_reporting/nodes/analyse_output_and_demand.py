import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.output_and_demand import output_and_demand_prompt
from ai_uk_macro_reporting.report_context import serialize_prompt_data
from ai_uk_macro_reporting.schemas.output_and_demand import OutputDemandResponse
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)

log = logging.getLogger(__name__)

analysis_llm = get_chat_model(ModelRole.ANALYSIS)
output_and_demand_chain = output_and_demand_prompt | (
    analysis_llm.with_structured_output(OutputDemandResponse)
)


def analyse_output_and_demand(state: MonthlyReport) -> dict[str, Any]:
    """Generate and validate the output-and-demand report section."""
    result = invoke_chat_model(
        output_and_demand_chain,
        {
            "reporting_period": state.reporting_period,
            "output_demand_metrics": serialize_prompt_data(
                state.metrics.get("output_demand", {})
            ),
        },
        length_limit_message=LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        quota_message=LLM_MODEL_QUOTA_MESSAGE,
    )
    log.info("Analysis of output-and-demand completed successfully.")
    return {
        "output_and_demand_report": (
            result.output_and_demand_report.model_dump(mode="json")
        )
    }
