from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from ai_uk_macro_reporting.common import (
    EvaluationDimensionName,
    PublicationVerdict,
    Severity,
)

# ============================================================
# Dimension scoring
# ============================================================


class DimensionEvaluation(BaseModel):
    """Record the result for one report-quality dimension."""

    dimension: EvaluationDimensionName

    score: Annotated[
        float,
        Field(ge=0.0, le=10.0),
    ]

    assessment: Annotated[
        str,
        Field(max_length=700),
    ]


DimensionEvaluations = Annotated[
    list[DimensionEvaluation],
    Field(min_length=14, max_length=14),
]


# ============================================================
# Evaluation issue
# ============================================================


class EvaluationIssue(BaseModel):
    """Describe a specific issue found during report evaluation."""

    severity: Severity

    category: EvaluationDimensionName

    section: Annotated[
        str,
        Field(max_length=120),
    ]

    problematic_text: Annotated[
        str | None,
        Field(default=None, max_length=400),
    ]

    issue: Annotated[
        str,
        Field(max_length=600),
    ]

    evidence_conflict: Annotated[
        str,
        Field(max_length=600),
    ]

    required_correction: Annotated[
        str,
        Field(max_length=600),
    ]


EvaluationIssues = Annotated[
    list[EvaluationIssue],
    Field(max_length=15),
]


# ============================================================
# Fidelity summary
# ============================================================


class ClassificationFidelity(BaseModel):
    """Audit whether the report preserves authoritative classifications."""

    macro_regime_correct: bool
    counter_verdict_correct: bool
    output_direction_correct: bool
    inflation_direction_correct: bool
    labour_classification_correct: bool
    monetary_classification_correct: bool
    confidence_classification_correct: bool

    assessment: Annotated[
        str,
        Field(max_length=700),
    ]


# ============================================================
# Numerical / evidence audit
# ============================================================


class EvidenceAudit(BaseModel):
    """Audit numerical claims and their supporting evidence."""

    numerical_claims_checked: int = Field(ge=0)

    numerical_errors_found: int = Field(ge=0)

    unsupported_claims_found: int = Field(ge=0)

    assessment: Annotated[
        str,
        Field(max_length=700),
    ]


# ============================================================
# Semantic consistency audit
# ============================================================


class SemanticConsistencyAudit(BaseModel):
    """Audit semantic consistency across the report's conclusions."""

    theme_prose_consistent: bool

    cross_theme_consistent: bool

    counter_analysis_consistent: bool

    scenarios_consistent: bool

    current_vs_outlook_separated: bool

    assessment: Annotated[
        str,
        Field(max_length=700),
    ]


# ============================================================
# Causality audit
# ============================================================


class CausalDisciplineAudit(BaseModel):
    """Audit the discipline of causal and transmission claims."""

    unsupported_causal_claims: Annotated[
        list[str],
        Field(max_length=5),
    ]

    transmission_overclaims: Annotated[
        list[str],
        Field(max_length=5),
    ]

    assessment: Annotated[
        str,
        Field(max_length=700),
    ]


# ============================================================
# Editorial audit
# ============================================================


class EditorialAudit(BaseModel):
    """Audit completeness, clarity, repetition, and style."""

    truncation_detected: bool

    material_repetition_detected: bool

    style_appropriate: bool

    length_appropriate: bool

    assessment: Annotated[
        str,
        Field(max_length=700),
    ]


# ============================================================
# Revision instruction
# ============================================================


class RevisionInstruction(BaseModel):
    """Specify a bounded correction for a report issue."""

    priority: Literal[
        "required",
        "recommended",
        "optional",
    ]

    section: Annotated[
        str,
        Field(max_length=120),
    ]

    instruction: Annotated[
        str,
        Field(max_length=600),
    ]

    reason: Annotated[
        str,
        Field(max_length=400),
    ]


RevisionInstructions = Annotated[
    list[RevisionInstruction],
    Field(max_length=10),
]


# ============================================================
# Overall evaluation
# ============================================================


class OverallEvaluation(BaseModel):
    """Summarise report quality and publication readiness."""

    score: Annotated[
        float,
        Field(ge=0.0, le=10.0),
    ]

    publication_verdict: PublicationVerdict

    summary: Annotated[
        str,
        Field(max_length=1000),
    ]

    strongest_aspect: Annotated[
        str,
        Field(max_length=400),
    ]

    main_weakness: Annotated[
        str | None,
        Field(default=None, max_length=400),
    ]


# ============================================================
# Final evaluation report
# ============================================================


class MonthlyReportEvaluation(BaseModel):
    """Represent the complete quality evaluation of a monthly report."""

    reporting_period: str

    classification_fidelity: ClassificationFidelity

    evidence_audit: EvidenceAudit

    semantic_consistency: SemanticConsistencyAudit

    causal_discipline: CausalDisciplineAudit

    editorial_audit: EditorialAudit

    dimension_scores: DimensionEvaluations

    issues: EvaluationIssues

    revision_instructions: RevisionInstructions

    overall_evaluation: OverallEvaluation

    # --------------------------------------------------------
    # Deterministic issue counts
    # --------------------------------------------------------

    @property
    def critical_issue_count(self) -> int:
        return sum(issue.severity == "critical" for issue in self.issues)

    @property
    def major_issue_count(self) -> int:
        return sum(issue.severity == "major" for issue in self.issues)

    @property
    def minor_issue_count(self) -> int:
        return sum(issue.severity == "minor" for issue in self.issues)

    # --------------------------------------------------------
    # Cross-field validation
    # --------------------------------------------------------

    @model_validator(mode="after")
    def validate_evaluation(self):
        # -----------------------------------------------
        # Exactly one score for every evaluation dimension
        # -----------------------------------------------

        dimensions = [item.dimension for item in self.dimension_scores]

        if len(dimensions) != len(set(dimensions)):
            raise ValueError("dimension_scores contains duplicate dimensions")

        required_dimensions = {
            "classification_fidelity",
            "numerical_evidence_fidelity",
            "theme_semantic_fidelity",
            "cross_theme_consistency",
            "counter_analysis_integration",
            "outlook_scenario_discipline",
            "causal_transmission_discipline",
            "uncertainty_confidence_calibration",
            "timing_frequency_alignment",
            "internal_consistency",
            "completeness_truncation",
            "repetition_editorial_quality",
            "analytical_depth_reader_accessibility",
            "length_style",
        }

        if set(dimensions) != required_dimensions:
            raise ValueError(
                "dimension_scores must contain exactly "
                "the required evaluation dimensions"
            )

        # -----------------------------------------------
        # Critical issues cannot receive passing verdict
        # -----------------------------------------------

        if (
            self.critical_issue_count > 0
            and self.overall_evaluation.publication_verdict
            in {
                "pass",
                "pass_with_minor_edits",
            }
        ):
            raise ValueError("A report with a critical issue cannot pass")

        # -----------------------------------------------
        # Critical issue => score <= 7.9
        # -----------------------------------------------

        if self.critical_issue_count > 0 and self.overall_evaluation.score > 7.9:
            raise ValueError(
                "A report with critical issues cannot "
                "receive an overall score above 7.9"
            )

        # -----------------------------------------------
        # PASS means no critical / major issues
        # -----------------------------------------------

        if self.overall_evaluation.publication_verdict == "pass" and (
            self.critical_issue_count > 0
            or self.major_issue_count > 0
            or self.minor_issue_count > 0
        ):
            raise ValueError("pass requires no reported issues")

        # -----------------------------------------------
        # PASS WITH MINOR EDITS means no critical/major
        # -----------------------------------------------

        if self.overall_evaluation.publication_verdict == "pass_with_minor_edits" and (
            self.critical_issue_count > 0 or self.major_issue_count > 0
        ):
            raise ValueError(
                "pass_with_minor_edits cannot contain critical or major issues"
            )

        # -----------------------------------------------
        # Classification mismatch should be critical
        # -----------------------------------------------

        fidelity = self.classification_fidelity

        classification_error = not all(
            [
                fidelity.macro_regime_correct,
                fidelity.counter_verdict_correct,
                fidelity.output_direction_correct,
                fidelity.inflation_direction_correct,
                fidelity.labour_classification_correct,
                fidelity.monetary_classification_correct,
                fidelity.confidence_classification_correct,
            ]
        )

        if classification_error:
            has_classification_critical_issue = any(
                issue.severity == "critical"
                and issue.category == "classification_fidelity"
                for issue in self.issues
            )

            if not has_classification_critical_issue:
                raise ValueError(
                    "A classification fidelity failure must "
                    "produce a critical classification issue"
                )

        # -----------------------------------------------
        # Truncation should be critical
        # -----------------------------------------------

        if self.editorial_audit.truncation_detected:
            has_truncation_critical_issue = any(
                issue.severity == "critical"
                and issue.category == "completeness_truncation"
                for issue in self.issues
            )

            if not has_truncation_critical_issue:
                raise ValueError(
                    "Detected truncation must produce a critical truncation issue"
                )

        return self


class MonthlyReportEvaluationResponse(BaseModel):
    """Wrap the report evaluation returned by structured model output."""

    evaluate_report: MonthlyReportEvaluation
