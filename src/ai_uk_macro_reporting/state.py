import datetime as dt

from pydantic import BaseModel, Field

from ai_uk_macro_reporting.schemas.compose_monthly_report import ComposedMonthlyReport
from ai_uk_macro_reporting.schemas.counter_analysis import CounterAnalysisReport
from ai_uk_macro_reporting.schemas.cross_theme import CrossThemeReport
from ai_uk_macro_reporting.schemas.inflation import InflationReport
from ai_uk_macro_reporting.schemas.labour_market import LabourMarketReport
from ai_uk_macro_reporting.schemas.monetary_policy import MonetaryPolicyReport
from ai_uk_macro_reporting.schemas.outlook_scenarios import OutlookScenariosReport
from ai_uk_macro_reporting.schemas.output_and_demand import OutputDemandReport


def current_utc_date() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


class MonthlyReport(BaseModel):
    """State accumulated while building a monthly report."""

    rows: list[dict] = Field(default_factory=list)
    reporting_period: dt.date = Field(default_factory=current_utc_date)
    metrics: dict = Field(default_factory=dict)
    previous_metrics: dict = Field(default_factory=dict)
    previous_reporting_period: str | None = None
    monthly_change_analysis: dict = Field(default_factory=dict)
    confidence_profile: dict = Field(default_factory=dict)
    output_and_demand_report: OutputDemandReport | None = None
    inflation_report: InflationReport | None = None
    labour_market_report: LabourMarketReport | None = None
    monetary_policy_report: MonetaryPolicyReport | None = None
    cross_theme_report: CrossThemeReport | None = None
    counter_analysis_report: CounterAnalysisReport | None = None
    outlook_scenarios_report: OutlookScenariosReport | None = None
    compose_monthly_report: ComposedMonthlyReport | None = None
    prose_leakage_issues: list[dict] = Field(default_factory=list)
    prose_style_warnings: list[dict] = Field(default_factory=list)
    report_evaluation: dict = Field(default_factory=dict)
    revision_count: int = 0
