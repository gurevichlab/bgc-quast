from pathlib import Path

import pytest
from src.compare_to_ref_data import ReferenceBgc, Status
from src.genome_mining_result import Bgc, GenomeMiningResult
from src.reporting.metrics_calculators import (
    BasicMetricsCalculator,
    CompareToRefMetricsCalculator,
)
from src.reporting.report_config import (
    GroupingDimensionConfig,
    MetricConfig,
    ReportConfig,
)


@pytest.fixture
def basic_calculator():
    bgcs = [
        Bgc(
            bgc_id="bgc1",
            sequence_id="seq1",
            start=0,
            end=100,
            completeness="Complete",
            product_types=["NRP"],
        ),
        Bgc(
            bgc_id="bgc2",
            sequence_id="seq2",
            start=200,
            end=300,
            completeness="Incomplete",
            product_types=["PKS"],
        ),
        Bgc(
            bgc_id="bgc3",
            sequence_id="seq3",
            start=400,
            end=500,
            completeness="Complete",
            product_types=["Hybrid"],
        ),
    ]

    results = [
        GenomeMiningResult(
            input_file=Path("test_file_1"),
            input_file_label="label1",
            mining_tool="tool1",
            bgcs=bgcs,
        ),
    ]

    config = ReportConfig(
        metrics=[
            MetricConfig(name="total_bgc_count", display_name="Total BGC Count"),
            MetricConfig(name="mean_bgc_length", display_name="Mean BGC Length"),
        ],
        grouping_dimensions={
            "product_type": GroupingDimensionConfig(),
            "completeness": GroupingDimensionConfig(),
        },
        grouping_combinations=[["product_type", "completeness"]],
    )

    return BasicMetricsCalculator(results, config)


def test_calculate_metrics(basic_calculator):
    metrics = basic_calculator.calculate_metrics()

    assert len(metrics) == 18  # 2 metrics x 9 groups (1 + 2 + 3 + 3)

    # Check correctness of calculated metrics
    metric_names = {m.metric_name for m in metrics}
    assert "total_bgc_count" in metric_names
    assert "mean_bgc_length" in metric_names

    # Check values for ungrouped metrics
    ungrouped = [m for m in metrics if m.grouping == {}]
    assert len(ungrouped) == 2
    total_bgc_count_metric = next(
        m for m in ungrouped if m.metric_name == "total_bgc_count"
    )
    mean_bgc_length_metric = next(
        m for m in ungrouped if m.metric_name == "mean_bgc_length"
    )
    assert total_bgc_count_metric.value == 3
    assert mean_bgc_length_metric.value == pytest.approx((100 + 100 + 100) / 3)

    # Check grouped metrics for product_type and completeness
    nrp_complete = [
        m
        for m in metrics
        if m.grouping == {"product_type": "NRP", "completeness": "Complete"}
    ]
    assert len(nrp_complete) == 2
    assert any(
        m.metric_name == "total_bgc_count" and m.value == 1 for m in nrp_complete
    )
    assert any(
        m.metric_name == "mean_bgc_length" and m.value == 100 for m in nrp_complete
    )


def test_empty_bgcs():
    empty_results = [
        GenomeMiningResult(
            input_file=Path("empty_file"),
            input_file_label="label2",
            mining_tool="tool2",
            bgcs=[],
        ),
    ]

    config = ReportConfig(
        metrics=[
            MetricConfig(name="total_bgc_count", display_name="Total BGC Count"),
            MetricConfig(name="mean_bgc_length", display_name="Mean BGC Length"),
        ],
        grouping_dimensions={
            "product_type": GroupingDimensionConfig(),
            "completeness": GroupingDimensionConfig(),
        },
        grouping_combinations=[["product_type", "completeness"]],
    )

    calculator = BasicMetricsCalculator(empty_results, config)

    metrics = calculator.calculate_metrics()
    assert len(metrics) == 2
    assert metrics[0].metric_name == "total_bgc_count"
    assert metrics[0].value == 0
    assert metrics[0].grouping == {}
    assert metrics[1].metric_name == "mean_bgc_length"
    assert metrics[1].value == 0
    assert metrics[1].grouping == {}


def test_generate_grouping_combinations(basic_calculator):
    config = basic_calculator.config
    combinations = basic_calculator._generate_grouping_combinations(config)

    assert combinations == [
        [],
        ["product_type"],
        ["completeness"],
        ["product_type", "completeness"],
    ]


def test_group_bgcs(basic_calculator):
    bgcs = basic_calculator.results[0].bgcs
    grouping_funcs = {
        "product_type": lambda bgc: bgc.product_types[0]
        if bgc.product_types
        else "Unknown",
        "completeness": lambda bgc: bgc.completeness,
    }

    grouped = basic_calculator._group_bgcs(bgcs, grouping_funcs)

    assert len(grouped) == 3
    assert grouped[("NRP", "Complete")][0].bgc_id == "bgc1"
    assert grouped[("PKS", "Incomplete")][0].bgc_id == "bgc2"
    assert grouped[("Hybrid", "Complete")][0].bgc_id == "bgc3"


def test_calculate_all_metrics_for_bgcs(basic_calculator):
    bgcs = basic_calculator.results[0].bgcs
    input_file = basic_calculator.results[0].input_file
    mining_tool = basic_calculator.results[0].mining_tool
    metric_names = basic_calculator.metric_names
    grouping_dimensions = ["product_type", "completeness"]

    metrics = basic_calculator._calculate_all_metrics_for_bgcs(
        bgcs, input_file, mining_tool, metric_names, grouping_dimensions
    )

    assert len(metrics) == 6
    assert metrics[0].metric_name == "total_bgc_count"
    assert metrics[0].value == 1
    assert metrics[0].grouping == {"product_type": "NRP", "completeness": "Complete"}
    assert metrics[0].mining_tool == "tool1"


@pytest.fixture
def compare_to_ref_calculator():
    assembly_bgcs = []
    result = GenomeMiningResult(
        input_file=Path("test_file_1"),
        input_file_label="label1",
        mining_tool="tool1",
        bgcs=assembly_bgcs,
    )

    ref_bgcs = [
        ReferenceBgc(
            bgc_id="bgc1_ref",
            sequence_id="ref_seq1",
            start=0,
            end=100,
            completeness="Complete",
            product_types=["NRP"],
            status=Status.FULLY_RECOVERED,
            recovered_product_types=["NRP"],
        ),
        ReferenceBgc(
            bgc_id="bgc2_ref",
            sequence_id="ref_seq1",
            start=1000,
            end=1100,
            completeness="Complete",
            product_types=["PKS"],
            status=Status.MISSED,
            recovered_product_types=[],
        ),
        ReferenceBgc(
            bgc_id="bgc3_ref",
            sequence_id="ref_seq2",
            start=2000,
            end=2100,
            completeness="Incomplete",
            product_types=["Hybrid"],
            status=Status.PARTIALLY_RECOVERED,
            recovered_product_types=["Hybrid"],
        ),
    ]

    results_with_ref_bgcs = [(result, ref_bgcs)]

    config = ReportConfig(
        metrics=[
            MetricConfig(
                name="fully_recovered_bgcs_count",
                display_name="Fully Recovered BGCs",
            ),
            MetricConfig(name="recovery_rate", display_name="Recovery Rate"),
        ],
        grouping_dimensions={
            "completeness": GroupingDimensionConfig(),
            "product_type": GroupingDimensionConfig(),
        },
        grouping_combinations=[["completeness", "product_type"]],
    )

    return CompareToRefMetricsCalculator(results_with_ref_bgcs, config)


def test_compare_to_ref_calculate_metrics(compare_to_ref_calculator):
    metrics = compare_to_ref_calculator.calculate_metrics()

    assert len(metrics) == 18

    metric_names = {m.metric_name for m in metrics}
    assert "fully_recovered_bgcs_count" in metric_names
    assert "recovery_rate" in metric_names

    ungrouped = [m for m in metrics if m.grouping == {}]
    assert len(ungrouped) == 2
    fully_recovered_metric = next(
        m for m in ungrouped if m.metric_name == "fully_recovered_bgcs_count"
    )
    recovery_rate_metric = next(
        m for m in ungrouped if m.metric_name == "recovery_rate"
    )
    assert fully_recovered_metric.value == 1
    assert recovery_rate_metric.value == pytest.approx(2 / 3)

    incomplete_group = [
        m for m in metrics if m.grouping.get("completeness") == "Incomplete"
    ]
    assert len(incomplete_group) == 4
    assert any(
        m.metric_name == "fully_recovered_bgcs_count" and m.value == 0
        for m in incomplete_group
    )
    assert any(
        m.metric_name == "recovery_rate" and m.value == 1.0 for m in incomplete_group
    )

    complete_pks = [
        m
        for m in metrics
        if m.grouping.get("completeness") == "Complete"
        and m.grouping.get("product_type") == "PKS"
    ]
    assert len(complete_pks) == 2
    assert any(
        m.metric_name == "fully_recovered_bgcs_count" and m.value == 0
        for m in complete_pks
    )
    assert any(m.metric_name == "recovery_rate" and m.value == 0 for m in complete_pks)
