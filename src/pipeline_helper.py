from src.option_parser import (
    CommandLineArgs,
    get_command_line_args,
    ValidationError
)
from src.logger import Logger
from src.config import Config, load_config


class PipelineHelper:
    config: Config
    args: CommandLineArgs
    log: Logger

    def __init__(self, log: Logger):
        self.log = log

        default_cfg = load_config()
        try:
            self.args = get_command_line_args(default_cfg)
        except ValidationError as e:
            self.log.error(str(e), to_stderr=True)
            raise e

        try:
            self.config = load_config(self.args)
        except ValueError as e:
            self.log.error(str(e), to_stderr=True)
            raise e
        self.set_up_output_dir()

        self.log.set_up_file_handler(self.config.output_config.output_dir)
        self.log.start()

        # shutil.copytree(self.config.configs_dir, self.config.output_config.configs_output, copy_function=shutil.copy)

    def set_up_output_dir(self):
        if self.config.output_config.output_dir.exists():
            self.log.warning(f'output directory ({self.config.output_config.output_dir}) already exists! '
                             f'The content will be overwritten')
        else:
            self.config.output_config.output_dir.mkdir(parents=True)

        # TODO: create 'latest' symlink if needed (default output dir with timestamp)

    def parse_input(self):
        # TODO: handle all kind of inputs:
        # E.g., genome mining results (antiSMASH vs GECCO vs deepBGC) vs QUAST results ve etc
        pass

    def write_results(self):
        self.log.info("RESULTS:")
        self.log.info("Text report is saved to " + str(self.config.output_config.report), indent=1)
        self.log.info("HTML report is saved to " + str(self.config.output_config.html_report), indent=1)
        # TODO: actually write something to the specified reports

        self.log.finish()  # TODO: create a separate method for this and "cleaning up"


