from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.genome_mining_parser import GenomeMiningResult, QuastResult
from src.logger import Logger
from src.option_parser import ValidationError
from src.pipeline_helper import PipelineHelper
from src.report import RunningMode

# Test data paths
TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
ANTISMASH_FILE = (
    TEST_DATA_DIR / "assembly_10_mining" / "antiSMASH" / "assembly_10.json.gz"
)
QUAST_OUTPUT_DIR = TEST_DATA_DIR / "quast_out"


@pytest.fixture
def logger():
    """Create a mock logger instance for testing."""
    logger = MagicMock(spec=Logger)
    return logger


@pytest.fixture
def pipeline_helper(logger, tmp_path):
    """Create a PipelineHelper instance with test configuration."""
    with patch("src.pipeline_helper.get_command_line_args") as mock_args:
        mock_args.return_value = MagicMock(
            mining_results=[ANTISMASH_FILE],
            quast_output_dir=None,
            reference_mining_result=None,
            output_dir=tmp_path,
        )
        with patch("src.pipeline_helper.load_config") as mock_config:
            mock_config.return_value = MagicMock(
                output_config=MagicMock(
                    output_dir=tmp_path,
                    report=tmp_path / "report.txt",
                    html_report=tmp_path / "report.html",
                )
            )
            yield PipelineHelper(logger)


def test_initialization(pipeline_helper):
    """Test that the PipelineHelper initializes correctly."""
    assert pipeline_helper.log is not None
    assert pipeline_helper.genome_mining_results == []
    assert pipeline_helper.reference_mining_result is None
    assert pipeline_helper.quast_results is None


def test_set_up_output_dir_creates_directory(pipeline_helper, tmp_path):
    """Test that set_up_output_dir creates the output directory if it doesn't exist."""
    output_dir = tmp_path / "output"
    pipeline_helper.config.output_config.output_dir = output_dir

    pipeline_helper.set_up_output_dir()
    assert output_dir.exists()


def test_set_up_output_dir_warns_if_exists(pipeline_helper, tmp_path):
    """Test that set_up_output_dir logs a warning if the directory already exists."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pipeline_helper.config.output_config.output_dir = output_dir

    pipeline_helper.set_up_output_dir()
    pipeline_helper.log.warning.assert_called_with(
        f"Output directory ({output_dir}) already exists! The content will be overwritten."
    )


def test_parse_input_valid_input(pipeline_helper):
    """Test parsing valid input files."""
    with (
        patch("src.pipeline_helper.parse_input_files") as mock_parse,
        patch("src.pipeline_helper.utils.determine_running_mode") as mock_mode,
    ):
        mock_parse.return_value = [MagicMock(spec=GenomeMiningResult)]
        mock_mode.return_value = RunningMode.COMPARE_TOOLS
        pipeline_helper.parse_input()

        assert len(pipeline_helper.genome_mining_results) == 1
        mock_parse.assert_called_with(pipeline_helper.config, [ANTISMASH_FILE])


def test_parse_input_invalid_input(pipeline_helper):
    """Test parsing invalid input files."""
    with patch(
        "src.pipeline_helper.parse_input_files", side_effect=Exception("Invalid input")
    ):
        with pytest.raises(Exception, match="Invalid input"):
            pipeline_helper.parse_input()
        pipeline_helper.log.error.assert_called_with(
            "Failed to parse genome mining results: Invalid input"
        )


def test_parse_input_missing_reference(pipeline_helper):
    """Test error when QUAST results are provided without a reference genome."""
    pipeline_helper.args.reference_mining_result = None
    pipeline_helper.args.quast_output_dir = QUAST_OUTPUT_DIR

    with patch("src.pipeline_helper.parse_quast_output_dir") as mock_parse:
        mock_parse.return_value = MagicMock(spec=QuastResult)
        with pytest.raises(
            ValidationError, match="Reference genome mining result is required"
        ):
            pipeline_helper.parse_input()
        pipeline_helper.log.error.assert_called_with(
            "Reference genome mining result is required when QUAST "
            "output directory is specified."
        )


def test_parse_input_missing_quast(pipeline_helper):
    """Test error when reference genome is provided without QUAST results."""
    pipeline_helper.args.reference_mining_result = ANTISMASH_FILE
    pipeline_helper.args.quast_output_dir = None

    with pytest.raises(ValidationError, match="QUAST output directory is required"):
        pipeline_helper.parse_input()
    pipeline_helper.log.error.assert_called_with(
        "QUAST output directory is required when Reference genome mining "
        "result is specified."
    )


def test_parse_input_sets_running_mode(pipeline_helper):
    """Test that parse_input sets the running_mode correctly."""
    with (
        patch("src.pipeline_helper.parse_input_files") as mock_parse,
        patch("src.pipeline_helper.utils.determine_running_mode") as mock_mode,
    ):
        mock_parse.return_value = [MagicMock(spec=GenomeMiningResult)]
        mock_mode.return_value = RunningMode.COMPARE_TOOLS

        pipeline_helper.parse_input()

        assert pipeline_helper.running_mode == RunningMode.COMPARE_TOOLS
        mock_mode.assert_called_once()
        pipeline_helper.log.info.assert_called_with(
            "Running mode set to: RunningMode.COMPARE_TOOLS"
        )


def test_parse_input_unknown_mode_raises_error(pipeline_helper):
    """Test that parse_input raises error when running mode is unknown."""
    with (
        patch("src.pipeline_helper.parse_input_files") as mock_parse,
        patch("src.pipeline_helper.utils.determine_running_mode") as mock_mode,
    ):
        mock_parse.return_value = [MagicMock(spec=GenomeMiningResult)]
        mock_mode.return_value = RunningMode.UNKNOWN

        with pytest.raises(
            ValidationError, match="Running mode could not be determined"
        ):
            pipeline_helper.parse_input()

        pipeline_helper.log.error.assert_called_with(
            "Running mode could not be determined. "
            "Please provide a valid combination of genome mining results."
        )


def test_compute_stats_placeholder(pipeline_helper):
    """Test that compute_stats is a placeholder."""
    assert pipeline_helper.compute_stats() is None


def test_write_results_logs_results(pipeline_helper):
    """Test that write_results logs the locations of the reports."""
    pipeline_helper.write_results()
    pipeline_helper.log.info.assert_any_call("RESULTS:")
    pipeline_helper.log.info.assert_any_call(
        f"Text report is saved to {pipeline_helper.config.output_config.report}",
        indent=1,
    )
    pipeline_helper.log.info.assert_any_call(
        f"HTML report is saved to {pipeline_helper.config.output_config.html_report}",
        indent=1,
    )
