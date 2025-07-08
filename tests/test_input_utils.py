from pathlib import Path

import pytest
from src.config import Config
from src.genome_mining_result import GenomeMiningResult
from src.input_utils import (
    determine_running_mode,
    get_file_label_from_path,
)
from src.report import RunningMode

SAMPLE_PATH_1 = Path("sample1.json")
SAMPLE_PATH_2 = Path("sample2.json")
REFERENCE_PATH = Path("reference.json")


def test_determine_running_mode_compare_to_reference():
    """Test running mode when a reference mining result is provided."""
    reference_result = GenomeMiningResult(
        input_file=REFERENCE_PATH, input_file_label="ref", mining_tool="tool1"
    )
    genome_results = [
        GenomeMiningResult(
            input_file=SAMPLE_PATH_1, input_file_label="sample1", mining_tool="tool1"
        ),
        GenomeMiningResult(
            input_file=SAMPLE_PATH_1, input_file_label="sample1", mining_tool="tool1"
        ),
    ]

    mode = determine_running_mode(reference_result, genome_results)
    assert mode == RunningMode.COMPARE_TO_REFERENCE


def test_determine_running_mode_different_labels_with_reference_unknown():
    """Test running mode when a reference mining result is provided."""
    reference_result = GenomeMiningResult(
        input_file=REFERENCE_PATH, input_file_label="ref", mining_tool="tool1"
    )
    genome_results = [
        GenomeMiningResult(
            input_file=SAMPLE_PATH_1, input_file_label="sample1", mining_tool="tool1"
        ),
        GenomeMiningResult(
            input_file=SAMPLE_PATH_2, input_file_label="sample2", mining_tool="tool1"
        ),
    ]

    mode = determine_running_mode(reference_result, genome_results)
    assert mode == RunningMode.UNKNOWN


def test_determine_running_mode_one_genome_result_compare_samples():
    """Test running mode compare samples with one genome result."""
    genome_results = [
        GenomeMiningResult(
            input_file=SAMPLE_PATH_1, input_file_label="label1", mining_tool="tool1"
        ),
    ]

    mode = determine_running_mode(None, genome_results)
    assert mode == RunningMode.COMPARE_SAMPLES


def test_determine_running_mode_compare_tools():
    """Test running mode when comparing tools with the same input file label."""
    genome_results = [
        GenomeMiningResult(
            input_file=SAMPLE_PATH_1, input_file_label="label1", mining_tool="tool1"
        ),
        GenomeMiningResult(
            input_file=SAMPLE_PATH_1, input_file_label="label1", mining_tool="tool2"
        ),
    ]

    mode = determine_running_mode(None, genome_results)
    assert mode == RunningMode.COMPARE_TOOLS


def test_determine_running_mode_compare_samples():
    """Test running mode when comparing samples with the same mining tool."""
    genome_results = [
        GenomeMiningResult(
            input_file=SAMPLE_PATH_1, input_file_label="label1", mining_tool="tool1"
        ),
        GenomeMiningResult(
            input_file=SAMPLE_PATH_2, input_file_label="label2", mining_tool="tool1"
        ),
    ]

    mode = determine_running_mode(None, genome_results)
    assert mode == RunningMode.COMPARE_SAMPLES


def test_determine_running_mode_different_labels_and_tools_unknown():
    """Test running mode when input file labels and mining tools are different."""
    genome_results = [
        GenomeMiningResult(
            input_file=SAMPLE_PATH_1, input_file_label="label1", mining_tool="tool1"
        ),
        GenomeMiningResult(
            input_file=SAMPLE_PATH_2, input_file_label="label2", mining_tool="tool2"
        ),
    ]

    mode = determine_running_mode(None, genome_results)
    assert mode == RunningMode.UNKNOWN


@pytest.mark.parametrize(
    "filename,expected",
    [
        (Path("example.txt.gz"), "example"),
        (Path("kittens.fastq"), "kittens"),
        (Path("best.sample.json"), "best.sample"),
        (Path("archive.tar.bz2"), "archive"),
        (Path("foo.bar.bgzf"), "foo"),
        (Path("plainfile"), "plainfile"),
    ],
)
def test_get_file_label_from_path(tmp_path, filename, expected):
    # Create a dummy file at the given path
    file_path = tmp_path / filename
    file_path.touch()
    assert get_file_label_from_path(file_path) == expected
