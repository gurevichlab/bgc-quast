from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from src.config import Config
from src.genome_mining_result import Bgc, GenomeMiningResult, QuastResult
from src.reporting.report_builder import ReportBuilder
from src.reporting.report_config import ReportConfig
from src.reporting.report_data import MetricValue, ReportData, RunningMode


@pytest.fixture
def mock_config():
    """Provides a mock Config object."""
    config = MagicMock(spec=Config)
    config.allowed_gap_for_fragmented_recovery = 100
    return config


@pytest.fixture
def mock_report_config():
    """Provides a mock ReportConfig object."""
    return MagicMock(
        spec=ReportConfig, grouping_dimensions={}, grouping_combinations=[]
    )


@pytest.fixture
def mock_config_manager(mock_report_config):
    """
    Provides a mock ReportConfigManager that returns a valid config.
    """
    config_manager = MagicMock()
    config_manager.get_config.return_value = mock_report_config
    return config_manager


@pytest.fixture
def mock_basic_metrics():
    """Provides a list of mock MetricValue objects for testing."""
    return [
        MetricValue(
            file_path=Path("sample1.fasta"),
            mining_tool="antiSMASH",
            metric_name="total_bgc_count",
            value=5,
            grouping={},
        ),
        MetricValue(
            file_path=Path("sample2.fasta"),
            mining_tool="antiSMASH",
            metric_name="total_bgc_count",
            value=10,
            grouping={},
        ),
    ]


@pytest.fixture
def mock_compare_to_ref_metrics():
    """Provides a list of mock MetricValue objects for the compare to ref mode."""
    return [
        MetricValue(
            file_path=Path("sample1.fasta"),
            mining_tool="antiSMASH",
            metric_name="completeness_metric",
            value=0.8,
            grouping={},
        ),
    ]


@pytest.fixture
def mock_genome_mining_results():
    """Provides a list of mock GenomeMiningResult objects."""
    result1 = MagicMock(spec=GenomeMiningResult)
    result1.input_file = Path("sample1.fasta")
    result1.input_file_label = "sample1"
    result1.mining_tool = "tool1"
    result1.bgcs = [MagicMock(spec=Bgc) for _ in range(5)]

    result2 = MagicMock(spec=GenomeMiningResult)
    result2.input_file = Path("sample2.fasta")
    result2.input_file_label = "sample2"
    result2.mining_tool = "tool2"
    result2.bgcs = [MagicMock(spec=Bgc) for _ in range(10)]

    return [result1, result2]


@pytest.fixture
def mock_quast_results():
    """Provides a list of mock QuastResult objects."""
    return [
        MagicMock(spec=QuastResult, input_file_label="sample1"),
        MagicMock(spec=QuastResult, input_file_label="sample2"),
    ]


@pytest.fixture
def mock_reference_result():
    """Provides a mock GenomeMiningResult for a reference genome."""
    return MagicMock(spec=GenomeMiningResult, input_file_label="reference")


# --- Tests for ReportBuilder class ---


def test_init(mock_config_manager):
    """Test that the ReportBuilder can be initialized correctly."""
    builder = ReportBuilder(mock_config_manager)
    assert builder.report_config_manager == mock_config_manager


def test_build_report_basic_mode(
    mock_config_manager, mock_genome_mining_results, mock_basic_metrics, mock_config
):
    """
    Test the 'basic_report' running mode.

    This test verifies that the ReportBuilder correctly:
    - Instantiates and uses BasicMetricsCalculator.
    - Creates a DataFrame with the correct structure and content.
    - Sets the correct running mode and metadata.
    """
    # Arrange: Mock the dependencies using patch as a context manager
    with (
        patch(
            "src.reporting.report_builder.BasicMetricsCalculator"
        ) as MockBasicCalculator,
        patch(
            "src.reporting.report_builder.create_dataframe_from_metrics"
        ) as MockDataFrame,
        patch(
            "src.reporting.report_builder.input_utils.get_file_label_from_path"
        ) as MockGetLabel,
    ):
        MockBasicCalculator.return_value.calculate_metrics.return_value = (
            mock_basic_metrics
        )
        MockDataFrame.return_value = pd.DataFrame(
            {
                "file_path": [Path("sample1.fasta"), Path("sample2.fasta")],
                "metric_name": ["total_bgc_count", "total_bgc_count"],
                "value": ["5", "10"],
            }
        )
        MockGetLabel.side_effect = ["sample1", "sample2"]

        builder = ReportBuilder(mock_config_manager)

        report_data = builder.build_report(
            config=mock_config,
            results=mock_genome_mining_results,
            running_mode=RunningMode.UNKNOWN,
        )

        assert isinstance(report_data, ReportData)
        assert report_data.running_mode == RunningMode.UNKNOWN
        assert report_data.metadata["results_count"] == 2

        df = report_data.metrics_df
        assert "file_label" in df.columns
        assert "file_path" not in df.columns
        assert list(df["file_label"]) == ["sample1", "sample2"]


def test_build_report_compare_to_reference_mode(
    mock_config_manager,
    mock_genome_mining_results,
    mock_quast_results,
    mock_reference_result,
    mock_basic_metrics,
    mock_compare_to_ref_metrics,
    mock_config,
):
    """
    Test the 'compare_to_reference' running mode.

    This test verifies that the ReportBuilder correctly:
    - Instantiates and uses both calculators.
    - Calls the reference coverage analysis function.
    - Extends the metrics list with the results from both calculators.
    - Updates the metadata with reference BGCs.
    """
    # Arrange: Mock the dependencies
    with (
        patch(
            "src.reporting.report_builder.BasicMetricsCalculator"
        ) as MockBasicCalculator,
        patch(
            "src.reporting.report_builder.CompareToRefMetricsCalculator"
        ) as MockCompareCalculator,
        patch(
            "src.reporting.report_builder.compare_to_ref_analyzer.compute_coverage"
        ) as MockComputeCoverage,
        patch(
            "src.reporting.report_builder.create_dataframe_from_metrics"
        ) as MockDataFrame,
        patch(
            "src.reporting.report_builder.input_utils.get_file_label_from_path"
        ) as MockGetLabel,
    ):
        MockBasicCalculator.return_value.calculate_metrics.return_value = (
            mock_basic_metrics
        )
        MockCompareCalculator.return_value.calculate_metrics.return_value = (
            mock_compare_to_ref_metrics
        )
        MockComputeCoverage.return_value = {"ref_bgc_1": 0.9}

        # Mock the get_config call for the compare_to_reference mode
        mock_config_manager.get_config.side_effect = [
            MagicMock(spec=ReportConfig),  # for "basic_report"
            MagicMock(spec=ReportConfig),  # for "compare_to_reference"
        ]

        MockDataFrame.return_value = pd.DataFrame(
            {
                "file_path": [
                    Path("sample1.fasta"),
                    Path("sample2.fasta"),
                    Path("sample1.fasta"),
                ],
                "metric_name": [
                    "total_bgc_count",
                    "total_bgc_count",
                    "completeness_metric",
                ],
                "value": ["5", "10", "0.8"],
            }
        )
        MockGetLabel.side_effect = ["sample1", "sample2", "sample1"]

        builder = ReportBuilder(mock_config_manager)

        # Act: Call the method
        report_data = builder.build_report(
            config=mock_config,
            results=mock_genome_mining_results,
            running_mode=RunningMode.COMPARE_TO_REFERENCE,
            quast_results=mock_quast_results,
            reference_genome_mining_result=mock_reference_result,
        )

        # Assert: Check the results
        assert isinstance(report_data, ReportData)
        assert report_data.running_mode == RunningMode.COMPARE_TO_REFERENCE
        assert report_data.metadata["results_count"] == 2
        assert "reference_bgcs" in report_data.metadata
        assert report_data.metadata["reference_bgcs"] == {"ref_bgc_1": 0.9}

        df = report_data.metrics_df
        assert "file_label" in df.columns
        assert "file_path" not in df.columns
        assert len(df) == 3


def test_build_report_no_metrics_calculated(
    mock_config_manager, mock_genome_mining_results, mock_config
):
    """
    Test that a ValueError is raised when no metrics are calculated.
    """
    # Arrange: Mock the calculator to return an empty list
    with patch(
        "src.reporting.report_builder.BasicMetricsCalculator"
    ) as MockBasicCalculator:
        MockBasicCalculator.return_value.calculate_metrics.return_value = []
        builder = ReportBuilder(mock_config_manager)

        # Act & Assert: Check for the expected exception
        with pytest.raises(
            ValueError, match="No metrics were calculated. Check your input data."
        ):
            builder.build_report(
                config=mock_config,
                results=mock_genome_mining_results,
                running_mode=RunningMode.UNKNOWN,
            )


def test_build_report_missing_basic_config(
    mock_config_manager, mock_genome_mining_results, mock_config
):
    """
    Test that a ValueError is raised when the basic_report config is not found.
    """
    # Arrange: Mock the config manager to return None
    mock_config_manager.get_config.return_value = None

    builder = ReportBuilder(mock_config_manager)

    # Act & Assert: Check for the expected exception
    with pytest.raises(
        ValueError, match="No configuration found for running mode: basic_report"
    ):
        builder.build_report(
            config=mock_config,
            results=mock_genome_mining_results,
            running_mode=RunningMode.UNKNOWN,
        )
