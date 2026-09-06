from typing import Annotated, Literal

from pydantic import BaseModel, Field

from ai_uk_macro_reporting.common import Confidence

# ============================================================
# Headline
# ============================================================


class HeadlineAssessment(BaseModel):
    """Summarise the headline inflation conclusion."""

    signal: str
    confidence: Confidence


# ============================================================
# Headline / underlying inflation
# ============================================================


class InflationAssessment(BaseModel):
    """Assess the direction and strength of inflation pressures."""

    assessment: str
    headline_vs_core: str
    momentum_and_persistence: str
    key_qualification: str


# ============================================================
# Inflation composition
# ============================================================


class CompositionAssessment(BaseModel):
    """Assess the composition and breadth of inflation pressures."""

    assessment: str
    services_vs_goods: str
    food_and_energy: str
    breadth: str
    key_qualification: str


# ============================================================
# Producer-price pipeline
# ============================================================


class PipelineAssessment(BaseModel):
    """Assess upstream price pressures in the inflation pipeline."""

    assessment: str
    input_vs_output: str
    pass_through_implication: str
    key_qualification: str


# ============================================================
# Inflation expectations
# ============================================================


class ExpectationsAssessment(BaseModel):
    """Assess the state of inflation expectations."""

    assessment: str
    near_vs_medium_term: str
    own_price_expectations: str
    key_qualification: str


# ============================================================
# Relationship across:
# current inflation -> pipeline -> expectations
# ============================================================


class InflationRelationship(BaseModel):
    """Describe a relationship among inflation indicators."""

    classification: Literal[
        "reinforcing",
        "partially_reinforcing",
        "divergent",
        "mixed",
        "insufficient_evidence",
    ]

    direction: Literal[
        "inflationary",
        "disinflationary",
        "neutral",
        "unclear",
    ]

    assessment: str
    persistence_assessment: str
    economic_interpretation: str


# ============================================================
# Key insights
# ============================================================


class Insight(BaseModel):
    """Capture a supported insight about inflation conditions."""

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
    """Express a testable hypothesis about inflation dynamics."""

    hypothesis: str

    status: Literal[
        "most_consistent",
        "plausible_alternative",
    ]

    supporting_evidence: list[str]
    qualifying_evidence: list[str]

    mechanism: str

    discriminator: list[str]

    confidence: Confidence


Hypotheses = Annotated[
    list[Hypothesis],
    Field(max_length=2),
]


# ============================================================
# Contradictions / alternative interpretations
# ============================================================


class AlternativeInterpretation(BaseModel):
    """Present an alternative interpretation of inflation evidence."""

    issue: str
    interpretation: str

    supporting_evidence: list[str]

    importance: Literal[
        "high",
        "medium",
        "low",
    ]


AlternativeInterpretations = Annotated[
    list[AlternativeInterpretation],
    Field(max_length=3),
]


# ============================================================
# Confidence
# ============================================================


class OverallConfidence(BaseModel):
    """State overall confidence in the inflation assessment."""

    level: Confidence
    rationale: str


# ============================================================
# Final inflation report
# ============================================================


class InflationReport(BaseModel):
    """Represent the complete thematic inflation analysis."""

    headline_assessment: HeadlineAssessment

    headline_underlying: InflationAssessment

    inflation_composition: CompositionAssessment

    pipeline_pressure: PipelineAssessment

    inflation_expectations: ExpectationsAssessment

    inflation_pressure_relationship: InflationRelationship

    key_insights: KeyInsights

    hypotheses: Hypotheses

    contradictions_and_alternative_interpretations: AlternativeInterpretations

    timing_and_data_limitations: list[str]

    questions_for_cross_theme_synthesis: list[str]

    overall_confidence: OverallConfidence


class InflationResponse(BaseModel):
    """Wrap the inflation report returned by structured model output."""

    inflation_report: InflationReport
