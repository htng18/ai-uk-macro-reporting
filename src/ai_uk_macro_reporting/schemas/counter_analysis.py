from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from ai_uk_macro_reporting.common import Confidence, MacroRegime, ThemeName

# ============================================================
# Central thesis being challenged
# ============================================================


class CentralThesisAssessment(BaseModel):
    """Restate and assess the central macroeconomic thesis."""

    regime: MacroRegime
    thesis: str
    confidence: Confidence


# ============================================================
# Major challenges
# ============================================================


class CounterChallenge(BaseModel):
    """Describe evidence that challenges the central thesis."""

    challenge: str

    challenge_type: Literal[
        "contradiction",
        "missing_confirmation",
        "weak_evidence",
        "narrow_breadth",
        "timing_mismatch",
        "causal_uncertainty",
        "transmission_uncertainty",
    ]

    themes: Annotated[
        list[ThemeName],
        Field(min_length=1, max_length=4),
    ]

    supporting_evidence: Annotated[
        list[str],
        Field(min_length=1, max_length=3),
    ]

    interpretation: str

    materiality: Literal[
        "high",
        "medium",
        "low",
    ]

    confidence: Confidence


MajorChallenges = Annotated[
    list[CounterChallenge],
    Field(max_length=3),
]


# ============================================================
# Alternative mechanisms
# ============================================================


class AlternativeMechanism(BaseModel):
    """Describe an alternative mechanism that could explain the evidence."""

    issue: str

    themes: Annotated[
        list[ThemeName],
        Field(min_length=1, max_length=4),
    ]

    mechanism: str

    supporting_evidence: Annotated[
        list[str],
        Field(max_length=2),
    ]

    limitation: str


AlternativeMechanisms = Annotated[
    list[AlternativeMechanism],
    Field(max_length=3),
]


# ============================================================
# Strongest counter-case
# ============================================================


class StrongestCounterCase(BaseModel):
    """Present the strongest coherent case against the central thesis."""

    counter_case: str

    themes: Annotated[
        list[ThemeName],
        Field(min_length=2, max_length=4),
    ]

    supporting_evidence: Annotated[
        list[str],
        Field(min_length=2, max_length=3),
    ]

    qualifying_evidence: Annotated[
        list[str],
        Field(max_length=2),
    ]

    mechanism: str

    alternative_regime: MacroRegime

    confidence: Confidence


# ============================================================
# Falsification conditions
# ============================================================


class FalsificationCondition(BaseModel):
    """Define evidence that would falsify the central thesis."""

    condition: str

    themes: Annotated[
        list[ThemeName],
        Field(min_length=1, max_length=4),
    ]

    implication: str


FalsificationConditions = Annotated[
    list[FalsificationCondition],
    Field(min_length=1, max_length=3),
]


# ============================================================
# Final verdict
# ============================================================


class CounterAnalysisVerdict(BaseModel):
    """State the conclusion reached after testing the central thesis."""

    classification: Literal[
        "survives",
        "survives_with_qualifications",
        "materially_weakened",
        "should_be_replaced",
        "insufficient_evidence",
    ]

    assessment: str

    strongest_reason: str

    confidence: Confidence


# ============================================================
# Outlook implications
# ============================================================


class OutlookImplication(BaseModel):
    """Explain how counter-analysis affects the conditional outlook."""

    implication: str

    importance: Literal[
        "high",
        "medium",
        "low",
    ]


OutlookImplications = Annotated[
    list[OutlookImplication],
    Field(max_length=3),
]


# ============================================================
# Overall confidence
# ============================================================


class OverallConfidence(BaseModel):
    """State overall confidence in the counter-analysis."""

    level: Confidence

    rationale: str


# ============================================================
# Final CounterAnalysisReport
# ============================================================


class CounterAnalysisReport(BaseModel):
    """Collect challenges and alternatives to the central macro thesis."""

    central_thesis_under_review: CentralThesisAssessment

    major_challenges: MajorChallenges

    alternative_mechanisms: AlternativeMechanisms

    strongest_counter_case: StrongestCounterCase

    falsification_conditions: FalsificationConditions

    verdict: CounterAnalysisVerdict

    implications_for_outlook: OutlookImplications

    overall_confidence: OverallConfidence

    @model_validator(mode="after")
    def validate_counter_analysis(self):
        # The strongest counter-case must genuinely be cross-theme.
        if len(self.strongest_counter_case.themes) < 2:
            raise ValueError("strongest_counter_case must integrate at least 2 themes")

        return self


class CounterAnalysisReportResponse(BaseModel):
    """Wrap the counter-analysis returned by structured model output."""

    counter_analysis_report: CounterAnalysisReport
