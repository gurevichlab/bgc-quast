from pathlib import Path
import argparse
from argparse import Namespace as CommandLineArgs
from src.config import Config
from io import StringIO


def add_basic_arguments(parser: argparse.ArgumentParser, default_cfg: Config):
    # These go directly into the main group (not a separate argument group)
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        metavar="DIR",
        help="Output directory "
        f"[default: {default_cfg.output_config.output_dir.parent}/"
        "{CURRENT_TIME}]",
    )
    parser.add_argument(
        "--threads",
        "-t",
        default=1,
        type=int,
        metavar="INT",
        help="Number of threads [default: %(default)s]",
        action="store",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Run in debug mode and keep all intermediate files",
    )

    # Add positional arguments: genome mining results (at least one required)
    parser.add_argument(
        "mining_results",
        type=Path,
        nargs="+",
        metavar="GENOME_MINING_RESULT",
        help="Paths to genome mining results (antiSMASH, GECCO, or deepBGC); "
        "at least one is required",
    )

    parser.add_argument(
        "--mode",
        choices=["auto", "compare-reference", "compare-tools", "compare-samples"],
        default="auto",
        help=(
            "Running mode that controls how BGC-QUAST interprets the inputs. "
            "'auto' (default) tries to infer the mode from the provided files. "
            "'compare-reference' expects reference genome mining result plus QUAST output."
            "'compare-tools' compares genome mining tools, "
            "including multiple runs from the same tool. "
            "'compare-samples' compares assemblies mined with a single tool."
        ),
    )


def add_advanced_arguments(parser: argparse.ArgumentParser):
    advanced_input_group = parser.add_argument_group("Advanced input", "TBA")

    advanced_input_group.add_argument(
        "--min-bgc-length",
        type=int,
        metavar='INT',
        default=None,
        help=(
            "Minimum BGC length in bp. BGCs shorter than this threshold are "
            "filtered out from all analyses (default: 0)"
        ),
    )

    advanced_input_group.add_argument(
        "--quast-output-dir",
        "-q",
        help="QUAST output in the reference-based evaluation mode; if specified, it is expected that the "
        "genome mining results are provided for both the reference and the assembly; "
        "required if --reference-mining-result is specified",
        metavar="DIR",
        action="store",
        type=Path,
    )

    advanced_input_group.add_argument(
        "--reference-mining-result",
        "-r",
        help="Path to the reference genome mining result (antiSMASH, GECCO, or deepBGC); "
        "required if --quast-output-dir is specified",
        metavar="REFERENCE_GENOME_MINING_RESULT",
        action="store",
        type=Path,
    )

    advanced_input_group.add_argument(
        "--genome",
        "-g",
        help="Path to the genome FASTA or GenBank file; "
        "if genome mining results are provided for multiple genomes, "
        "this argument can accept multiple paths.",
        metavar="GENOME",
        nargs="*",
        dest="genome_data",
        type=Path,
    )

    advanced_input_group.add_argument(
        "--reference-genome",
        "-R",
        help="Path to the reference genome FASTA or GenBank file.",
        metavar="REFERENCE_GENOME",
        dest="reference_genome_data",
        nargs="?",
        type=Path,
    )

    advanced_input_group.add_argument(
        "--overlap-threshold",
        dest="compare_tools_overlap_threshold",
        type=float,
        metavar='FLOAT',
        default=None,
        help="BGC overlap threshold in (0,1] for COMPARE-TOOLS mode (default: 0.9)",
    )

    advanced_input_group.add_argument(
        "--edge-distance",
        dest="bgc_completeness_margin",
        metavar='INT',
        type=int,
        help="Margin (in bp) from contig edges used to classify BGC completeness (default: 100)",
    )


def build_cmdline_args_parser(default_cfg: Config) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="BGC-QUAST: quality assessment tool for genome mining (BGC prediction) software",
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
        error_message = str(e) if str(e) else "Options validation failed!"
        raise ValidationError(error_message + "\n" + help_message.getvalue())
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
                 "--compare-tools-overlap-threshold must be between 0 and 1")

    min_len = getattr(args, "min_bgc_length", None)
    if min_len is not None:
        validate(
            min_len >= 0,
            "--min-bgc-length must not be a negative integer",
        )