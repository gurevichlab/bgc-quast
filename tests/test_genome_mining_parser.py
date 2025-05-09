import os
from pathlib import Path

import pytest
from src.config import load_config
from src.genome_mining_parser import (
    InvalidInputException,
    parse_antismash_json,
    parse_deepbgc_json,
    parse_deepbgc_tsv,
    parse_gecco_tsv,
    parse_input_files,
    parse_quast_output_dir,
)
from src.genome_mining_result import AlignmentInfo

# Get the test data directory path - one level up from tests directory
TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
ANTISMASH_FILE = (
    TEST_DATA_DIR / "assembly_10_mining" / "antiSMASH" / "assembly_10.json.gz"
)
GECCO_FILE = (
    TEST_DATA_DIR / "assembly_10_mining" / "GECCO" / "assembly_10.fasta.clusters.tsv"
)
DEEPBGC_TSV_FILE = TEST_DATA_DIR / "assembly_10_mining" / "deepBGC" / "deepBGC.bgc.tsv"
DEEPBGC_JSON_FILE = (
    TEST_DATA_DIR / "assembly_10_mining" / "deepBGC" / "deepBGC.antismash.json"
)
QUAST_DIR = TEST_DATA_DIR / "quast_out"


def test_parse_antismash_json_gzipped():
    """Test parsing a gzipped antiSMASH JSON file."""
    bgcs = parse_antismash_json(load_config(), ANTISMASH_FILE)

    # Verify we got some BGCs
    assert len(bgcs) == 6

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_2.1"
    assert bgc.sequence_id == "CONTIG_2"
    assert bgc.start == 0
    assert bgc.end == 39844
    assert bgc.product_types == ["PKS"]
    assert bgc.is_complete == "Unknown"


def test_parse_antismash_json_invalid_format():
    """Test parsing an invalid JSON file."""
    invalid_file = os.path.join(TEST_DATA_DIR, "invalid.json")
    with open(invalid_file, "w") as f:
        f.write("invalid json content")

    with pytest.raises(InvalidInputException) as exc_info:
        parse_antismash_json(load_config(), invalid_file)
    assert "Failed to parse antiSMASH format" in str(exc_info.value)

    # Clean up
    if os.path.exists(invalid_file):
        os.remove(invalid_file)


def test_parse_gecco_tsv():
    """Test parsing a GECCO TSV file."""
    bgcs = parse_gecco_tsv(load_config(), GECCO_FILE)

    # Verify we got some BGCs
    assert len(bgcs) == 6

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_1_1"
    assert bgc.sequence_id == "CONTIG_1"
    assert bgc.start == 1144
    assert bgc.end == 42174
    assert bgc.product_types == ["Unknown"]
    assert bgc.is_complete == "Unknown"


def test_parse_deepbgc_tsv():
    """Test parsing a deepBGC TSV file."""
    bgcs = parse_deepbgc_tsv(load_config(), DEEPBGC_TSV_FILE)

    # Verify we got some BGCs
    assert len(bgcs) == 40

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_1_1"
    assert bgc.sequence_id == "CONTIG_1"
    assert bgc.start == 1143
    assert bgc.end == 9307
    assert bgc.product_types == ["Unknown"]
    assert bgc.is_complete == "Unknown"


def test_parse_deepbgc_json():
    """Test parsing a deepBGC JSON file."""
    bgcs = parse_deepbgc_json(load_config(), DEEPBGC_JSON_FILE)

    # Verify we got some BGCs
    assert len(bgcs) == 40

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_1_1"
    assert bgc.sequence_id == "CONTIG_1"
    assert bgc.start == 1143
    assert bgc.end == 9307
    assert bgc.product_types == ["Unknown"]
    assert bgc.is_complete == "Unknown"


def test_parse_quast_output_dir_valid_file():
    """Test parsing a valid QUAST output directory."""
    quast_results = parse_quast_output_dir(QUAST_DIR)

    # Verify we got some results
    assert len(quast_results) == 2

    # Test the first result
    quast_result = quast_results[0]
    if quast_result.input_file_label != "assembly_10":
        quast_result = quast_results[1]

    assert quast_result.input_dir == QUAST_DIR
    assert quast_result.input_file_label == "assembly_10"
    assert len(quast_result.assembly_sequences) == 10
    assert len(quast_result.reference_sequences) == 1
    assert quast_result.assembly_sequences["CONTIG_2"] == [
        AlignmentInfo(
            assembly_seq_id="CONTIG_2",
            ref_seq_id="NC_003888.3",
            ref_start=99811,
            ref_end=199986,
            assembly_start=1,
            assembly_end=100176,
            len_diff=0,
        )
    ]


def test_parse_quast_output_dir_invalid_file():
    with pytest.raises(InvalidInputException) as exc_info:
        parse_quast_output_dir(Path("dummy_dir"))
    assert "Failed to parse QUAST output directory" in str(exc_info.value)
    assert "QUAST output directory does not exist" in str(exc_info.value)


def test_parse_input_files_invalid_file():
    with pytest.raises(InvalidInputException) as exc_info:
        parse_input_files(load_config(), ["dummy_path.json"])
    assert "Could not parse file dummy_path.json with any available parser" in str(
        exc_info.value
    )


def test_parse_input_files_valid_file():
    """Test parsing a valid input file."""
    # Assuming the test data directory contains a valid antiSMASH JSON file

    # Parse the input files
    results = parse_input_files(load_config(), [ANTISMASH_FILE])

    # Verify we got some results
    assert len(results) == 1
    assert results[0].input_file == ANTISMASH_FILE
    assert results[0].input_file_label == "assembly_10"
    assert results[0].mining_tool == "antiSMASH"
    assert len(results[0].bgcs) == 6
