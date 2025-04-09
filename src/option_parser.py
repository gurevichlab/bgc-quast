from pathlib import Path
import argparse
from argparse import Namespace as CommandLineArgs
from src.config import Config
from io import StringIO
import csv

def add_advanced_arguments(parser: argparse.ArgumentParser):
    advanced_input_group = parser.add_argument_group('Advanced input',
                                                     'TBA')
    advanced_input_group.add_argument("--quast-output-dir", help="QUAST output in the "
                                      "reference-based evaluation mode; if specified, it is expected that the "
                                      "genome mining results are provided for both the reference and the assembly",
                                      metavar='DIR', action="store", type=Path)


def add_basic_arguments(parser: argparse.ArgumentParser, default_cfg: Config):
    configs_group = parser.add_argument_group('BGC-QUAST pipeline',
                                              'TBA')

    configs_group.add_argument("--output-dir", "-o", type=Path, metavar='DIR',
                               help="output directory "
                                    f"[default: {default_cfg.output_config.output_dir.parent}/" "{CURRENT_TIME}]")
    configs_group.add_argument("--threads", "-t", default=1, type=int, metavar='INT',
                               help="number of threads [default: %(default)s]", action="store")
    configs_group.add_argument("--debug", action="store_true", default=False,
                               help="run in the debug mode and keep all intermediate files")


def build_cmdline_args_parser(default_cfg: Config) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    add_basic_arguments(parser, default_cfg)
    add_advanced_arguments(parser)
    return parser


def get_command_line_args(default_cfg: Config) -> CommandLineArgs:
    parser = build_cmdline_args_parser(default_cfg)
    parsed_args = parser.parse_args()
    try:
        validate_arguments(parsed_args)
    except ValidationError as e:
        help_message = StringIO()
        parser.print_help(help_message)
        error_message = str(e) if str(e) else 'Options validation failed!'
        raise ValidationError(error_message + '\n' + help_message.getvalue())
    return parsed_args


class ValidationError(Exception):
    pass


def validate(expr, msg=''):
    if not expr:
        raise ValidationError(msg)


def validate_arguments(args: CommandLineArgs):
    if None:  # TODO
        raise ValidationError('at least one genome mining tool output is required')
