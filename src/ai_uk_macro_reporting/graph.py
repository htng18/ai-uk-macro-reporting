"""Construct the LangGraph workflow for monthly macroeconomic reports."""

from langgraph.graph import END, START, StateGraph

from ai_uk_macro_reporting.nodes.analyse_inflation import analyse_inflation
from ai_uk_macro_reporting.nodes.analyse_labour_market import analyse_labour_market
from ai_uk_macro_reporting.nodes.analyse_monetary_policy import analyse_monetary_policy
from ai_uk_macro_reporting.nodes.analyse_output_and_demand import (
    analyse_output_and_demand,
)
from ai_uk_macro_reporting.nodes.compare_monthly import compare_monthly_state
from ai_uk_macro_reporting.nodes.compose_monthly_report import compose_monthly_report
from ai_uk_macro_reporting.nodes.compute_confidence_profile import (
    compute_confidence_profile,
)
from ai_uk_macro_reporting.nodes.compute_metrics import compute_metrics
from ai_uk_macro_reporting.nodes.counter_analysis import counter_analysis
from ai_uk_macro_reporting.nodes.cross_theme_synthesis import cross_theme_synthesis
from ai_uk_macro_reporting.nodes.evaluate_report import evaluate_report
from ai_uk_macro_reporting.nodes.outlook_scenarios import outlook_scenarios
from ai_uk_macro_reporting.nodes.revise_report import revise_report
from ai_uk_macro_reporting.nodes.route_after_evaluation import route_after_evaluation
from ai_uk_macro_reporting.state import MonthlyReport

PARALLEL_ANALYSIS_NODES = (
    "compare_monthly_state",
    "analyse_output_and_demand",
    "analyse_inflation",
    "analyse_labour_market",
    "analyse_monetary_policy",
)


def build_monthly_report():
    """Compile the report workflow, including its bounded revision loop."""
    graph_builder = StateGraph(MonthlyReport)

    node_functions = {
        "compute_metrics": compute_metrics,
        "compare_monthly_state": compare_monthly_state,
        "analyse_output_and_demand": analyse_output_and_demand,
        "analyse_inflation": analyse_inflation,
        "analyse_labour_market": analyse_labour_market,
        "analyse_monetary_policy": analyse_monetary_policy,
        "compute_confidence_profile": compute_confidence_profile,
        "cross_theme_synthesis": cross_theme_synthesis,
        "counter_analysis": counter_analysis,
        "outlook_scenarios": outlook_scenarios,
        "compose_monthly_report": compose_monthly_report,
        "evaluate_report": evaluate_report,
        "revise_report": revise_report,
    }
    for node_name, node_function in node_functions.items():
        graph_builder.add_node(node_name, node_function)

    graph_builder.add_edge(START, "compute_metrics")
    for analysis_node in PARALLEL_ANALYSIS_NODES:
        graph_builder.add_edge("compute_metrics", analysis_node)

    # LangGraph treats the list as a barrier: confidence is computed only after
    # the comparison and all four thematic analyses have completed.
    graph_builder.add_edge(
        list(PARALLEL_ANALYSIS_NODES),
        "compute_confidence_profile",
    )

    sequential_edges = (
        ("compute_confidence_profile", "cross_theme_synthesis"),
        ("cross_theme_synthesis", "counter_analysis"),
        ("counter_analysis", "outlook_scenarios"),
        ("outlook_scenarios", "compose_monthly_report"),
        ("compose_monthly_report", "evaluate_report"),
        ("revise_report", "evaluate_report"),
    )
    for source_node, target_node in sequential_edges:
        graph_builder.add_edge(source_node, target_node)

    graph_builder.add_conditional_edges(
        "evaluate_report",
        route_after_evaluation,
        {
            "revise_report": "revise_report",
            "end": END,
        },
    )

    return graph_builder.compile()
