from pathlib import Path
from unittest.mock import MagicMock, patch

from src.basic_analyzer import (
    generate_basic_report,
    generate_metrics,
    generate_metrics_for_all,
)
from src.genome_mining_result import GenomeMiningResult
from src.report import BasicReport


def test_generate_metrics():
    """Test generate_metrics function."""

    mock_result = MagicMock(spec=GenomeMiningResult, bgcs=[])

    with patch("src.metrics.MetricsEngine.compute") as mock_compute:
        mock_compute.side_effect = lambda group_by: {
            tuple(group_by): {"metric": "value"}
        }
        metrics = generate_metrics(mock_result)

        assert metrics == {
            "total": {(): {"metric": "value"}},
            "by_type": {("product_type",): {"metric": "value"}},
            "by_completeness": {("completeness",): {"metric": "value"}},
            "by_type_completeness": {
                ("product_type", "completeness"): {"metric": "value"}
            },
        }


def test_generate_metrics_for_all():
    """Test generate_metrics_for_all function."""
    mock_result1 = MagicMock(spec=GenomeMiningResult, input_file=Path("file1.json"))
    mock_result2 = MagicMock(spec=GenomeMiningResult, input_file=Path("file2.json"))
    mock_results = [mock_result1, mock_result2]

    with patch("src.basic_analyzer.generate_metrics") as mock_generate_metrics:
        mock_generate_metrics.side_effect = lambda result: {
            f"metrics_for_{result.input_file}": "value"
        }
        metrics = generate_metrics_for_all(mock_results)

        assert metrics == {
            Path("file1.json"): {"metrics_for_file1.json": "value"},
            Path("file2.json"): {"metrics_for_file2.json": "value"},
        }


def test_generate_basic_report():
    """Test generate_basic_report function."""
    mock_result1 = MagicMock(spec=GenomeMiningResult, input_file=Path("file1.json"))
    mock_result2 = MagicMock(spec=GenomeMiningResult, input_file=Path("file2.json"))
    mock_results = [mock_result1, mock_result2]

    with patch(
        "src.basic_analyzer.generate_metrics_for_all"
    ) as mock_generate_metrics_for_all:
        mock_generate_metrics_for_all.return_value = {
            Path("file1.json"): {"metric1": "value1"},
            Path("file2.json"): {"metric2": "value2"},
        }
        report = generate_basic_report(mock_results)

        assert isinstance(report, BasicReport)
        assert report.basic_metrics == {
            Path("file1.json"): {"metric1": "value1"},
            Path("file2.json"): {"metric2": "value2"},
        }
