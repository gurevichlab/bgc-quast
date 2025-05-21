from pathlib import Path
from typing import Any, Sequence

from src.genome_mining_result import GenomeMiningResult
from src.metrics import MetricsEngine
from src.report import BasicReport


def generate_metrics(
    result: GenomeMiningResult,
) -> dict[str, dict[tuple, dict[str, Any]]]:
    """
    Generate metrics for the given genome mining result.

    Args:
        result (GenomeMiningResult): The genome mining result to analyze.

    Returns:
        dict[str, dict[tuple, dict[str, Any]]]: A dictionary containing the computed metrics.
        The keys are metric names, and the values are dictionaries where keys are tuples of
        grouping key values and values are dictionaries of metrics.

    The grouping keys and metrics are defined in the MetricsEngine class.
    """

    engine = MetricsEngine(result.bgcs)
    return {
        "total": engine.compute([]),  # no grouping
        "by_type": engine.compute(["product_type"]),
        "by_completeness": engine.compute(["completeness"]),
        "by_type_completeness": engine.compute(["product_type", "completeness"]),
    }


def generate_metrics_for_all(
    genome_mining_results: Sequence[GenomeMiningResult],
) -> dict[Path, dict[str, dict[tuple, dict[str, Any]]]]:
    """
    Generate metrics for all genome mining results.

    Args:
        genome_mining_results (Sequence[GenomeMiningResult]): List of genome mining results to analyze.

    Returns:
        basic_metrics: A dictionary containing the computed metrics for each genome mining result.
    """
    basic_metrics = {}
    for result in genome_mining_results:
        basic_metrics[result.input_file] = generate_metrics(result)
    return basic_metrics


def generate_basic_report(
    genome_mining_results: Sequence[GenomeMiningResult],
) -> BasicReport:
    """
    Generate a basic report for the given genome mining results.

    Args:
        genome_mining_results (Sequence[GenomeMiningResult]): List of genome mining results to analyze.

    Returns:
        BasicReport: A report containing the basic metrics.
    """
    basic_report = BasicReport(generate_metrics_for_all(genome_mining_results))

    return basic_report
