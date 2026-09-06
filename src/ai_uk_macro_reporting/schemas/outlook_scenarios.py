from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from ai_uk_macro_reporting.common import (
    Confidence,
    MacroRegime,
    ScenarioLikelihood,
    ScenarioType,
    ThemeName,
)

# ============================================================
# Headline
# ============================================================


class OutlookHeadline(BaseModel):
    """Summarise the conditional macroeconomic outlook."""

    outlook: str
    confidence: Confidence


# ============================================================
# Scenario configuration
# ============================================================


class ScenarioConfiguration(BaseModel):
    """Describe the macroeconomic configuration within a scenario."""

    regime: MacroRegime

    activity_and_demand: str
    labour_market: str
    inflation: str
    monetary_financial_conditions: str


# ============================================================
# Scenario trigger
# ============================================================


class ScenarioTrigger(BaseModel):
    """Identify a development that would increase a scenario's likelihood."""

    trigger: str

    themes: Annotated[
        list[ThemeName],
        Field(min_length=1, max_length=4),
    ]

    significance: str


ScenarioTriggers = Annotated[
    list[ScenarioTrigger],
    Field(min_length=2, max_length=3),
]


# ============================================================
# Scenario invalidator
# ============================================================


class ScenarioInvalidator(BaseModel):
    """Identify evidence that would invalidate a scenario."""

    condition: str

    themes: Annotated[
        list[ThemeName],
        Field(min_length=1, max_length=4),
    ]

    implication: str


ScenarioInvalidators = Annotated[
    list[ScenarioInvalidator],
    Field(min_length=1, max_length=2),
]


# ============================================================
# Macro scenario
# ============================================================


class MacroScenario(BaseModel):
    """Describe a coherent conditional macroeconomic scenario."""

    scenario_type: ScenarioType

    title: str

    likelihood: ScenarioLikelihood

    summary: str

    configuration: ScenarioConfiguration

    mechanism: str

    confirmation_triggers: ScenarioTriggers

    invalidating_evidence: ScenarioInvalidators

    confidence: Confidence


# ============================================================
# Early-warning indicators
# ============================================================


class EarlyWarningIndicator(BaseModel):
    """Identify an indicator that provides early evidence of a scenario."""

    indicator: str

    theme: ThemeName

    development_to_watch: str

    scenario_implication: str


EarlyWarningIndicators = Annotated[
    list[EarlyWarningIndicator],
    Field(min_length=3, max_length=5),
]


# ============================================================
# Key outlook conclusions
# ============================================================


class OutlookConclusion(BaseModel):
    """State the conclusion drawn from the scenario set."""

    conclusion: str

    themes: Annotated[
        list[ThemeName],
        Field(min_length=2, max_length=4),
    ]

    importance: Literal[
        "high",
        "medium",
        "low",
    ]


KeyOutlookConclusions = Annotated[
    list[OutlookConclusion],
    Field(min_length=3, max_length=3),
]


# ============================================================
# Overall confidence
# ============================================================


class OutlookConfidence(BaseModel):
    """State confidence in the conditional outlook."""

    level: Confidence

    rationale: str

    main_uncertainties: Annotated[
        list[str],
        Field(min_length=1, max_length=3),
    ]


# ============================================================
# Final OutlookScenariosReport
# ============================================================


class OutlookScenariosReport(BaseModel):
    """Represent the complete central, upside, and downside outlook."""

    headline: OutlookHeadline

    outlook_horizon: str

    scenarios: Annotated[
        list[MacroScenario],
        Field(min_length=3, max_length=3),
    ]

    early_warning_indicators: EarlyWarningIndicators

    key_outlook_conclusions: KeyOutlookConclusions

    overall_confidence: OutlookConfidence

    @model_validator(mode="after")
    def validate_scenarios(self):
        scenario_types = [scenario.scenario_type for scenario in self.scenarios]

        required_types = {
            "central",
            "upside",
            "downside",
        }

        # Exactly one of each scenario type
        if set(scenario_types) != required_types:
            raise ValueError(
                "scenarios must contain exactly one central, "
                "one upside, and one downside scenario"
            )

        # Prevent duplicates
        if len(scenario_types) != len(set(scenario_types)):
            raise ValueError("scenario types must be unique")

        central = next(
            scenario
            for scenario in self.scenarios
            if scenario.scenario_type == "central"
        )

        # Central must be primary
        if central.likelihood != "primary":
            raise ValueError("central scenario likelihood must be 'primary'")

        # Only central may be primary
        for scenario in self.scenarios:
            if scenario.scenario_type != "central" and scenario.likelihood == "primary":
                raise ValueError(
                    "only the central scenario may have likelihood='primary'"
                )

        return self


class OutlookScenariosReportResponse(BaseModel):
    """Wrap the outlook report returned by structured model output."""

    outlook_scenarios_report: OutlookScenariosReport
