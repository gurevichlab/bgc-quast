import os

import pytest
from src.genome_mining_parser import (
    InvalidInputException,
    parse_antismash_json,
    parse_deepbgc_json,
    parse_deepbgc_tsv,
    parse_gecco_tsv,
    parse_input_files,
    parse_quast_output_dir,
)

# Get the test data directory path - one level up from tests directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "test_data")
ANTISMASH_FILE = os.path.join(
    TEST_DATA_DIR, "assembly_10_mining", "antiSMASH", "assembly_10.json.gz"
)


def test_parse_antismash_json_gzipped():
    """Test parsing a gzipped antiSMASH JSON file."""
    bgcs = parse_antismash_json(ANTISMASH_FILE)

    # Verify we got some BGCs
    assert len(bgcs) == 6

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_2.1"
    assert bgc.sequence_id == "CONTIG_2"
    assert bgc.start == 0
    assert bgc.end == 39844
    assert bgc.product_types == ["hglE-KS"]
    assert bgc.is_complete == "False"


def test_parse_antismash_json_invalid_format():
    """Test parsing an invalid JSON file."""
    invalid_file = os.path.join(TEST_DATA_DIR, "invalid.json")
    with open(invalid_file, "w") as f:
        f.write("invalid json content")

    with pytest.raises(InvalidInputException) as exc_info:
        parse_antismash_json(invalid_file)
    assert "Failed to parse antiSMASH format" in str(exc_info.value)

    # Clean up
    if os.path.exists(invalid_file):
        os.remove(invalid_file)


def test_parse_gecco_tsv_not_implemented():
    with pytest.raises(InvalidInputException) as exc_info:
        parse_gecco_tsv("dummy_path.tsv")
    assert "Failed to parse GECCO TSV format" in str(exc_info.value)
    assert "not implemented" in str(exc_info.value).lower()


def test_parse_deepbgc_tsv_not_implemented():
    with pytest.raises(InvalidInputException) as exc_info:
        parse_deepbgc_tsv("dummy_path.tsv")
    assert "Failed to parse deepBGC TSV format" in str(exc_info.value)
    assert "not implemented" in str(exc_info.value).lower()


def test_parse_deepbgc_json_not_implemented():
    with pytest.raises(InvalidInputException) as exc_info:
        parse_deepbgc_json("dummy_path.json")
    assert "Failed to parse deepBGC JSON format" in str(exc_info.value)
    assert "not implemented" in str(exc_info.value).lower()


def test_parse_quast_output_dir_not_implemented():
    with pytest.raises(InvalidInputException) as exc_info:
        parse_quast_output_dir("dummy_dir")
    assert "Failed to parse QUAST output directory" in str(exc_info.value)
    assert "not implemented" in str(exc_info.value).lower()


def test_parse_input_files_invalid_file():
    with pytest.raises(InvalidInputException) as exc_info:
        parse_input_files(["dummy_path.json"])
    assert "Could not parse file dummy_path.json with any available parser" in str(
        exc_info.value
    )

def test_parse_input_files_valid_file():
    """Test parsing a valid input file."""
    # Assuming the test data directory contains a valid antiSMASH JSON file
    valid_file = os.path.join(TEST_DATA_DIR, "assembly_10_mining", "antiSMASH", "assembly_10.json.gz")
    
    # Parse the input files
    results = parse_input_files([valid_file])
    
    # Verify we got some results
    assert len(results) == 1
    assert results[0].input_file == valid_file
    assert results[0].mining_tool == "antiSMASH"
    assert len(results[0].bgcs) == 6