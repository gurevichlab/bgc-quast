from typing import List, Optional
from pathlib import Path

import src.input_utils as input_utils
import src.reporting.report_writer as report_writer
from src.config import load_config
from src.genome_mining_parser import (
    GenomeMiningResult,
    QuastResult,
    parse_input_mining_result_files,
    parse_quast_output_dir,
    parse_reference_genome_mining_result,
)
from src.logger import Logger
from src.option_parser import ValidationError, get_command_line_args
from src.reporting.report_builder import ReportBuilder
from src.reporting.report_config import ReportConfigManager
from src.reporting.report_data import ReportData, RunningMode


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
        self.analysis_report: Optional[ReportData] = None
        self.label_renaming_log: List[dict] = []

        default_cfg = load_config()
        try:
            self.args = get_command_line_args(default_cfg)
        except ValidationError as e:
            self.log.error(
                f"The command-line argument validation failed: {str(e)}",
                to_stderr=True,
            )
            raise e

        try:
            self.config = load_config(self.args)
        except ValueError as e:
            self.log.error(f"The configuration loading failed: {str(e)}", to_stderr=True)
            raise e

        self.set_up_output_dir()
        self.log.set_up_file_handler(self.config.output_config.output_dir)
        self.log.start()

    def set_up_output_dir(self) -> None:
        output_cfg = self.config.output_config
        output_dir = output_cfg.output_dir

        if output_dir.exists():
            self.log.warning(
                f"The output directory ({output_dir}) already exists! "
                f"Existing files may be overwritten."
            )
        else:
            output_dir.mkdir(parents=True)

        # Only for the *default timestamped* output dir:
        if output_cfg.update_latest_symlink:
            self._update_latest_symlink(output_cfg.latest_symlink, output_dir)

    def _update_latest_symlink(self, symlink_path: Path, target_dir: Path) -> None:
        """
        Create/overwrite symlink_path -> target_dir.
        """
        try:
            if symlink_path.exists() or symlink_path.is_symlink():
                # If it's a symlink or file, unlink. If it's a real dir, be defensive.
                if symlink_path.is_dir() and not symlink_path.is_symlink():
                    raise RuntimeError(
                        f"Cannot overwrite '{symlink_path}': it exists and is a directory (not a symlink)."
                    )
                symlink_path.unlink()

            relative_target = target_dir.relative_to(symlink_path.parent)
            symlink_path.symlink_to(relative_target, target_is_directory=True)
        except OSError as e:
            self.log.warning(f"Failed to update the latest symlink '{symlink_path}' -> '{target_dir}': {e}")


    def parse_input(self) -> None:
        """
        Parse input files for genome mining and QUAST results.

        Raises:
            ValidationError: If required inputs are missing or invalid.
        """
        # TODO: move this part into the option_parser? There is a so-far-empty function
        # for validating input correctness
        if self.args.quast_output_dir and not self.args.reference_mining_result:
            error_message = (
                "The reference genome mining result is required in the compare-to-reference mode.\n"
                "Please specify it using --reference-mining-result FILE or -r FILE."
            )
            self.log.error(error_message)
            raise ValidationError(error_message)
        if not self.args.quast_output_dir and self.args.reference_mining_result:
            error_message = (
                "The QUAST output directory is required in the compare-to-reference mode.\n"
                "Please specify it using --quast-output-dir DIR or -q DIR."
            )
            self.log.error(error_message)
            raise ValidationError(error_message)

        # Prevent the usage of duplicates
        all_gm_paths = list(self.args.mining_results)
        if self.args.reference_mining_result is not None:
            all_gm_paths.append(self.args.reference_mining_result)

        input_utils.validate_no_duplicate_paths(
            all_gm_paths,
        )

        # Parse genome mining results.
        try:
            self.assembly_genome_mining_results = parse_input_mining_result_files(
                self.log, self.config, self.args.mining_results, self.args.genome_data
            )
        except Exception as e:
            self.log.error(f"Failed to parse genome mining results: {str(e)}")
            raise e

        # Parse QUAST results if provided.
        if self.args.quast_output_dir:
            try:
                self.quast_results = parse_quast_output_dir(self.args.quast_output_dir)
            except Exception as e:
                self.log.error(f"Failed to parse QUAST results: {str(e)}")
                raise e

        # Parse reference genome mining result if provided.
        if self.args.reference_mining_result:
            try:
                self.reference_genome_mining_result = (
                    parse_reference_genome_mining_result(
                        self.log,
                        self.config,
                        self.args.reference_mining_result,
                        self.args.reference_genome_data,
                    )
                )
            except Exception as e:
                self.log.error(
                    f"Failed to parse reference genome mining results: {str(e)}"
                )
                raise e

        # Set running mode based on the provided arguments.
        try:
            self.running_mode = input_utils.determine_running_mode(
                self.args.mode,
                self.reference_genome_mining_result,
                self.assembly_genome_mining_results,
                log=self.log,
            )
            self.label_renaming_log = input_utils.assign_and_deduplicate_display_labels(
                assembly_results=self.assembly_genome_mining_results,
                reference_result=self.reference_genome_mining_result,
                names_arg=self.args.names,
                ref_name=self.args.ref_name,
            )
        except ValidationError as e:
            # Log the specific message from determine_running_mode, then re-raise.
            self.log.error(str(e))
            raise

        self.log.info(f"The running mode is set to: {self.running_mode}")

    def compute_stats(self) -> None:
        """
        Compute statistics for the parsed results.
        """

        analysis_report = ReportBuilder(ReportConfigManager()).build_report(
            config=self.config,
            results=self.assembly_genome_mining_results,
            running_mode=self.running_mode,  # type: ignore
            quast_results=self.quast_results,
            reference_genome_mining_result=self.reference_genome_mining_result,
            label_renaming_log=getattr(self, "label_renaming_log", []),
            requested_mode=self.args.mode,
        )

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
            self.config.output_config.tsv_report,
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
        self.log.info(
            f"TSV report is saved to {self.config.output_config.tsv_report}",
            indent=1,
        )

        # Log file label renamings (if any)
        renaming_log = self.analysis_report.metadata.get("label_renaming_log") or []
        if renaming_log:
            self.log.info(
                "Some input files had identical labels and were renamed "
                "in the report to avoid ambiguity:",
                indent=1,
            )
            for entry in renaming_log:
                path = entry.get("path", "<unknown path>")
                old_label = entry.get("old_label", "<unknown>")
                new_label = entry.get("new_label", "<unknown>")
                self.log.info(
                    f"{path}: '{old_label}' ===> '{new_label}'",
                    indent=2,
                )

        self.log.finish()  # TODO: Create a separate method for this and "cleaning up"
