from typing import List, Optional

import src.basic_analyzer as basic_analyzer
import src.input_utils as input_utils
import src.report_writer as report_writer
from src import compare_to_ref_analyzer
from src.config import load_config
from src.genome_mining_parser import (
    GenomeMiningResult,
    QuastResult,
    parse_input_files,
    parse_quast_output_dir,
)
from src.logger import Logger
from src.option_parser import ValidationError, get_command_line_args
from src.report import BasicReport, RunningMode


class PipelineHelper:
    """
    A helper class to manage the BGC-QUAST pipeline.

    Attributes:
        config: Configuration object for the pipeline.
        args: Command-line arguments parsed into an object.
        log: Logger instance for logging operations.
        assembly_genome_mining_results: List of parsed genome mining results.
        reference_genome_mining_result: Parsed reference genome mining result.
        quast_results: List of parsed QUAST results.

        running_mode: Running mode of the pipeline (e.g., COMPARE_TO_REFERENCE,
        COMPARE_TOOLS, COMPARE_SAMPLES).
        analysis_report: Report with analysis results.
    """

    def __init__(self, log: Logger):
        """
        Initialize the PipelineHelper.

        Args:
            log: Logger instance for logging operations.
        """
        self.log = log
        self.assembly_genome_mining_results: List[GenomeMiningResult] = []
        self.reference_genome_mining_result: Optional[GenomeMiningResult] = None
        self.quast_results: Optional[List[QuastResult]] = None
        self.running_mode: Optional[RunningMode] = None
        self.analysis_report: Optional[BasicReport] = None

        default_cfg = load_config()
        try:
            self.args = get_command_line_args(default_cfg)
        except ValidationError as e:
            self.log.error(
                f"Command-line argument validation failed: {str(e)}",
                to_stderr=True,
            )
            raise e

        try:
            self.config = load_config(self.args)
        except ValueError as e:
            self.log.error(f"Configuration loading failed: {str(e)}", to_stderr=True)
            raise e

        self.set_up_output_dir()
        self.log.set_up_file_handler(self.config.output_config.output_dir)
        self.log.start()

    def set_up_output_dir(self) -> None:
        """
        Set up the output directory for the pipeline.

        If the directory already exists, log a warning and overwrite its content.
        """
        output_dir = self.config.output_config.output_dir
        if output_dir.exists():
            self.log.warning(
                f"Output directory ({output_dir}) already exists! "
                f"The content will be overwritten."
            )
        else:
            output_dir.mkdir(parents=True)

        # TODO: Create 'latest' symlink if needed (default output dir with timestamp)

    def parse_input(self) -> None:
        """
        Parse input files for genome mining and QUAST results.

        Raises:
            ValidationError: If required inputs are missing or invalid.
        """
        # TODO: move this part into the option_parser? There is a so-far-empty function for validating input correctness
        if self.args.quast_output_dir and not self.args.reference_mining_result:
            error_message = "Reference genome mining result is required when QUAST output directory is specified."
            self.log.error(error_message)
            raise ValidationError(error_message)
        if not self.args.quast_output_dir and self.args.reference_mining_result:
            error_message = "QUAST output directory is required when Reference genome mining result is specified."
            self.log.error(error_message)
            raise ValidationError(error_message)

        try:
            self.assembly_genome_mining_results = parse_input_files(
                self.config, self.args.mining_results
            )
        except Exception as e:
            self.log.error(f"Failed to parse genome mining results: {str(e)}")
            raise e

        if self.args.quast_output_dir:
            try:
                self.quast_results = parse_quast_output_dir(self.args.quast_output_dir)
            except Exception as e:
                self.log.error(f"Failed to parse QUAST results: {str(e)}")
                raise e

        if self.args.reference_mining_result:
            try:
                self.reference_genome_mining_result = parse_input_files(
                    self.config, [self.args.reference_mining_result]
                )[0]
            except Exception as e:
                self.log.error(
                    f"Failed to parse reference genome mining results: {str(e)}"
                )
                raise e

        # Set running mode based on the provided arguments.
        self.running_mode = input_utils.determine_running_mode(
            self.reference_genome_mining_result, self.assembly_genome_mining_results
        )
        if self.running_mode == RunningMode.UNKNOWN:
            error_message = (
                "Running mode could not be determined. "
                "Please provide a valid combination of genome mining results."
            )
            self.log.error(error_message)
            raise ValidationError(error_message)

        self.log.info(f"Running mode set to: {self.running_mode}")

    def compute_stats(self) -> None:
        """
        Compute statistics for the parsed results.
        """

        analysis_report = basic_analyzer.generate_basic_report(
            self.assembly_genome_mining_results
        )

        if self.running_mode == RunningMode.COMPARE_TO_REFERENCE:
            analysis_report = compare_to_ref_analyzer.compute_stats(
                analysis_report,
                self.assembly_genome_mining_results,
                self.reference_genome_mining_result,
                self.quast_results,
            )
        elif self.running_mode == RunningMode.COMPARE_TOOLS:
            # TODO: Implement analysis for COMPARE_TOOLS mode
            pass
        elif self.running_mode == RunningMode.COMPARE_SAMPLES:
            # TODO: Implement analysis for COMPARE_SAMPLES mode
            pass

        self.analysis_report = analysis_report

    def write_results(self) -> None:
        """
        Write the results of the pipeline to the output directory.

        Logs the locations of the text and HTML reports.
        """

        if not self.analysis_report:
            self.log.error("No analysis report available to write results.")
            return

        report_writer.write_report(
            self.analysis_report,
            self.config.output_config.report,
            self.config.output_config.html_report,
        )

        self.log.info("RESULTS:")
        self.log.info(
            f"Text report is saved to {self.config.output_config.report}",
            indent=1,
        )
        self.log.info(
            f"HTML report is saved to {self.config.output_config.html_report}",
            indent=1,
        )
        # TODO: Actually write something to the specified reports

        self.log.finish()  # TODO: Create a separate method for this and "cleaning up"
