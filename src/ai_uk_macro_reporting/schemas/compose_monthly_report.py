from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from ai_uk_macro_reporting.common import Confidence, CounterVerdict, MacroRegime

# ============================================================
# Executive summary
# ============================================================


class ExecutiveSummary(BaseModel):
    """Summarise the report's central findings, outlook, and confidence."""

    summary: str = Field(
        max_length=2200,
        description=(
            "Approximately 180–250 words. Summarise current conditions, "
            "identify the main drivers, explain the most important "
            "cross-theme insight, and state the main qualification."
        ),
    )

    macro_regime: MacroRegime

    confidence: Confidence

    confidence_explanation: str = Field(
        max_length=500,
        description=(
            "Explain in plain economic language why the authoritative "
            "confidence level is appropriate. Describe the underlying "
            "breadth, persistence, confirmation and timing of the evidence "
            "without mentioning internal scoring dimensions or numerical "
            "confidence metrics."
        ),
    )

    central_outlook: str = Field(
        max_length=700,
    )

    main_qualification: str = Field(
        max_length=500,
    )


# ============================================================
# Current thematic conditions
# ============================================================


class OutputDemandFinalSection(BaseModel):
    """Present the final output-and-demand assessment."""

    direction: Literal[
        "positive",
        "neutral",
        "negative",
        "insufficient_evidence",
    ]
    assessment: str
    key_qualification: str


class InflationFinalSection(BaseModel):
    """Present the final inflation assessment."""

    direction: Literal[
        "inflationary",
        "disinflationary",
        "neutral",
        "unclear",
    ]
    assessment: str
    key_qualification: str


class LabourFinalSection(BaseModel):
    """Present the final labour-market assessment."""

    classification: Literal[
        "tight",
        "easing_tightness",
        "balanced",
        "increasing_slack",
        "mixed",
        "insufficient_evidence",
    ]
    assessment: str
    key_qualification: str


class MonetaryFinalSection(BaseModel):
    """Present the final monetary and financial conditions assessment."""

    classification: Literal[
        "tightening",
        "easing",
        "broadly_stable",
        "mixed",
        "insufficient_evidence",
    ]
    assessment: str
    key_qualification: str


class CurrentConditions(BaseModel):
    """Collect the report's four current-condition assessments."""

    output_and_demand: OutputDemandFinalSection
    inflation: InflationFinalSection
    labour_market: LabourFinalSection
    monetary_and_financial_conditions: MonetaryFinalSection


# ============================================================
# Cross-theme assessment
# ============================================================


class CrossThemeAssessment(BaseModel):
    """Explain relationships and conclusions spanning macroeconomic themes."""

    assessment: Annotated[
        str,
        Field(max_length=2400),
    ]
    key_relationships: Annotated[
        list[str],
        Field(min_length=2, max_length=5),
    ]
    regime_interpretation: Annotated[
        str,
        Field(max_length=900),
    ]


# ============================================================
# Risks to central interpretation
# ============================================================


class CentralInterpretationRisk(BaseModel):
    """Describe a risk to the report's central interpretation."""

    risk: Annotated[
        str,
        Field(max_length=400),
    ]
    significance: Annotated[
        str,
        Field(max_length=500),
    ]


class RisksToCentralInterpretation(BaseModel):
    """Summarise counter-analysis and risks to the central interpretation."""

    counter_analysis_verdict: CounterVerdict

    assessment: Annotated[
        str,
        Field(max_length=1400),
    ]
    key_risks: Annotated[
        list[CentralInterpretationRisk],
        Field(min_length=1, max_length=3),
    ]
    strongest_counter_case: Annotated[
        str,
        Field(max_length=700),
    ]


# ============================================================
# Concise outlook scenarios
# ============================================================


class FinalScenarioSummary(BaseModel):
    """Provide a concise scenario for the final report."""

    scenario_type: Literal[
        "central",
        "upside",
        "downside",
    ]

    title: Annotated[
        str,
        Field(max_length=120),
    ]

    outlook: Annotated[
        str,
        Field(max_length=800),
    ]

    confirmation_to_watch: Annotated[
        list[str],
        Field(min_length=1, max_length=2),
    ]


class ConditionalOutlook(BaseModel):
    """Collect the report's scenarios over a stated horizon."""

    horizon: str

    scenarios: Annotated[
        list[FinalScenarioSummary],
        Field(min_length=3, max_length=3),
    ]


# ============================================================
# What to watch
# ============================================================


class WatchIndicator(BaseModel):
    """Identify an indicator and the development to monitor."""

    indicator: str

    development_to_watch: Annotated[
        str,
        Field(max_length=250),
    ]
    significance: Annotated[
        str,
        Field(max_length=300),
    ]


WatchList = Annotated[
    list[WatchIndicator],
    Field(min_length=3, max_length=5),
]


# ============================================================
# Overall assessment
# ============================================================


class OverallAssessment(BaseModel):
    """State the report's overall conclusion and main uncertainties."""

    assessment: Annotated[
        str,
        Field(max_length=1000),
    ]

    confidence: Confidence

    main_uncertainties: Annotated[
        list[str],
        Field(min_length=1, max_length=3),
    ]


# ============================================================
# Final monthly report
# ============================================================


class ComposedMonthlyReport(BaseModel):
    """Represent the complete public-facing monthly macroeconomic report."""

    reporting_period: str
    executive_summary: ExecutiveSummary
    current_conditions: CurrentConditions
    cross_theme_assessment: CrossThemeAssessment
    risks_to_central_interpretation: RisksToCentralInterpretation
    conditional_outlook: ConditionalOutlook
    what_to_watch: WatchList
    overall_assessment: OverallAssessment

    @model_validator(mode="after")
    def validate_report(self):
        # -----------------------------------------------
        # Exactly one central/upside/downside scenario
        # -----------------------------------------------
        scenario_types = [
            scenario.scenario_type for scenario in self.conditional_outlook.scenarios
        ]

        required = {
            "central",
            "upside",
            "downside",
        }

        if set(scenario_types) != required:
            raise ValueError(
                "conditional_outlook.scenarios must contain exactly "
                "one central, one upside, and one downside scenario"
            )

        if len(scenario_types) != len(set(scenario_types)):
            raise ValueError("conditional outlook scenario types must be unique")

        return self


class ComposedMonthlyReportResponse(BaseModel):
    """Wrap the composed report returned by structured model output."""

    compose_monthly_report: ComposedMonthlyReport
