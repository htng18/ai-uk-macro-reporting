from ai_uk_macro_reporting.graph import build_monthly_report


def test_monthly_report_graph_contains_expected_nodes_and_edges():
    graph = build_monthly_report().get_graph()

    assert set(graph.nodes) == {
        "__start__",
        "__end__",
        "compute_metrics",
        "compare_monthly_state",
        "analyse_output_and_demand",
        "analyse_inflation",
        "analyse_labour_market",
        "analyse_monetary_policy",
        "compute_confidence_profile",
        "cross_theme_synthesis",
        "counter_analysis",
        "outlook_scenarios",
        "compose_monthly_report",
        "evaluate_report",
        "revise_report",
    }

    edges = {(edge.source, edge.target, edge.conditional) for edge in graph.edges}
    assert edges == {
        ("__start__", "compute_metrics", False),
        ("compute_metrics", "compare_monthly_state", False),
        ("compute_metrics", "analyse_output_and_demand", False),
        ("compute_metrics", "analyse_inflation", False),
        ("compute_metrics", "analyse_labour_market", False),
        ("compute_metrics", "analyse_monetary_policy", False),
        ("compare_monthly_state", "compute_confidence_profile", False),
        ("analyse_output_and_demand", "compute_confidence_profile", False),
        ("analyse_inflation", "compute_confidence_profile", False),
        ("analyse_labour_market", "compute_confidence_profile", False),
        ("analyse_monetary_policy", "compute_confidence_profile", False),
        ("compute_confidence_profile", "cross_theme_synthesis", False),
        ("cross_theme_synthesis", "counter_analysis", False),
        ("counter_analysis", "outlook_scenarios", False),
        ("outlook_scenarios", "compose_monthly_report", False),
        ("compose_monthly_report", "evaluate_report", False),
        ("evaluate_report", "revise_report", True),
        ("evaluate_report", "__end__", True),
        ("revise_report", "evaluate_report", False),
    }
