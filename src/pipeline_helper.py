from typing import List, Optional
from src.option_parser import get_command_line_args, ValidationError
from src.logger import Logger
from src.config import load_config
from src.genome_mining_parser import (
    GenomeMiningResult,
    QuastResult,
    parse_input_files,
    parse_quast_output_dir,
)


class PipelineHelper:
    """
    A helper class to manage the BGC-QUAST pipeline.

    Attributes:
        config: Configuration object for the pipeline.
        args: Command-line arguments parsed into an object.
        log: Logger instance for logging operations.
        genome_mining_results: List of parsed genome mining results.
        reference_genome_mining_result: Parsed reference genome mining result.
        quast_results: List of parsed QUAST results.
    """

    def __init__(self, log: Logger):
        """
        Initialize the PipelineHelper.

        Args:
            log: Logger instance for logging operations.
        """
        self.log = log
        self.genome_mining_results: List[GenomeMiningResult] = []
        self.reference_mining_result: Optional[GenomeMiningResult] = None
        self.quast_results: Optional[List[QuastResult]] = None

        default_cfg = load_config()
        try:
            self.args = get_command_line_args(default_cfg)
        except ValidationError as e:
            self.log.error(
                f"Command-line argument validation failed: {str(e)}", to_stderr=True
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
            self.genome_mining_results = parse_input_files(self.config, self.args.mining_results)
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
                self.reference_mining_result = parse_input_files(self.config,
                    [self.args.reference_mining_result]
                )
            except Exception as e:
                self.log.error(
                    f"Failed to parse reference genome mining results: {str(e)}"
                )
                raise e


    def compute_stats(self) -> None:
        """
        Compute statistics for the parsed results.

        TODO: Implement this method.
        """
        pass

    def write_results(self) -> None:
        """
        Write the results of the pipeline to the output directory.

        Logs the locations of the text and HTML reports.
        """
        self.log.info("RESULTS:")
        self.log.info(
            f"Text report is saved to {self.config.output_config.report}", indent=1
        )
        self.log.info(
            f"HTML report is saved to {self.config.output_config.html_report}", indent=1
        )
        # TODO: Actually write something to the specified reports

        self.log.finish()  # TODO: Create a separate method for this and "cleaning up"
