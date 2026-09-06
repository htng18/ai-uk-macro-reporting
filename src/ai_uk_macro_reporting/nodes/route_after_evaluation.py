from ai_uk_macro_reporting.common import MAX_REVISION_ITERATIONS
from ai_uk_macro_reporting.state import MonthlyReport


def route_after_evaluation(
    state: MonthlyReport,
) -> str:
    """End an acceptable report or route it through another bounded revision."""
    evaluation = state.report_evaluation
    verdict = evaluation["overall_evaluation"]["publication_verdict"]
    score = evaluation["overall_evaluation"]["score"]
    issues = evaluation["issues"]
    critical_issue_count = sum(issue["severity"] == "critical" for issue in issues)
    major_issue_count = sum(issue["severity"] == "major" for issue in issues)

    # --------------------------------------------
    # Pass
    # --------------------------------------------

    if (
        verdict == "pass"
        and score >= 9.0
        and critical_issue_count == 0
        and major_issue_count == 0
    ):
        return "end"

    # --------------------------------------------
    # Pass with minor edits
    # --------------------------------------------

    if (
        verdict == "pass_with_minor_edits"
        and score >= 8.5
        and critical_issue_count == 0
        and major_issue_count == 0
    ):
        return "end"

    # --------------------------------------------
    # Stop after maximum revisions
    # --------------------------------------------

    if state.revision_count >= MAX_REVISION_ITERATIONS:
        return "end"

    # --------------------------------------------
    # Otherwise revise
    # --------------------------------------------

    return "revise_report"
