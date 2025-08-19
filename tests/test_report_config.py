"""Unit tests for the report_config module."""

from unittest.mock import mock_open, patch

import pytest
from src.reporting.report_config import (
    GroupingDimensionConfig,
    MetricConfig,
    ReportConfig,
    ReportConfigManager,
)


@pytest.fixture
def mock_config_manager():
    """Fixture to create a ReportConfigManager with a mock config file."""
    mock_yaml_content = """
basic_report:
  metrics:
    - name: "total_bgc_count"
      display_name: "# BGCs"
      description: "Total number of BGCs identified"
  grouping_dimensions:
    product_type:
      include_total: true
      order: ["total", "NRPS", "PKS"]
  grouping_combinations: [["product_type"]]

compare_to_reference:
  metrics:
    - name: "fully_recovered_bgcs"
      display_name: "Fully recovered BGCs"
  grouping_dimensions:
    product_type:
      include_total: false
  grouping_combinations: [["product_type"]]
"""
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
        yield ReportConfigManager()


def test_successful_loading(mock_config_manager: ReportConfigManager):
    """Test that the configuration is loaded successfully."""
    assert "basic_report" in mock_config_manager.list_report_types()
    assert "compare_to_reference" in mock_config_manager.list_report_types()


def test_get_config(mock_config_manager: ReportConfigManager):
    """Test retrieving a specific report configuration."""
    config = mock_config_manager.get_config("basic_report")
    assert isinstance(config, ReportConfig)
    assert len(config.metrics) == 1
    assert config.metrics[0].name == "total_bgc_count"


def test_get_invalid_config(mock_config_manager: ReportConfigManager):
    """Test that retrieving a non-existent config raises a ValueError."""
    with pytest.raises(ValueError):
        mock_config_manager.get_config("non_existent_report")


def test_file_not_found():
    """Test that a FileNotFoundError is raised if the config file is not found."""
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError
        with pytest.raises(FileNotFoundError):
            ReportConfigManager()


def test_invalid_yaml():
    """Test that a ValueError is raised for invalid YAML."""
    invalid_yaml_content = "basic_report: { metric: [ name: 'test' }"
    with patch("builtins.open", mock_open(read_data=invalid_yaml_content)):
        with pytest.raises(ValueError):
            ReportConfigManager()


def test_combined_config(mock_config_manager: ReportConfigManager):
    """Test combining multiple report configurations."""
    combined_config = mock_config_manager.get_combined_config(
        ["basic_report", "compare_to_reference"]
    )
    assert len(combined_config.metrics) == 2
    assert "product_type" in combined_config.grouping_dimensions
    # Check that the last seen grouping dimension config is used
    assert not combined_config.grouping_dimensions["product_type"].include_total


def test_metric_config_parsing(mock_config_manager: ReportConfigManager):
    """Test that MetricConfig is parsed correctly."""
    config = mock_config_manager.get_config("basic_report")
    metric = config.metrics[0]
    assert isinstance(metric, MetricConfig)
    assert metric.name == "total_bgc_count"
    assert metric.display_name == "# BGCs"
    assert metric.description == "Total number of BGCs identified"


def test_grouping_dimension_config_parsing(mock_config_manager: ReportConfigManager):
    """Test that GroupingDimensionConfig is parsed correctly."""
    config = mock_config_manager.get_config("basic_report")
    grouping_dim = config.grouping_dimensions["product_type"]
    assert isinstance(grouping_dim, GroupingDimensionConfig)
    assert grouping_dim.include_total
    assert grouping_dim.order == ["total", "NRPS", "PKS"]
