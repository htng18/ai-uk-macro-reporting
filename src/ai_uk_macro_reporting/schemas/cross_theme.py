from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from ai_uk_macro_reporting.common import Confidence, ThemeName

# ============================================================
# Headline
# ============================================================


class HeadlineAssessment(BaseModel):
    """Summarise the headline cross-theme conclusion."""

    signal: str
    confidence: Confidence


# ============================================================
# Overall macro regime
# ============================================================


class MacroRegimeAssessment(BaseModel):
    """Classify and explain the overall macroeconomic regime."""

    classification: Literal[
        "resilient_disinflation",
        "soft_landing",
        "broad_cooling",
        "demand_reacceleration",
        "inflationary_reacceleration",
        "weak_growth_sticky_inflation",
        "stagflationary_pressure",
        "balanced_stability",
        "mixed_transition",
        "insufficient_evidence",
    ]

    assessment: str

    supporting_themes: Annotated[
        list[ThemeName],
        Field(min_length=2, max_length=4),
    ]

    key_qualification: str


# ============================================================
# Cross-theme relationships
# ============================================================


class CrossThemeRelationship(BaseModel):
    """Describe a relationship between macroeconomic themes."""

    themes: Annotated[
        list[ThemeName],
        Field(min_length=2, max_length=2),
    ]

    classification: Literal[
        "reinforcing",
        "partially_reinforcing",
        "divergent",
        "neutral",
        "unclear",
    ]

    assessment: str

    economic_interpretation: str

    confidence: Confidence


CrossThemeRelationships = Annotated[
    list[CrossThemeRelationship],
    Field(
        min_length=1,
        max_length=5,
    ),
]


# ============================================================
# Key insights
# ============================================================


class CrossThemeInsight(BaseModel):
    """Capture an insight that emerges across multiple themes."""

    insight: str

    themes: Annotated[
        list[ThemeName],
        Field(min_length=2, max_length=4),
    ]

    supporting_evidence: Annotated[
        list[str],
        Field(max_length=3),
    ]

    confidence: Confidence


KeyInsights = Annotated[
    list[CrossThemeInsight],
    Field(
        min_length=3,
        max_length=3,
    ),
]


# ============================================================
# Cross-theme hypotheses
# ============================================================


class CrossThemeHypothesis(BaseModel):
    """Express a testable hypothesis spanning multiple themes."""

    hypothesis: str

    status: Literal[
        "most_consistent",
        "plausible_alternative",
    ]

    themes: Annotated[
        list[ThemeName],
        Field(min_length=2, max_length=4),
    ]

    supporting_evidence: Annotated[
        list[str],
        Field(max_length=3),
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


CrossThemeHypotheses = Annotated[
    list[CrossThemeHypothesis],
    Field(max_length=2),
]


# ============================================================
# Cross-theme tensions / contradictions
# ============================================================


class CrossThemeTension(BaseModel):
    """Describe evidence or conclusions that remain in tension."""

    themes: Annotated[
        list[ThemeName],
        Field(min_length=2, max_length=4),
    ]

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


CrossThemeTensions = Annotated[
    list[CrossThemeTension],
    Field(max_length=3),
]


# ============================================================
# Overall confidence
# ============================================================


class OverallConfidence(BaseModel):
    """State overall confidence in the cross-theme synthesis."""

    level: Confidence
    rationale: str


# ============================================================
# Authoritative confidence-profile interpretation
# ============================================================


class CrossThemeConfidenceAssessment(BaseModel):
    """Explain the evidence supporting cross-theme confidence."""

    classification: Confidence

    assessment: Annotated[
        str,
        Field(
            max_length=800,
            description=(
                "How the deterministic confidence profile qualifies the "
                "cross-theme interpretation without recalculating confidence."
            ),
        ),
    ]

    main_support: Annotated[
        str,
        Field(max_length=400),
    ]

    main_limitation: Annotated[
        str,
        Field(max_length=400),
    ]


# ============================================================
# Final cross-theme report
# ============================================================


class CrossThemeReport(BaseModel):
    """Represent the complete synthesis across macroeconomic themes."""

    headline_assessment: HeadlineAssessment

    overall_macro_regime: MacroRegimeAssessment

    cross_theme_relationships: CrossThemeRelationships

    key_insights: KeyInsights

    hypotheses: CrossThemeHypotheses

    cross_theme_tensions: CrossThemeTensions

    questions_for_counter_analysis: Annotated[
        list[str],
        Field(max_length=3),
    ]

    overall_confidence: OverallConfidence

    confidence_assessment: CrossThemeConfidenceAssessment

    @model_validator(mode="after")
    def validate_hypotheses(self):
        if len(self.hypotheses) not in {0, 2}:
            raise ValueError("hypotheses must contain either 0 or exactly 2 hypotheses")

        return self


class CrossThemeReportResponse(BaseModel):
    """Wrap the cross-theme report returned by structured model output."""

    cross_theme_report: CrossThemeReport
