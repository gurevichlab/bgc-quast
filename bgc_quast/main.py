import sys
from bgc_quast.logger import Logger
from bgc_quast.pipeline_helper import PipelineHelper


def run(log: Logger):
    """
    Run BGC-QUAST pipeline step by step.
    log is passed as an argument to make it easier to write log in case of exception.
    """
    pipeline_helper = PipelineHelper(log)
    pipeline_helper.parse_input()
    pipeline_helper.compute_stats()
    pipeline_helper.write_results()


def main() -> int:
    """
    Main entry point function. Sets up logger and handles top-level exceptions.
    Returns 0 on success, 1 on failure.
    """
    log = Logger()
    try:
        run(log)
        return 0
    except Exception as e:
        _, exc_value, _ = sys.exc_info()
        log.exception(exc_value)
        return 1
    finally:
        # TODO: clean up: remove all intermediate files
        pass


if __name__ == "__main__":
    sys.exit(main())
