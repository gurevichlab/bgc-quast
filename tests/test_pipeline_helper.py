from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from bgc_quast.genome_mining_parser import GenomeMiningResult, QuastResult
from bgc_quast.logger import Logger
from bgc_quast.option_parser import ValidationError
from bgc_quast.pipeline_helper import PipelineHelper
from bgc_quast.reporting.report_data import RunningMode

# Test data paths
TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
DUMMY_ANTISMASH_FILE = TEST_DATA_DIR / "dummy_antismash.json"
QUAST_OUTPUT_DIR = TEST_DATA_DIR / "quast_out"

def create_mock_genome_mining_result(input_file="dummy.fasta", input_file_label="dummy", mining_tool="tool"):
    mock = MagicMock(spec=GenomeMiningResult)
    mock.input_file = Path(input_file)
    mock.input_file_label = input_file_label
    mock.display_label = None
    mock.mining_tool = mining_tool
    return mock



@pytest.fixture
def logger():
    """Create a mock logger instance for testing."""
    logger = MagicMock(spec=Logger)
    return logger


@pytest.fixture
def pipeline_helper(logger, tmp_path):
    """Create a PipelineHelper instance with test configuration."""
    with patch("bgc_quast.pipeline_helper.get_command_line_args") as mock_args:
        mock_args.return_value = MagicMock(
            mining_results=[DUMMY_ANTISMASH_FILE],
            quast_output_dir=None,
            reference_mining_result=None,
            genome_data=None,
            reference_genome_data=None,
            output_dir=tmp_path,
        )
        with patch("bgc_quast.pipeline_helper.load_config") as mock_config:
            mock_config.return_value = MagicMock(
                output_config=MagicMock(
                    output_dir=tmp_path,
                    report=tmp_path / "report.txt",
                    html_report=tmp_path / "report.html",
                    bgc_annotations_basename="bgcs",
                    bgc_completeness_margin=100,
                    update_latest_symlink=False,
                ),
                min_bgc_length=0,
                bgc_completeness_margin=100,
            )
            yield PipelineHelper(logger)


def test_initialization(pipeline_helper):
    """Test that the PipelineHelper initializes correctly."""
    assert pipeline_helper.log is not None
    assert pipeline_helper.assembly_genome_mining_results == []
    assert pipeline_helper.reference_genome_mining_result is None
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
        f"The output directory ({output_dir}) already exists! Existing files may be overwritten."
    )


def test_parse_input_valid_input(pipeline_helper):
    """Test parsing valid input files."""
    with (
        patch("bgc_quast.pipeline_helper.parse_input_mining_result_files") as mock_parse,
        patch("bgc_quast.pipeline_helper.input_utils.determine_running_mode") as mock_mode,
    ):
        mock_parse.return_value = [create_mock_genome_mining_result()]
        mock_mode.return_value = RunningMode.COMPARE_TOOLS
        pipeline_helper.parse_input()

        assert len(pipeline_helper.assembly_genome_mining_results) == 1
        mock_parse.assert_called_with(
            pipeline_helper.log,
            pipeline_helper.config,
            [DUMMY_ANTISMASH_FILE],
            None,
            matching_aliases=None,
        )


def test_parse_input_invalid_input(pipeline_helper):
    """Test parsing invalid input files."""
    with patch(
        "bgc_quast.pipeline_helper.parse_input_mining_result_files",
        side_effect=Exception("Invalid input"),
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

    with patch("bgc_quast.pipeline_helper.parse_quast_output_dir") as mock_parse:
        mock_parse.return_value = MagicMock(spec=QuastResult)
        with pytest.raises(
            ValidationError, match="The reference genome mining result is required"
        ):
            pipeline_helper.parse_input()
        pipeline_helper.log.error.assert_called_with(
            "The reference genome mining result is required in the compare-to-reference mode.\n"
            "Please specify it using --reference-mining-result FILE or -r FILE."
        )


def test_parse_input_missing_quast(pipeline_helper):
    """Test error when reference genome is provided without QUAST results."""
    pipeline_helper.args.reference_mining_result = DUMMY_ANTISMASH_FILE
    pipeline_helper.args.quast_output_dir = None

    with pytest.raises(ValidationError, match="The QUAST output directory is required"):
        pipeline_helper.parse_input()
    pipeline_helper.log.error.assert_called_with(
        "The QUAST output directory is required in the compare-to-reference mode.\n"
        "Please specify it using --quast-output-dir DIR or -q DIR."
    )


def test_parse_input_sets_running_mode(pipeline_helper):
    """Test that parse_input sets the running_mode correctly."""
    with (
        patch("bgc_quast.pipeline_helper.parse_input_mining_result_files") as mock_parse,
        patch("bgc_quast.pipeline_helper.input_utils.determine_running_mode") as mock_mode,
    ):
        mock_parse.return_value = [create_mock_genome_mining_result()]
        mock_mode.return_value = RunningMode.COMPARE_TOOLS

        pipeline_helper.parse_input()

        assert pipeline_helper.running_mode == RunningMode.COMPARE_TOOLS
        mock_mode.assert_called_once()
        pipeline_helper.log.info.assert_called_with(
            "The running mode is set to: RunningMode.COMPARE_TOOLS"
        )


def test_parse_input_unknown_mode_raises_error(pipeline_helper):
    """Test that parse_input raises error when running mode is unknown."""
    with (
        patch("bgc_quast.pipeline_helper.parse_input_mining_result_files") as mock_parse,
        patch("bgc_quast.pipeline_helper.input_utils.determine_running_mode") as mock_mode,
    ):
        mock_parse.return_value = [create_mock_genome_mining_result()]
        mock_mode.side_effect = ValidationError(
            "Running mode could not be determined. "
            "Please provide a valid combination of genome mining results."
        )

        with pytest.raises(
            ValidationError, match="Running mode could not be determined"
        ):
            pipeline_helper.parse_input()

        pipeline_helper.log.error.assert_called_with(
            "Running mode could not be determined. "
            "Please provide a valid combination of genome mining results."
        )


def test_compute_stats_creates_analysis_report(pipeline_helper):
    """Test that compute_stats creates an ReportData report."""
    mock_genome_mining_result = MagicMock()
    pipeline_helper.assembly_genome_mining_results = [mock_genome_mining_result]
    pipeline_helper.running_mode = RunningMode.COMPARE_TOOLS
    pipeline_helper.quast_results = [MagicMock(spec=QuastResult)]

    with patch("bgc_quast.pipeline_helper.ReportBuilder.build_report") as mock_build_report:
        mock_report = MagicMock()
        mock_build_report.return_value = mock_report

        pipeline_helper.compute_stats()

        mock_build_report.assert_called_once_with(
            config=pipeline_helper.config,
            results=[mock_genome_mining_result],
            running_mode=RunningMode.COMPARE_TOOLS,
            quast_results=pipeline_helper.quast_results,
            reference_genome_mining_result=None,
            label_renaming_log=[],
            requested_mode=pipeline_helper.args.mode,
            matching_aliases=None,
            log=pipeline_helper.log,
        )
        assert pipeline_helper.analysis_report == mock_report


def test_write_results_logs_results(pipeline_helper):
    """Test that write_results logs the locations of the reports."""
    with patch("bgc_quast.pipeline_helper.report_writer.write_report") as mock_write_report:
        mock_write_report.return_value = None
        pipeline_helper.analysis_report = MagicMock()

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
        pipeline_helper.log.info.assert_any_call(
            f"TSV report is saved to {pipeline_helper.config.output_config.tsv_report}",
            indent=1,
        )


def test_parse_input_with_genome_data(pipeline_helper):
    """Test parsing input when genome data is provided."""
    with (
        patch("bgc_quast.pipeline_helper.parse_input_mining_result_files") as mock_parse,
        patch("bgc_quast.pipeline_helper.input_utils.determine_running_mode") as mock_mode,
    ):
        pipeline_helper.args.genome_data = [Path("dummy.fasta")]
        pipeline_helper.args.mining_results = [DUMMY_ANTISMASH_FILE]
        mock_parse.return_value = [create_mock_genome_mining_result()]
        mock_mode.return_value = RunningMode.COMPARE_TOOLS

        pipeline_helper.parse_input()
        mock_parse.assert_called_with(
            pipeline_helper.log,
            pipeline_helper.config,
            [DUMMY_ANTISMASH_FILE],
            pipeline_helper.args.genome_data,
            matching_aliases=None,
        )


def test_parse_input_with_reference_genome_data(pipeline_helper):
    """Test parsing input with reference genome data."""
    with (
        patch("bgc_quast.pipeline_helper.parse_input_mining_result_files") as mock_parse,
        patch(
            "bgc_quast.pipeline_helper.parse_reference_genome_mining_result"
        ) as mock_ref_parse,
        patch("bgc_quast.pipeline_helper.input_utils.determine_running_mode") as mock_mode,
    ):
        pipeline_helper.args.reference_genome_data = Path("ref_genome.fasta")
        pipeline_helper.args.reference_mining_result = DUMMY_ANTISMASH_FILE
        pipeline_helper.args.quast_output_dir = QUAST_OUTPUT_DIR
        pipeline_helper.args.mining_results = [Path("dummy.fasta")]
        mock_parse.return_value = [create_mock_genome_mining_result()]
        mock_ref_parse.return_value = create_mock_genome_mining_result(input_file="ref_genome.fasta", input_file_label="reference")
        mock_mode.return_value = RunningMode.COMPARE_TOOLS

        pipeline_helper.parse_input()
        mock_ref_parse.assert_called_with(
            pipeline_helper.log,
            pipeline_helper.config,
            DUMMY_ANTISMASH_FILE,
            pipeline_helper.args.reference_genome_data,
        )

def test_parse_input_passes_names_as_matching_aliases(pipeline_helper):
    """Test that --names values are passed as genome-matching aliases."""
    mining_results = [
        Path("sample1/DeepBGC/DeepBGC.bgc.tsv"),
        Path("sample2/DeepBGC/DeepBGC.bgc.tsv"),
    ]

    pipeline_helper.args.mining_results = mining_results
    pipeline_helper.args.names = "assembly_1,assembly_2"

    with (
        patch(
            "bgc_quast.pipeline_helper.parse_input_mining_result_files"
        ) as mock_parse,
        patch(
            "bgc_quast.pipeline_helper.input_utils.determine_running_mode"
        ) as mock_mode,
    ):
        mock_parse.return_value = [
            create_mock_genome_mining_result(),
            create_mock_genome_mining_result(),
        ]
        mock_mode.return_value = RunningMode.COMPARE_SAMPLES

        pipeline_helper.parse_input()

        mock_parse.assert_called_with(
            pipeline_helper.log,
            pipeline_helper.config,
            mining_results,
            pipeline_helper.args.genome_data,
            matching_aliases=["assembly_1", "assembly_2"],
        )


def test_parse_input_rejects_multiple_genomes_in_compare_tools(pipeline_helper):
    """Compare-tools mode must accept at most one genome."""
    pipeline_helper.args.genome_data = [
        Path("genome_1.fasta"),
        Path("genome_2.fasta"),
    ]
    pipeline_helper.args.mode = "compare-tools"
    pipeline_helper.args.names = None
    pipeline_helper.args.ref_name = None

    error_message = (
        "In compare-tools mode, all genome mining results must describe the same genome, "
        "so at most one genome file can be provided. "
        f"Expected 0 or 1 genome file, but got 2. "
        "Use -G/--genome to provide a single genome file."
    )

    with (
        patch(
            "bgc_quast.pipeline_helper.parse_input_mining_result_files"
        ) as mock_parse,
        patch(
            "bgc_quast.pipeline_helper.input_utils.determine_running_mode"
        ) as mock_mode,
    ):
        mock_parse.return_value = [
            create_mock_genome_mining_result(),
            create_mock_genome_mining_result(),
        ]
        mock_mode.return_value = RunningMode.COMPARE_TOOLS

        with pytest.raises(
            ValidationError,
            match="In compare-tools mode, all genome mining results must describe the same genome",
        ):
            pipeline_helper.parse_input()

    pipeline_helper.log.error.assert_called_with(error_message)

def test_parse_input_allows_multiple_genomes_in_compare_samples(pipeline_helper):
    """Compare-samples mode may use multiple genome files."""
    pipeline_helper.args.mining_results = [
        Path("sample_1.json"),
        Path("sample_2.json"),
    ]
    pipeline_helper.args.genome_data = [
        Path("genome_1.fasta"),
        Path("genome_2.fasta"),
    ]
    pipeline_helper.args.mode = "compare-samples"
    pipeline_helper.args.names = None
    pipeline_helper.args.ref_name = None

    with (
        patch(
            "bgc_quast.pipeline_helper.parse_input_mining_result_files"
        ) as mock_parse,
        patch(
            "bgc_quast.pipeline_helper.input_utils.determine_running_mode"
        ) as mock_mode,
    ):
        mock_parse.return_value = [
            create_mock_genome_mining_result(
                input_file="sample_1.json",
                input_file_label="sample_1",
            ),
            create_mock_genome_mining_result(
                input_file="sample_2.json",
                input_file_label="sample_2",
            ),
        ]
        mock_mode.return_value = RunningMode.COMPARE_SAMPLES

        pipeline_helper.parse_input()

    assert pipeline_helper.running_mode == RunningMode.COMPARE_SAMPLES

def test_parse_input_allows_multiple_genomes_in_compare_to_reference(
    pipeline_helper,
):
    """Compare-to-reference mode may use multiple assembly genomes."""
    pipeline_helper.args.mining_results = [
        Path("assembly_1.json"),
        Path("assembly_2.json"),
    ]
    pipeline_helper.args.genome_data = [
        Path("genome_1.fasta"),
        Path("genome_2.fasta"),
    ]
    pipeline_helper.args.reference_mining_result = Path("reference.json")
    pipeline_helper.args.quast_output_dir = QUAST_OUTPUT_DIR
    pipeline_helper.args.mode = "compare-to-reference"
    pipeline_helper.args.names = None
    pipeline_helper.args.ref_name = None

    with (
        patch(
            "bgc_quast.pipeline_helper.parse_input_mining_result_files"
        ) as mock_parse,
        patch(
            "bgc_quast.pipeline_helper.parse_quast_output_dir"
        ) as mock_quast_parse,
        patch(
            "bgc_quast.pipeline_helper.parse_reference_genome_mining_result"
        ) as mock_reference_parse,
        patch(
            "bgc_quast.pipeline_helper.input_utils.determine_running_mode"
        ) as mock_mode,
    ):
        mock_parse.return_value = [
            create_mock_genome_mining_result(
                input_file="assembly_1.json",
                input_file_label="assembly_1",
            ),
            create_mock_genome_mining_result(
                input_file="assembly_2.json",
                input_file_label="assembly_2",
            ),
        ]
        mock_quast_parse.return_value = []
        mock_reference_parse.return_value = create_mock_genome_mining_result(
            input_file="reference.json",
            input_file_label="reference",
        )
        mock_mode.return_value = RunningMode.COMPARE_TO_REFERENCE

        pipeline_helper.parse_input()

    assert pipeline_helper.running_mode == RunningMode.COMPARE_TO_REFERENCE


def test_parse_input_rejects_incomplete_genomes_in_compare_samples(
    pipeline_helper,
):
    """Compare-samples requires one genome per result when genomes are given."""
    pipeline_helper.args.mining_results = [
        Path("sample_1.json"),
        Path("sample_2.json"),
    ]
    pipeline_helper.args.genome_data = [Path("genome_1.fasta")]
    pipeline_helper.args.mode = "compare-samples"
    pipeline_helper.args.names = None
    pipeline_helper.args.ref_name = None

    error_message = (
        "In compare-samples mode, the number of genome files provided with -G/--genome "
        "must either be zero or match the number of input genome mining result files. "
        "Expected 0 or 2 genome file(s), but got 1. "
        "Use -G/--genome to provide one genome file per input genome mining result file."
    )

    with (
        patch(
            "bgc_quast.pipeline_helper.parse_input_mining_result_files"
        ) as mock_parse,
        patch(
            "bgc_quast.pipeline_helper.input_utils.determine_running_mode"
        ) as mock_mode,
    ):
        mock_parse.return_value = [
            create_mock_genome_mining_result(),
            create_mock_genome_mining_result(),
        ]
        mock_mode.return_value = RunningMode.COMPARE_SAMPLES

        with pytest.raises(
            ValidationError,
            match="either be zero or match the number of input genome mining result files",
        ):
            pipeline_helper.parse_input()

    pipeline_helper.log.error.assert_called_with(error_message)

def test_parse_input_rejects_incomplete_genomes_in_compare_to_reference(
    pipeline_helper,
):
    """Reference mode requires one assembly genome per result when provided."""
    pipeline_helper.args.mining_results = [
        Path("assembly_1.json"),
        Path("assembly_2.json"),
    ]
    pipeline_helper.args.genome_data = [Path("genome_1.fasta")]
    pipeline_helper.args.reference_mining_result = Path("reference.json")
    pipeline_helper.args.quast_output_dir = QUAST_OUTPUT_DIR
    pipeline_helper.args.mode = "compare-to-reference"
    pipeline_helper.args.names = None
    pipeline_helper.args.ref_name = None

    error_message = (
        "In compare-to-reference mode, the number of genome files provided with -G/--genome "
        "must either be zero or match the number of input genome mining result files. "
        "Expected 0 or 2 genome file(s), but got 1. "
        "Use -G/--genome to provide one genome file per input genome mining result file."
    )

    with (
        patch(
            "bgc_quast.pipeline_helper.parse_input_mining_result_files"
        ) as mock_parse,
        patch(
            "bgc_quast.pipeline_helper.parse_quast_output_dir"
        ) as mock_quast_parse,
        patch(
            "bgc_quast.pipeline_helper.parse_reference_genome_mining_result"
        ) as mock_reference_parse,
        patch(
            "bgc_quast.pipeline_helper.input_utils.determine_running_mode"
        ) as mock_mode,
    ):
        mock_parse.return_value = [
            create_mock_genome_mining_result(),
            create_mock_genome_mining_result(),
        ]
        mock_quast_parse.return_value = []
        mock_reference_parse.return_value = (
            create_mock_genome_mining_result(
                input_file="reference.json",
                input_file_label="reference",
            )
        )
        mock_mode.return_value = RunningMode.COMPARE_TO_REFERENCE

        with pytest.raises(
            ValidationError,
            match="either be zero or match the number of input genome mining result",
        ):
            pipeline_helper.parse_input()

    pipeline_helper.log.error.assert_called_with(error_message)