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


# Tests
def test_parse_antismash_json_not_implemented():
    with pytest.raises(InvalidInputException) as exc_info:
        parse_antismash_json("dummy_path.json")
    assert "Failed to parse Antismash format" in str(exc_info.value)
    assert "not implemented" in str(exc_info.value).lower()


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


def test_parse_input_files_not_implemented():
    with pytest.raises(InvalidInputException) as exc_info:
        parse_input_files(["dummy_path.json"])
    assert "Could not parse file dummy_path.json with any available parser" in str(
        exc_info.value
    )
