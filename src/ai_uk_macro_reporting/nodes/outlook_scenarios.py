import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.outlook_scenarios import outlook_scenarios_prompt
from ai_uk_macro_reporting.report_context import serialize_prompt_data
from ai_uk_macro_reporting.schemas.outlook_scenarios import (
    OutlookScenariosReportResponse,
)
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)

log = logging.getLogger(__name__)

synthesis_llm = get_chat_model(ModelRole.SYNTHESIS)
outlook_scenarios_chain = outlook_scenarios_prompt | (
    synthesis_llm.with_structured_output(OutlookScenariosReportResponse)
)


def outlook_scenarios(state: MonthlyReport) -> dict[str, Any]:
    """Generate central, upside, and downside scenarios from prior analyses."""
    outlook_horizon = "next 3 to 6 months"

    response = invoke_chat_model(
        outlook_scenarios_chain,
        {
            "reporting_period": state.reporting_period,
            "outlook_horizon": outlook_horizon,
            "output_demand_report": serialize_prompt_data(
                state.output_and_demand_report
            ),
            "inflation_report": serialize_prompt_data(state.inflation_report),
            "labour_market_report": serialize_prompt_data(state.labour_market_report),
            "monetary_policy_report": serialize_prompt_data(
                state.monetary_policy_report
            ),
            "cross_theme_report": serialize_prompt_data(state.cross_theme_report),
            "counter_analysis_report": serialize_prompt_data(
                state.counter_analysis_report
            ),
            "confidence_profile": serialize_prompt_data(state.confidence_profile),
        },
        length_limit_message=LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        quota_message=LLM_MODEL_QUOTA_MESSAGE,
    )
    log.info("Outlook scenarios report generated successfully.")

    return {
        "outlook_scenarios_report": (
            response.outlook_scenarios_report.model_dump(mode="json")
        )
    }
