from pathlib import Path

import pytest

from bgc_quast.config import load_config
from bgc_quast.option_parser import build_cmdline_args_parser


@pytest.fixture
def parser():
    return build_cmdline_args_parser(load_config())


def test_parse_single_genome_argument(parser):
    args = parser.parse_args(
        [
            "result.json",
            "-G",
            "genome.fasta",
        ]
    )

    assert args.mining_results == [Path("result.json")]
    assert args.genome_data == [Path("genome.fasta")]


def test_parse_repeated_genome_arguments(parser):
    args = parser.parse_args(
        [
            "result_1.json",
            "result_2.json",
            "-G",
            "genome_1.fasta",
            "-G",
            "genome_2.gbff",
        ]
    )

    assert args.mining_results == [
        Path("result_1.json"),
        Path("result_2.json"),
    ]
    assert args.genome_data == [
        Path("genome_1.fasta"),
        Path("genome_2.gbff"),
    ]


def test_parse_without_genome_argument(parser):
    args = parser.parse_args(["result.json"])

    assert args.mining_results == [Path("result.json")]
    assert args.genome_data is None