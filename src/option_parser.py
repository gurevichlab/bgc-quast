from pathlib import Path
import argparse
from argparse import Namespace as CommandLineArgs
from src.config import Config
from io import StringIO


def add_basic_arguments(parser: argparse.ArgumentParser, default_cfg: Config):
    # These go directly into the main group (not a separate argument group)
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        metavar='DIR',
        help="Output directory "
             f"[default: {default_cfg.output_config.output_dir.parent}/" "{CURRENT_TIME}]"
    )
    parser.add_argument(
        '--threads', '-t',
        default=1,
        type=int,
        metavar='INT',
        help="Number of threads [default: %(default)s]",
        action='store'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='Run in debug mode and keep all intermediate files'
    )

    # Add positional arguments: genome mining results (at least one required)
    parser.add_argument(
        'mining_results',
        type=Path,
        nargs='+',
        metavar='GENOME_MINING_RESULT',
        help='Paths to genome mining results (antiSMASH, GECCO, or deepBGC); '
             'at least one is required'
    )


def add_advanced_arguments(parser: argparse.ArgumentParser):
    advanced_input_group = parser.add_argument_group('Advanced input', 'TBA')
    advanced_input_group.add_argument(
        '--quast-output-dir',
        help="QUAST output in the reference-based evaluation mode; if specified, it is expected that the "
             "genome mining results are provided for both the reference and the assembly",
        metavar='DIR',
        action='store',
        type=Path
    )


def build_cmdline_args_parser(default_cfg: Config) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='BGC-QUAST: quality assessment tool for genome mining (BGC prediction) software'
    )
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
    if None:  # TODO if applicable
        raise ValidationError('something is wrong!')
