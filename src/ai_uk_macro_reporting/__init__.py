from ai_uk_macro_reporting.state import MonthlyReport

__all__ = [
    "MonthlyReport",
    "build_monthly_report",
]


def build_monthly_report():
    """Build the report graph without importing model clients eagerly."""
    from ai_uk_macro_reporting.graph import build_monthly_report as build_graph

    return build_graph()
