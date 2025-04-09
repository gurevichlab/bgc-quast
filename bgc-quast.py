#!/usr/bin/env python3

import sys
from src.logger import Logger
from src.pipeline_helper import PipelineHelper


def main(log: Logger):  # log is passed as an argument to make it easier to write log in case of exception
    pipeline_helper = PipelineHelper(log)

    pipeline_helper.parse_input()
    pipeline_helper.compute_stats()
    pipeline_helper.write_results()


if __name__ == "__main__":
    log = Logger()
    try:
        main(log)
    except Exception as e:
        _, exc_value, _ = sys.exc_info()
        log.exception(exc_value)
    finally:
        # TODO: clean up: remove all intermediate files
        pass
