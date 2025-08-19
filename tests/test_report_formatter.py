"""Tests for the report_formatter module."""

import pandas as pd
import pytest
from src.reporting.report_config import (
    GroupingDimensionConfig,
    MetricConfig,
    ReportConfig,
)
from src.reporting.report_data import ReportData, RunningMode
from src.reporting.report_formatter import DataFrameTableBuilder, ReportFormatter


@pytest.fixture
def simple_config() -> ReportConfig:
    """A simple report configuration for testing."""
    return ReportConfig(
        metrics=[
            MetricConfig(name="metric1", display_name="Metric 1"),
            MetricConfig(name="metric2", display_name="Metric 2"),
        ],
        grouping_dimensions={},
        grouping_combinations=[],
    )


@pytest.fixture
def simple_data() -> ReportData:
    """Simple report data for testing."""
    df = pd.DataFrame(
        {
            "metric_name": ["metric1", "metric2", "metric1", "metric2"],
            "value": [10, 20, 15, 25],
            "file_label": ["file1", "file1", "file2", "file2"],
            "mining_tool": ["tool1", "tool1", "tool2", "tool2"],
        }
    )
    return ReportData(metrics_df=df, running_mode=RunningMode.UNKNOWN)


@pytest.fixture
def grouped_config() -> ReportConfig:
    """A report configuration with grouping for testing."""
    return ReportConfig(
        metrics=[
            MetricConfig(name="metric1", display_name="Metric 1"),
        ],
        grouping_dimensions={
            "type": GroupingDimensionConfig(order=["A", "B"]),
        },
        grouping_combinations=[],
    )


@pytest.fixture
def grouped_data() -> ReportData:
    """Grouped report data for testing."""
    df = pd.DataFrame(
        {
            "metric_name": ["metric1", "metric1", "metric1", "metric1"],
            "value": [100, 200, 150, 250],
            "file_label": ["file1", "file1", "file2", "file2"],
            "mining_tool": ["tool1", "tool1", "tool2", "tool2"],
            "type": ["A", "B", "A", "B"],
        }
    )
    # Add total rows
    total_df = df.groupby(
        ["metric_name", "file_label", "mining_tool"], as_index=False
    )["value"].sum()
    total_df["type"] = pd.NA

    metrics_df = pd.concat([df, total_df], ignore_index=True)
    return ReportData(metrics_df=metrics_df, running_mode=RunningMode.UNKNOWN)


class TestDataFrameTableBuilder:
    """Tests for the DataFrameTableBuilder class."""

    def test_build_pivot_table_simple(self, simple_config, simple_data):
        """Test building a simple pivot table without grouping."""
        builder = DataFrameTableBuilder(simple_config)
        pivot_table = builder.build_pivot_table(simple_data)

        assert pivot_table.shape == (2, 2)
        assert list(pivot_table.columns) == [("file1", "tool1"), ("file2", "tool2")]
        assert "Metric 1 (total)" in pivot_table.index
        assert "Metric 2 (total)" in pivot_table.index
        assert pivot_table.loc["Metric 1 (total)", ("file1", "tool1")] == 10
        assert pivot_table.loc["Metric 2 (total)", ("file2", "tool2")] == 25

    def test_build_pivot_table_with_grouping(self, grouped_config, grouped_data):
        """Test building a pivot table with grouping."""
        builder = DataFrameTableBuilder(grouped_config)
        pivot_table = builder.build_pivot_table(grouped_data)

        assert pivot_table.shape == (3, 2)
        assert "Metric 1 (total)" in pivot_table.index
        assert "Metric 1 (A)" in pivot_table.index
        assert "Metric 1 (B)" in pivot_table.index

        # Check sorting
        expected_index = ["Metric 1 (total)", "Metric 1 (A)", "Metric 1 (B)"]
        assert pivot_table.index.tolist() == expected_index

        # Check values
        assert pivot_table.loc["Metric 1 (A)", ("file1", "tool1")] == 100
        assert pivot_table.loc["Metric 1 (B)", ("file2", "tool2")] == 250
        assert pivot_table.loc["Metric 1 (total)", ("file1", "tool1")] == 300  # 100 + 200


class TestReportFormatter:
    """Tests for the ReportFormatter class."""

    @pytest.fixture
    def formatter(self, simple_config) -> ReportFormatter:
        """A ReportFormatter instance for testing."""
        return ReportFormatter(simple_config)

    def test_write_txt(self, formatter, simple_data, tmp_path):
        """Test writing a report to a text file."""
        output_file = tmp_path / "report.txt"
        formatter.write_txt(simple_data, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "Metric 1 (total)" in content
        assert "file1" in content
        assert "10" in content

    def test_write_html(self, formatter, simple_data, tmp_path):
        """Test writing a report to an HTML file."""
        output_file = tmp_path / "report.html"
        formatter.write_html(simple_data, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "<h1>BGC-QUAST Report</h1>" in content
        assert "<th>Metric 1 (total)</th>" in content
        assert "<td>10</td>" in content

    def test_write_tsv(self, formatter, simple_data, tmp_path):
        """Test writing a report to a TSV file."""
        output_file = tmp_path / "report.tsv"
        formatter.write_tsv(simple_data, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "Metric 1 (total)\t10\t15" in content
        assert "Metric 2 (total)\t20\t25" in content
