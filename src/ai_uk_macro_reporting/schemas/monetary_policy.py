from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from ai_uk_macro_reporting.common import Confidence

# ============================================================
# Headline assessment
# ============================================================


class HeadlineAssessment(BaseModel):
    """Summarise the headline monetary-policy conclusion."""

    signal: str
    confidence: Confidence


# ============================================================
# Policy conditions
# Bank Rate + SONIA
# ============================================================


class PolicyConditionsAssessment(BaseModel):
    """Assess the current stance of monetary policy."""

    assessment: str
    bank_rate_assessment: str
    sonia_assessment: str
    policy_rate_relationship: str
    key_qualification: str


# ============================================================
# Market rates
# 5Y + 10Y gilt yields
# ============================================================


class MarketRatesAssessment(BaseModel):
    """Assess market interest rates and financing conditions."""

    assessment: str
    five_vs_ten_year: str
    momentum_and_trend: str
    market_rate_implication: str
    key_qualification: str


# ============================================================
# Money / credit conditions
# M4 + M4 lending
# ============================================================


class MoneyCreditAssessment(BaseModel):
    """Assess developments in money and credit."""

    assessment: str
    money_growth_assessment: str
    lending_growth_assessment: str
    money_credit_relationship: str
    key_qualification: str


# ============================================================
# Theme-level breadth
# ============================================================


class MonetaryPolicyBreadthAssessment(BaseModel):
    """Assess the breadth of monetary and financial signals."""

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
# Overall monetary-policy / financial-conditions relationship
# ============================================================


class MonetaryPolicyRelationship(BaseModel):
    """Describe a relationship among monetary and financial indicators."""

    classification: Literal[
        "tightening",
        "easing",
        "broadly_stable",
        "mixed",
        "insufficient_evidence",
    ]

    assessment: str

    policy_market_relationship: str

    transmission_assessment: str

    economic_interpretation: str


# ============================================================
# Key insights
# ============================================================


class Insight(BaseModel):
    """Capture a supported insight about monetary conditions."""

    insight: str

    supporting_evidence: Annotated[
        list[str],
        Field(max_length=2),
    ]

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
    """Express a testable hypothesis about monetary transmission."""

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
    """Present an alternative interpretation of monetary evidence."""

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
    """State overall confidence in the monetary-policy assessment."""

    level: Confidence
    rationale: str


# ============================================================
# Final monetary-policy thematic report
# ============================================================


class MonetaryPolicyReport(BaseModel):
    """Represent the complete thematic monetary-policy analysis."""

    headline_assessment: HeadlineAssessment

    policy_conditions: PolicyConditionsAssessment

    market_rates: MarketRatesAssessment

    money_credit_conditions: MoneyCreditAssessment

    theme_breadth: MonetaryPolicyBreadthAssessment

    monetary_policy_relationship: MonetaryPolicyRelationship

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


class MonetaryPolicyReportResponse(BaseModel):
    """Wrap the monetary-policy report returned by structured model output."""

    monetary_policy_report: MonetaryPolicyReport
