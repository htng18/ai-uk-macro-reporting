from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from ai_uk_macro_reporting.common import Confidence

# ============================================================
# Headline assessment
# ============================================================


class HeadlineAssessment(BaseModel):
    """Summarise the headline labour-market conclusion."""

    signal: str
    confidence: Confidence


# ============================================================
# Employment conditions
# ============================================================


class EmploymentConditionsAssessment(BaseModel):
    """Assess current employment conditions."""

    assessment: str
    employment_vs_unemployment: str
    inactivity_assessment: str
    labour_utilisation: str
    key_qualification: str


# ============================================================
# Labour demand
# ============================================================


class LabourDemandAssessment(BaseModel):
    """Assess demand for labour and its recent direction."""

    assessment: str
    vacancy_signal: str
    demand_implication: str
    key_qualification: str


# ============================================================
# Wage pressure
# ============================================================


class WagePressureAssessment(BaseModel):
    """Assess the direction and persistence of wage pressures."""

    assessment: str
    regular_vs_total_pay: str
    momentum_and_persistence: str
    key_qualification: str


# ============================================================
# Labour expectations
# ============================================================


class LabourExpectationsAssessment(BaseModel):
    """Assess forward-looking labour-market expectations."""

    assessment: str
    wage_expectations: str
    employment_expectations: str
    expectations_relationship: str
    key_qualification: str


# ============================================================
# Theme-level breadth
# ============================================================


class LabourBreadthAssessment(BaseModel):
    """Assess how broadly labour-market signals are distributed."""

    classification: Literal[
        "broad_positive",
        "broad_negative",
        "broadly_stable",
        "mixed",
        "insufficient_evidence",
    ]

    assessment: str
    economic_interpretation: str


# ============================================================
# Overall labour-market relationship
# ============================================================


class LabourMarketRelationship(BaseModel):
    """Describe a relationship among labour-market indicators."""

    classification: Literal[
        "tight",
        "easing_tightness",
        "balanced",
        "increasing_slack",
        "mixed",
        "insufficient_evidence",
    ]

    assessment: str

    wage_pressure_assessment: str

    persistence_or_slack_assessment: str

    economic_interpretation: str


# ============================================================
# Key insights
# ============================================================


class Insight(BaseModel):
    """Capture a supported insight about labour-market conditions."""

    insight: str
    supporting_evidence: list[str]
    confidence: Confidence


KeyInsights = Annotated[
    list[Insight],
    Field(
        min_length=3,
        max_length=3,
    ),
]


# ============================================================
# Hypotheses
# ============================================================


class Hypothesis(BaseModel):
    """Express a testable hypothesis about labour-market dynamics."""

    hypothesis: str

    status: Literal[
        "most_consistent",
        "plausible_alternative",
    ]

    supporting_evidence: Annotated[
        list[str],
        Field(max_length=2),
    ]

    qualifying_evidence: Annotated[
        list[str],
        Field(max_length=2),
    ]

    mechanism: str

    discriminator: Annotated[
        list[str],
        Field(max_length=2),
    ]

    confidence: Confidence


Hypotheses = Annotated[
    list[Hypothesis],
    Field(max_length=2),
]


# ============================================================
# Contradictions / alternative interpretations
# ============================================================


class AlternativeInterpretation(BaseModel):
    """Present an alternative interpretation of labour-market evidence."""

    issue: str

    interpretation: str

    supporting_evidence: Annotated[
        list[str],
        Field(max_length=2),
    ]

    importance: Literal[
        "high",
        "medium",
        "low",
    ]


AlternativeInterpretations = Annotated[
    list[AlternativeInterpretation],
    Field(max_length=2),
]


# ============================================================
# Overall confidence
# ============================================================


class OverallConfidence(BaseModel):
    """State overall confidence in the labour-market assessment."""

    level: Confidence
    rationale: str


# ============================================================
# Final labour-market report
# ============================================================


class LabourMarketReport(BaseModel):
    """Represent the complete thematic labour-market analysis."""

    headline_assessment: HeadlineAssessment
    employment_conditions: EmploymentConditionsAssessment
    labour_demand: LabourDemandAssessment
    wage_pressure: WagePressureAssessment
    labour_expectations: LabourExpectationsAssessment
    theme_breadth: LabourBreadthAssessment
    labour_market_relationship: LabourMarketRelationship
    key_insights: KeyInsights
    hypotheses: Hypotheses
    contradictions_and_alternative_interpretations: AlternativeInterpretations
    timing_and_data_limitations: Annotated[
        list[str],
        Field(max_length=3),
    ]
    questions_for_cross_theme_synthesis: Annotated[
        list[str],
        Field(max_length=3),
    ]
    overall_confidence: OverallConfidence

    @model_validator(mode="after")
    def validate_hypotheses(self):
        if len(self.hypotheses) not in {0, 2}:
            raise ValueError("hypotheses must contain either 0 or exactly 2 hypotheses")

        return self


class LabourMarketReportResponse(BaseModel):
    """Wrap the labour-market report returned by structured model output."""

    labour_market_report: LabourMarketReport
