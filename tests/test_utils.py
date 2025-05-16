import pytest
from src.genome_mining_result import GenomeMiningResult
from src.report import RunningMode
from src.utils import determine_running_mode


def test_determine_running_mode_compare_to_reference():
    """Test running mode when a reference mining result is provided."""
    reference_result = GenomeMiningResult(
        input_file="ref.json", input_file_label="ref", mining_tool="tool1"
    )
    genome_results = [
        GenomeMiningResult(
            input_file="sample1.json", input_file_label="sample1", mining_tool="tool1"
        ),
        GenomeMiningResult(
            input_file="sample2.json", input_file_label="sample2", mining_tool="tool1"
        ),
    ]

    mode = determine_running_mode(reference_result, genome_results)
    assert mode == RunningMode.COMPARE_TO_REFERENCE


def test_determine_running_mode_compare_tools():
    """Test running mode when comparing tools with the same input file label."""
    genome_results = [
        GenomeMiningResult(
            input_file="sample1.json", input_file_label="label1", mining_tool="tool1"
        ),
        GenomeMiningResult(
            input_file="sample1.json", input_file_label="label1", mining_tool="tool2"
        ),
    ]

    mode = determine_running_mode(None, genome_results)
    assert mode == RunningMode.COMPARE_TOOLS


def test_determine_running_mode_compare_samples():
    """Test running mode when comparing samples with the same mining tool."""
    genome_results = [
        GenomeMiningResult(
            input_file="sample1.json", input_file_label="label1", mining_tool="tool1"
        ),
        GenomeMiningResult(
            input_file="sample2.json", input_file_label="label2", mining_tool="tool1"
        ),
    ]

    mode = determine_running_mode(None, genome_results)
    assert mode == RunningMode.COMPARE_SAMPLES


def test_determine_running_mode_unknown():
    """Test running mode when input file labels and mining tools are different."""
    genome_results = [
        GenomeMiningResult(
            input_file="sample1.json", input_file_label="label1", mining_tool="tool1"
        ),
        GenomeMiningResult(
            input_file="sample2.json", input_file_label="label2", mining_tool="tool2"
        ),
    ]

    mode = determine_running_mode(None, genome_results)
    assert mode == RunningMode.UNKNOWN
