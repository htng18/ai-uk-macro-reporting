from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from ai_uk_macro_reporting.common import Confidence


class HeadlineAssessment(BaseModel):
    """Summarise the headline output-and-demand conclusion."""

    signal: str
    confidence: Confidence


class OutputAssessment(BaseModel):
    """Assess the direction and strength of economic output."""

    assessment: str
    composition_and_breadth: str
    momentum_and_trend: str
    key_qualification: str


class HouseholdDemandAssessment(BaseModel):
    """Assess household demand conditions."""

    assessment: str
    retail_activity: str
    credit_signal: str
    key_qualification: str


class HousingDemandAssessment(BaseModel):
    """Assess housing demand conditions."""

    assessment: str
    approvals_and_lending: str
    key_qualification: str


class BusinessDemandAssessment(BaseModel):
    """Assess business demand conditions."""

    assessment: str
    key_qualification: str


class OutputDemandRelationship(BaseModel):
    """Describe a relationship among output-and-demand indicators."""

    classification: Literal[
        "reinforcing",
        "partially_reinforcing",
        "divergent",
        "mixed",
        "insufficient_evidence",
    ]
    assessment: str
    economic_interpretation: str


class Insight(BaseModel):
    """Capture a supported insight about output and demand."""

    insight: str
    supporting_evidence: list[str]
    confidence: Confidence


class AlternativeInterpretation(BaseModel):
    """Present an alternative interpretation of output-and-demand evidence."""

    issue: str
    interpretation: str
    importance: Confidence


class Hypothesis(BaseModel):
    """Express a testable hypothesis about output-and-demand dynamics."""

    hypothesis: str
    status: Literal[
        "most_consistent",
        "plausible_alternative",
        "lower_support",
    ]
    supporting_evidence: list[str]
    qualifying_evidence: list[str]
    mechanism: str
    discriminator: list[str]
    confidence: Confidence


class OverallConfidence(BaseModel):
    """State overall confidence in the output-and-demand assessment."""

    level: Confidence
    rationale: str


class OutputDemandReport(BaseModel):
    """Represent the complete thematic output-and-demand analysis."""

    headline_assessment: HeadlineAssessment
    output: OutputAssessment
    household_demand: HouseholdDemandAssessment
    housing_demand: HousingDemandAssessment
    business_demand: BusinessDemandAssessment
    output_demand_relationship: OutputDemandRelationship
    key_insights: Annotated[list[Insight], Field(min_length=2, max_length=5)]
    hypotheses: Annotated[list[Hypothesis], Field(max_length=3)]
    contradictions_and_alternative_interpretations: list[AlternativeInterpretation]
    timing_and_data_limitations: list[str]
    questions_for_cross_theme_synthesis: list[str]
    overall_confidence: OverallConfidence

    @model_validator(mode="after")
    def require_hypotheses_for_uncertain_evidence(self):
        weak_or_uncertain = (
            self.overall_confidence.level == "low"
            or self.output_demand_relationship.classification
            in {"mixed", "insufficient_evidence"}
        )
        if weak_or_uncertain and len(self.hypotheses) < 2:
            raise ValueError(
                "At least two hypotheses are required under weak or mixed evidence."
            )
        return self


class OutputDemandResponse(BaseModel):
    """Wrap the output-and-demand report returned by structured model output."""

    output_and_demand_report: OutputDemandReport
