from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ai_uk_macro_reporting.common import Confidence, ThemeName


class ThemeConfidenceExplanation(BaseModel):
    """Explain the evidence supporting confidence in one theme."""

    theme: ThemeName

    confidence: Confidence

    explanation: str = Field(
        max_length=700,
        description=(
            "Why confidence in this theme's existing classification "
            "is high, medium or low. Must not reclassify the theme."
        ),
    )

    main_support: str = Field(
        max_length=400,
        description=(
            "The strongest reason supporting confidence in the "
            "theme's current classification."
        ),
    )

    main_limitation: str = Field(
        max_length=400,
        description=(
            "The most important factor limiting confidence in the "
            "theme's current classification."
        ),
    )


class HistoricalRelationshipAssessment(BaseModel):
    """Assess whether historical relationships support current confidence."""

    relationship: Literal[
        "output_labour",
        "labour_inflation",
        "output_inflation",
        "monetary_output",
        "monetary_inflation",
    ]

    assessment: str = Field(
        max_length=500,
        description=(
            "Interpretation of the supplied historical correlation, "
            "concordance and stability metrics. Must not imply causality."
        ),
    )

    evidence_quality: Confidence = Field(
        description=(
            "Qualitative strength of historical relationship evidence, "
            "not a new macroeconomic classification."
        )
    )


class ConfidenceProfileExplanation(BaseModel):
    """Explain the report-wide confidence profile in economic terms."""

    overall_confidence: Confidence = Field(
        description=(
            "Must exactly match the deterministic overall confidence "
            "classification supplied to the model."
        )
    )

    overall_explanation: str = Field(
        max_length=1200,
        description=(
            "Concise explanation of why the deterministic overall "
            "confidence level is appropriate."
        ),
    )

    strongest_confidence_sources: list[str] = Field(
        min_length=1,
        max_length=4,
        description=("Most important factors increasing confidence."),
    )

    main_confidence_limitations: list[str] = Field(
        min_length=1,
        max_length=4,
        description=("Most important factors preventing a higher confidence level."),
    )

    theme_explanations: list[ThemeConfidenceExplanation] = Field(
        min_length=4,
        max_length=4,
        description=(
            "Exactly one confidence explanation for each of the four "
            "macroeconomic themes."
        ),
    )

    historical_relationships: list[HistoricalRelationshipAssessment] = Field(
        max_length=5,
        description=(
            "Interpretation of available historical cross-theme relationship metrics."
        ),
    )

    timing_and_freshness_qualification: str = Field(
        max_length=700,
        description=("How data freshness and timing alignment affect confidence."),
    )

    signal_stability_assessment: str = Field(
        max_length=700,
        description=(
            "How persistence, recent changes, reversals and breadth "
            "changes affect confidence."
        ),
    )

    evidence_that_would_increase_confidence: list[str] = Field(
        min_length=1,
        max_length=4,
        description=(
            "Observable evidence that would strengthen confidence in "
            "the current interpretation. Must not be forecasts."
        ),
    )

    evidence_that_would_reduce_confidence: list[str] = Field(
        min_length=1,
        max_length=4,
        description=(
            "Observable evidence that would weaken confidence in "
            "the current interpretation. Must not be forecasts."
        ),
    )

    @model_validator(mode="after")
    def validate_themes(self):
        expected = {
            "output_demand",
            "inflation",
            "labour_market",
            "monetary_policy",
        }

        actual = {item.theme for item in self.theme_explanations}

        if actual != expected:
            raise ValueError(
                "theme_explanations must contain exactly one entry "
                "for each of output_demand, inflation, "
                "labour_market and monetary_policy."
            )

        return self
