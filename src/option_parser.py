from pathlib import Path
import argparse
from argparse import Namespace as CommandLineArgs
from src.config import Config
from io import StringIO
import textwrap

class WrapPreserveNewlinesHelpFormatter(argparse.HelpFormatter):
    def _split_lines(self, text: str, width: int):
        # Wrap each existing line separately, preserving manual newlines
        lines = []
        for line in text.splitlines() or [""]:
            if not line.strip():
                lines.append("")
            else:
                lines.extend(textwrap.wrap(line, width))
        return lines

def formatter(prog: str) -> argparse.HelpFormatter:
    return WrapPreserveNewlinesHelpFormatter(
        prog,
        max_help_position=32,
        width=100,
    )

def add_basic_arguments(parser: argparse.ArgumentParser, default_cfg: Config):
    # Positional argument
    parser.add_argument(
        "mining_results",
        type=Path,
        nargs="+",
        metavar="GENOME_MINING_RESULT",
        help="Paths to genome mining results (antiSMASH, GECCO, or deepBGC); at least one is required",
    )

    basic = parser.add_argument_group("Basic options")

    basic.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        metavar="DIR",
        help="Output directory "
             f"[default: {default_cfg.output_config.output_dir.parent}/"
             "{CURRENT_TIME}]",
    )

    basic.add_argument(
        "--min-bgc-length",
        type=int,
        metavar="INT",
        default=None,
        help=(
            "Minimum BGC length in bp. BGCs shorter than this threshold are "
            "filtered out from all analyses [default: 0]"
        ),
    )

    basic.add_argument(
        "--edge-distance",
        dest="bgc_completeness_margin",
        metavar="INT",
        type=int,
        help="Margin (in bp) from contig edges used to classify BGC completeness [default: 100]",
    )

    basic.add_argument(
        "--mode",
        choices=["auto", "compare-to-reference", "compare-tools", "compare-samples"],
        default="auto",
        help=(
            "Running mode that controls how BGC-QUAST interprets the inputs.\n"
            "  - auto (default): Infer the mode from provided files\n"
            "  - compare-to-reference: Assess how well BGCs predicted on draft assemblies "
            "match the predictions from a high-quality reference genome. (!) Requires "
            "reference mining result and  QUAST output.\n"
            "  - compare-tools: Compare different genome mining tools run on the same genome sequence "
            "(supports multiple runs from the same tool).\n"
            "  - compare-samples: Summarize BGC predictions from a single genome mining tool across multiple genomes. "
            "Doesn't require any specific options."
        ),
    )

    basic.add_argument(
        "--genome",
        "-g",
        help=(
            "Path to the genome FASTA or GenBank file; if genome mining results are provided for multiple "
            "genomes, this argument can accept multiple paths."
        ),
        metavar="FILE",
        nargs="*",
        dest="genome_data",
        type=Path,
    )

    basic.add_argument(
        "--names",
        type=str,
        default=None,
        metavar="NAME1,NAME2",
        nargs="*",
        help=(
            "Custom names for the input genome mining results in reports.\n"
            "Comma-separated; use quotes if names contain spaces. "
            "The number of names must match the number of genome mining results files."
        ),
    )

    basic.add_argument(
        "--threads",
        "-t",
        default=1,
        type=int,
        metavar="INT",
        help="Number of threads [default: %(default)s]",
        action="store",
    )

    basic.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Run in debug mode and keep all intermediate files",
    )

def add_mode_specific_arguments(parser: argparse.ArgumentParser):
    parser.add_argument_group("Mode-specific options")

    compare_ref = parser.add_argument_group("Compare-to-reference")
    compare_ref.add_argument(
        "--reference-mining-result",
        "-r",
        help="Path to the reference genome mining result (antiSMASH, GECCO, or deepBGC); "
             "required if --quast-output-dir is specified",
        metavar="REFERENCE_GENOME_MINING_RESULT",
        action="store",
        type=Path,
    )

    compare_ref.add_argument(
        "--quast-output-dir",
        "-q",
        help="QUAST output in the reference-based evaluation mode; if specified, it is expected that the "
             "genome mining results are provided for both the reference and the assembly; "
             "required if --reference-mining-result is specified",
        metavar="DIR",
        action="store",
        type=Path,
    )

    compare_ref.add_argument(
        "--reference-genome",
        "-R",
        help="Path to the reference genome FASTA or GenBank file.",
        metavar="REFERENCE_GENOME",
        dest="reference_genome_data",
        nargs="?",
        type=Path,
    )

    compare_ref.add_argument(
        "--ref-name",
        type=str,
        default=None,
        help="Custom name for the reference genome mining result in reports (only if reference is provided).",
    )

    compare_tools = parser.add_argument_group("Compare-tools")
    compare_tools.add_argument(
        "--overlap-threshold",
        dest="compare_tools_overlap_threshold",
        type=float,
        metavar="FLOAT",
        default=None,
        help="BGC overlap threshold percentage in (0,1] for COMPARE-TOOLS mode [default: 0.9]",
    )

def add_other_arguments(parser: argparse.ArgumentParser):
    other = parser.add_argument_group("Other options")
    other.add_argument(
        "-h", "--help",
        action="help",
        help="show this help message and exit",
    )


def build_cmdline_args_parser(default_cfg: Config) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        add_help=False,  # prevents argparse from creating the default "options:"
        formatter_class=formatter,
        description="BGC-QUAST: quality assessment tool for genome mining (BGC prediction) software",
        usage=(
             "bgc-quast.py [-h] [--output-dir DIR] [--threads INT] [--mode {auto,compare-to-reference,compare-tools,compare-samples}] "
            "[--min-bgc-length INT] [--names NAME1,NAME2 ...] [--genome FILE ...] "
            "[mode-specific options] <GENOME_MINING_RESULT>"
        ),
    )

    add_basic_arguments(parser, default_cfg)
    add_mode_specific_arguments(parser)
    add_other_arguments(parser)

    return parser


def get_command_line_args(default_cfg: Config) -> CommandLineArgs:
    parser = build_cmdline_args_parser(default_cfg)
    parsed_args = parser.parse_args()
    try:
        validate_arguments(parsed_args)
    except ValidationError as e:
        help_message = StringIO()
        parser.print_help(help_message)
        error_message = str(e) if str(e) else "Options validation failed!"
        raise ValidationError(error_message + "\n\n" + help_message.getvalue())
    return parsed_args


class ValidationError(Exception):
    pass


def validate(expr, msg=""):
    if not expr:
        raise ValidationError(msg)


def validate_arguments(args: CommandLineArgs):
    if None:  # TODO if applicable
        raise ValidationError("something is wrong!")
    thr = getattr(args, "compare_tools_overlap_threshold", None)
    if thr is not None:
        validate(0.0 <= thr <= 1.0,
                 "--overlap-threshold must be between 0 and 1")

    min_len = getattr(args, "min_bgc_length", None)
    if min_len is not None:
        validate(
            min_len >= 0,
            "--min-bgc-length must not be a negative integer",
        )
    if getattr(args, "ref_name", None) and not getattr(args, "reference_mining_result", None):
        raise ValidationError(
            "--ref-name was provided but no reference genome mining result was specified. "
            "Please use --reference-mining-result together with --ref-name."
        )
