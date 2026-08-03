import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from bgc_quast.config import Config, load_config
from bgc_quast.genome_mining_parser import (
    InvalidInputException,
    get_completeness,
    get_seq_data_map,
    parse_antismash_json,
    parse_deepbgc_json,
    parse_deepbgc_tsv,
    parse_gecco_tsv,
    parse_genome_data,
    parse_input_mining_result_files,
    parse_prism_json,
    parse_quast_output_dir,
    parse_reference_genome_mining_result,
)
from bgc_quast.genome_mining_result import AlignmentInfo, ContigData
from bgc_quast.logger import Logger

# Test data directory and constants
TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
ANTISMASH_FILE = (
    TEST_DATA_DIR / "assembly_10_mining" / "antiSMASH" / "assembly_10.json.gz"
)
GECCO_FILE = (
    TEST_DATA_DIR / "assembly_10_mining" / "GECCO" / "assembly_10.clusters.tsv"
)
DEEPBGC_TSV_FILE = TEST_DATA_DIR / "assembly_10_mining" / "DeepBGC" / "DeepBGC.bgc.tsv"
DEEPBGC_JSON_FILE = (
    TEST_DATA_DIR / "assembly_10_mining" / "DeepBGC" / "DeepBGC.antismash.json"
)
QUAST_DIR = TEST_DATA_DIR / "quast_out"
SEQ_DATA_MAP = {
    "contig_1": ContigData(seq_len=50000),
    "contig_2": ContigData(seq_len=50000),
}


@pytest.fixture
def logger():
    return Logger()


def test_parse_antismash_json_gzipped():
    """Test parsing a gzipped antiSMASH JSON file."""
    bgcs = parse_antismash_json(load_config(), ANTISMASH_FILE, SEQ_DATA_MAP)

    # Verify we got some BGCs
    assert len(bgcs) == 6

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_2.1"
    assert bgc.sequence_id == "CONTIG_2"
    assert bgc.start == 0
    assert bgc.end == 39844
    assert bgc.product_types == ["PKS"]
    assert bgc.completeness == "Incomplete"


def test_parse_antismash_json_gzipped_unknown_seq_length():
    """Test parsing a gzipped antiSMASH JSON file."""
    bgcs = parse_antismash_json(load_config(), ANTISMASH_FILE, None)

    # Verify we got some BGCs
    assert len(bgcs) == 6

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_2.1"
    assert bgc.sequence_id == "CONTIG_2"
    assert bgc.start == 0
    assert bgc.end == 39844
    assert bgc.product_types == ["PKS"]
    assert bgc.completeness == "Incomplete"


def test_parse_antismash_json_invalid_format():
    """Test parsing an invalid JSON file."""
    invalid_file = os.path.join(TEST_DATA_DIR, "invalid.json")
    with open(invalid_file, "w") as f:
        f.write("invalid json content")

    with pytest.raises(InvalidInputException) as exc_info:
        parse_antismash_json(load_config(), Path(invalid_file), SEQ_DATA_MAP)
    assert "Failed to parse antiSMASH format" in str(exc_info.value)

    # Clean up
    if os.path.exists(invalid_file):
        os.remove(invalid_file)


def test_parse_gecco_tsv():
    """Test parsing a GECCO TSV file."""
    bgcs = parse_gecco_tsv(load_config(), GECCO_FILE, SEQ_DATA_MAP)

    # Verify we got some BGCs
    assert len(bgcs) == 6

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_1_1"
    assert bgc.sequence_id == "CONTIG_1"
    assert bgc.start == 1143
    assert bgc.end == 42174
    assert bgc.product_types == ["Unknown product"]
    assert bgc.completeness == "Complete"


def test_parse_gecco_tsv_invalid_format(tmp_path):
    # Missing 'type' column
    tsv_content = "sequence_id\tcluster_id\tstart\tend\ncontig1\tcluster_1\t1\t1000\n"
    tsv_file = tmp_path / "invalid_gecco.tsv"
    tsv_file.write_text(tsv_content)
    with pytest.raises(InvalidInputException) as exc_info:
        parse_gecco_tsv(load_config(), tsv_file, None)
    assert "Not GECCO TSV" in str(exc_info.value)


def test_parse_deepbgc_tsv():
    """Test parsing a DeepBGC TSV file."""
    bgcs = parse_deepbgc_tsv(load_config(), DEEPBGC_TSV_FILE, SEQ_DATA_MAP)

    # Verify we got some BGCs
    assert len(bgcs) == 40

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_1_1"
    assert bgc.sequence_id == "CONTIG_1"
    assert bgc.start == 1143
    assert bgc.end == 9307
    assert bgc.product_types == ["Unknown product"]
    assert bgc.completeness == "Complete"


def test_parse_deepbgc_tsv_invalid_format(tmp_path):
    # Missing 'product_class' column
    tsv_content = "sequence_id\tnucl_start\tnucl_end\ncontig1\t1\t1000\n"
    tsv_file = tmp_path / "invalid_deepbgc.tsv"
    tsv_file.write_text(tsv_content)
    with pytest.raises(InvalidInputException) as exc_info:
        parse_deepbgc_tsv(load_config(), tsv_file, None)
    assert "Not DeepBGC TSV" in str(exc_info.value)


def test_parse_deepbgc_json():
    """Test parsing a DeepBGC JSON file."""
    bgcs = parse_deepbgc_json(load_config(), DEEPBGC_JSON_FILE, SEQ_DATA_MAP)

    # Verify we got some BGCs
    assert len(bgcs) == 40

    # Test the first BGC
    bgc = bgcs[0]

    assert bgc.bgc_id == "CONTIG_1_1"
    assert bgc.sequence_id == "CONTIG_1"
    assert bgc.start == 1143
    assert bgc.end == 9307
    assert bgc.product_types == ["Unknown product"]
    assert bgc.completeness == "Complete"


def test_parse_prism_json(tmp_path):
    """Test parsing PRISM JSON."""
    prism_file = tmp_path / "prism.json"
    prism_file.write_text(
        json.dumps(
            {
                "prism_results": {
                    "clusters": [
                        {
                            "contig": "contig1",
                            "start": 100,
                            "end": 500,
                            "type": ["PKS"],
                            "family": ["TYPE_I_POLYKETIDE"],
                        },
                        {
                            "contig": "contig1",
                            "start": 600,
                            "end": 900,
                            "type": ["PKS", "NRPS"],
                            "family": [
                                "TYPE_I_POLYKETIDE",
                                "NONRIBOSOMAL_PEPTIDE",
                            ],
                        },
                        {
                            "contig": "contig1",
                            "start": 1000,
                            "end": 1200,
                            "type": ["NULL"],
                            "family": ["NULL"],
                        },
                    ]
                }
            }
        )
    )

    seq_data_map = {
        "contig1": ContigData(
            seq_len=2000,
            genes=[
                (150, 250),
                (300, 400),
            ],
        )
    }

    bgcs = parse_prism_json(
        load_config(),
        prism_file,
        seq_data_map,
    )

    assert len(bgcs) == 3

    assert bgcs[0].sequence_id == "contig1"
    assert bgcs[0].start == 100
    assert bgcs[0].end == 500
    assert bgcs[0].product_types == ["PKS"]
    assert bgcs[0].gene_count == 2
    assert bgcs[0].completeness == "Complete"
    assert bgcs[0].metadata == {
        "product_details": ["PKS"],
        "product_family": ["TYPE_I_POLYKETIDE"],
    }

    assert set(bgcs[1].product_types) == {"PKS", "NRPS"}
    assert bgcs[2].product_types == ["Unknown product"]

def test_parse_prism_json_invalid_format(tmp_path):
    """Test that non-PRISM JSON is rejected."""
    prism_file = tmp_path / "invalid.json"
    prism_file.write_text(json.dumps({"records": []}))

    with pytest.raises(InvalidInputException):
        parse_prism_json(load_config(), prism_file, None)


def test_parse_deepbgc_json_invalid_format(tmp_path):
    # Not a valid JSON
    json_file = tmp_path / "invalid_deepbgc.json"
    json_file.write_text("not a json")
    with pytest.raises(InvalidInputException) as exc_info:
        parse_deepbgc_json(load_config(), json_file, None)
    assert "Failed to parse DeepBGC format" in str(exc_info.value)

def test_parse_deepbgc_json_missing_records(tmp_path):
    """Test that valid JSON without a records list is rejected."""
    json_file = tmp_path / "wrong_schema.json"
    json_file.write_text(
        json.dumps(
            {
                "prism_results": {
                    "clusters": []
                }
            }
        )
    )

    with pytest.raises(InvalidInputException) as exc_info:
        parse_deepbgc_json(load_config(), json_file, None)

    assert "'records' is missing or not a list" in str(exc_info.value)


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


def test_parse_input_files_invalid_file(tmp_path, logger):
    dummy_file = tmp_path / "dummy_path.json"
    dummy_file.touch()
    with pytest.raises(InvalidInputException) as exc_info:
        parse_input_mining_result_files(logger, load_config(), [dummy_file], None)
    assert (
        f"Could not parse file {dummy_file.as_posix()} with any available parser"
        in str(exc_info.value)
    )

def test_parse_input_files_valid_json_wrong_schema(tmp_path, logger):
    """Test that valid JSON with an unsupported structure is rejected."""
    json_file = tmp_path / "wrong_schema.json"
    json_file.write_text(
        json.dumps(
            {
                "unsupported_format": {
                    "predictions": []
                }
            }
        )
    )

    with pytest.raises(InvalidInputException) as exc_info:
        parse_input_mining_result_files(
            logger,
            load_config(),
            [json_file],
            None,
        )

    assert (
        f"Could not parse file {json_file.as_posix()} with any available parser"
        in str(exc_info.value)
    )


def test_parse_input_files_valid_file(logger):
    """Test parsing a valid input file."""
    results = parse_input_mining_result_files(
        logger, load_config(), [ANTISMASH_FILE], None
    )
    assert len(results) == 1
    assert results[0].input_file == ANTISMASH_FILE
    assert results[0].input_file_label == "assembly_10"
    assert results[0].mining_tool == "antiSMASH"
    assert len(results[0].bgcs) == 6


def test_parse_input_mining_result_files_mixed_seq_length_sources(tmp_path, logger):
    """
    Test parse_input_mining_result_files with:
    - one file using genome_data for seq length
    - one file using antiSMASH JSON for seq length
    - one file with no seq length info (should be None)
    """

    # 1. File with genome_data
    fasta_content = ">contigA\nATGCATGC\n"
    fasta_file = tmp_path / "file1.fasta"
    fasta_file.write_text(fasta_content)
    antismash_json1 = {
        "records": [
            {
                "id": "contigA",
                "features": [{"type": "region", "location": "[0:7]", "qualifiers": {}}],
            }
        ]
    }
    antismash_file1 = tmp_path / "file1.json"
    antismash_file1.write_text(json.dumps(antismash_json1))

    # 2. File with antiSMASH JSON only
    antismash_json2 = {
        "records": [
            {
                "id": "contigB",
                "seq": {"data": "ATGCAT"},
                "features": [{"type": "region", "location": "[0:5]", "qualifiers": {}}],
            }
        ]
    }
    antismash_file2 = tmp_path / "file2.json"
    antismash_file2.write_text(json.dumps(antismash_json2))

    # 3. Dummy genome file to prevent the "single genome fallback" behavior
    dummy_fasta = tmp_path / "dummy.fasta"
    dummy_fasta.write_text(">dummy\nATGC\n")

    # Call function
    results = parse_input_mining_result_files(
        logger,
        load_config(),
        [antismash_file1, antismash_file2, DEEPBGC_TSV_FILE],
        [fasta_file, dummy_fasta],
    )

    # Check seq length sources
    # file1: from genome_data
    r1 = next(r for r in results if r.input_file == antismash_file1)
    assert r1.genome_data["contiga"].seq_len == 8  # type: ignore

    # file2: from antiSMASH JSON
    r2 = next(r for r in results if r.input_file == antismash_file2)
    assert r2.genome_data["contigb"].seq_len == 6  # type: ignore

    # file3: None
    r3 = next(r for r in results if r.input_file == DEEPBGC_TSV_FILE)
    assert r3.genome_data is None


def test_parse_reference_genome_mining_result(tmp_path, logger):
    config = load_config()
    antismash_json = {
        "records": [
            {
                "id": "contig",
                "seq": {"data": "ATGC"},
                "features": [
                    {
                        "type": "region",
                        "location": "[0:3]",
                        "qualifiers": {},
                    }
                ],
            }
        ]
    }
    file = tmp_path / "antismash.json"
    file.write_text(json.dumps(antismash_json))
    result = parse_reference_genome_mining_result(logger, config, file, None)
    assert result.input_file == file
    assert result.input_file_label == file.stem
    assert result.mining_tool == "antiSMASH"
    assert len(result.bgcs) == 1


def test_parse_genome_data_fasta(tmp_path):
    """Test parsing genome data from a FASTA file."""
    fasta_content = ">contigA\nATGCATGCATGC\n>contigB\nATGCATGC\n"
    fasta_file = tmp_path / "test.fasta"
    fasta_file.write_text(fasta_content)
    result = parse_genome_data([fasta_file])
    label = fasta_file.stem
    assert label in result
    assert result[label]["contiga"].seq_len == 12
    assert result[label]["contigb"].seq_len == 8
    assert result[label]["contiga"].genes == []


def test_parse_genome_data_gbff(tmp_path):
    """Test parsing genome data from a GBFF file."""
    gbff_content = """LOCUS       contigC              20 bp    DNA     linear   01-JAN-1980
DEFINITION  dummy.
ACCESSION   contigC
FEATURES             Location/Qualifiers
     gene            1..5
     gene            10..15
ORIGIN
        1 atgcatgcat gcatgcatgc
//
LOCUS       contigD              10 bp    DNA     linear   01-JAN-1980
DEFINITION  dummy.
ACCESSION   contigD
ORIGIN
        1 atgcatgcat
//
"""
    gbff_file = tmp_path / "test.gbff"
    gbff_file.write_text(gbff_content)
    result = parse_genome_data([gbff_file])
    label = gbff_file.stem
    assert label in result
    assert result[label]["contigc"].seq_len == 20
    assert result[label]["contigd"].seq_len == 10
    assert result[label]["contigc"].genes == [(0, 5), (9, 15)]
    assert result[label]["contigd"].genes == []

def test_parse_genome_data_gbff_cds_only(tmp_path):
    """Test that CDS-only GenBank annotations are used as genes."""
    gbff_content = """LOCUS       contigE              20 bp    DNA     linear   01-JAN-1980
DEFINITION  dummy.
ACCESSION   contigE
FEATURES             Location/Qualifiers
     CDS             1..5
     CDS             10..15
ORIGIN
        1 atgcatgcat gcatgcatgc
//
"""
    gbff_file = tmp_path / "cds_only.gbff"
    gbff_file.write_text(gbff_content)

    result = parse_genome_data([gbff_file])
    label = gbff_file.stem

    assert result[label]["contige"].genes == [(0, 5), (9, 15)]


def test_parse_genome_data_gbff_deduplicates_gene_and_cds(tmp_path):
    """Test that matching gene and CDS features are counted only once."""
    gbff_content = """LOCUS       contigF              20 bp    DNA     linear   01-JAN-1980
DEFINITION  dummy.
ACCESSION   contigF
FEATURES             Location/Qualifiers
     CDS             16..18
     gene            1..5
     CDS             1..5
     gene            10..15
     CDS             10..15
ORIGIN
        1 atgcatgcat gcatgcatgc
//
"""
    gbff_file = tmp_path / "gene_and_cds.gbff"
    gbff_file.write_text(gbff_content)

    result = parse_genome_data([gbff_file])
    label = gbff_file.stem

    assert result[label]["contigf"].genes == [
        (0, 5),
        (9, 15),
        (15, 18),
    ]


def test_parse_genome_data_unsupported_extension(tmp_path):
    file = tmp_path / "test.unsupported"
    file.write_text(">seq1\nATGC")
    with pytest.raises(ValueError) as exc_info:
        parse_genome_data([file])
    assert "Unsupported file extension" in str(exc_info.value)


def test_get_seq_data_map_with_genome_seq_data_maps(tmp_path):
    genome_seq_data_maps = {"foo": {"contig": ContigData(seq_len=123)}}
    dummy_file = tmp_path / "foo.json"
    dummy_file.write_text(
        json.dumps(
            {"records": [{"id": "contig", "seq": {"data": "ATGC"}, "features": []}]}
        )
    )
    result = get_seq_data_map(genome_seq_data_maps, dummy_file)
    assert result["contig"].seq_len == 123  # type: ignore

def test_get_seq_data_map_prefers_original_label_over_alias(tmp_path):
    """The original mining-result basename must have priority over --names."""
    original_map = {"contig": ContigData(seq_len=111)}
    alias_map = {"contig": ContigData(seq_len=222)}

    mining_file = tmp_path / "assembly1.json"
    mining_file.write_text("{}")

    result = get_seq_data_map(
        {
            "assembly1": original_map,
            "a1": alias_map,
        },
        mining_file,
        matching_alias="a1",
    )

    assert result is original_map


def test_get_seq_data_map_uses_names_alias_as_fallback(tmp_path):
    """Use the corresponding --names value when the original label does not match."""
    alias_map = {"contig": ContigData(seq_len=123)}
    log = MagicMock(spec=Logger)

    mining_file = tmp_path / "DeepBGC.bgc.tsv"
    mining_file.write_text("")

    result = get_seq_data_map(
        {"assembly1": alias_map},
        mining_file,
        log=log,
        matching_alias="assembly1",
    )

    assert result is alias_map
    log.info.assert_called_once()
    assert "--names alias" in log.info.call_args.args[0]


def test_get_seq_data_map_warns_when_multiple_genomes_do_not_match(tmp_path):
    """Warn when neither the original label nor --names matches a genome."""
    log = MagicMock(spec=Logger)

    mining_file = tmp_path / "DeepBGC.bgc.tsv"
    mining_file.write_text("")

    result = get_seq_data_map(
        {
            "assembly1": {"contig1": ContigData(seq_len=100)},
            "assembly2": {"contig2": ContigData(seq_len=200)},
        },
        mining_file,
        log=log,
        matching_alias="wrong_name",
    )

    assert result is None
    log.warning.assert_called_once()

    warning_message = log.warning.call_args.args[0]
    assert "Could not associate genome mining result" in warning_message
    assert "DeepBGC" in warning_message
    assert "wrong_name" in warning_message
    assert "assembly1" in warning_message
    assert "assembly2" in warning_message

def test_get_seq_data_map_fallback_to_mining_result(tmp_path):
    dummy_file = tmp_path / "foo.json"
    dummy_file.write_text(
        json.dumps(
            {"records": [{"id": "contig", "seq": {"data": "ATGC"}, "features": []}]}
        )
    )
    result = get_seq_data_map({}, dummy_file)
    assert result["contig"].seq_len == 4  # type: ignore


def test_get_seq_data_map_non_json_file(tmp_path):
    non_json_file = tmp_path / "bar.txt"
    non_json_file.write_text("not a json")
    result = get_seq_data_map({}, non_json_file)
    assert result is None


class DummyConfig(Config):
    def __init__(self, margin):
        self.bgc_completeness_margin = margin


@pytest.mark.parametrize(
    "seq_data_map,sequence_id,start,end,margin,expected",
    [
        ({"seq1": ContigData(1000)}, "seq1", 10, 990, 10, "Complete"),
        ({"seq1": ContigData(1000)}, "seq1", 5, 990, 10, "Incomplete"),
        ({"seq1": ContigData(1000)}, "seq1", 10, 995, 10, "Incomplete"),
        ({}, "seq1", 10, 990, 10, "Unknown completeness"),
        ({"seq1": ContigData(1000)}, "seq2", 10, 990, 10, "Unknown completeness"),
    ],
)
def test_get_completeness(seq_data_map, sequence_id, start, end, margin, expected):
    config = DummyConfig(margin)
    result = get_completeness(config, seq_data_map, sequence_id, start, end)
    assert result == expected


def test_parse_input_mining_results_does_not_reuse_genome_alias(logger):
    """A genome alias may be assigned only once when multiple genomes exist."""
    assembly_20_deepbgc = (
        TEST_DATA_DIR / "assembly_20_mining" / "DeepBGC" / "DeepBGC.bgc.tsv"
    )

    results = parse_input_mining_result_files(
        logger,
        load_config(),
        [DEEPBGC_TSV_FILE, assembly_20_deepbgc],
        [
            TEST_DATA_DIR / "assembly_10.gbff.gz",
            TEST_DATA_DIR / "assembly_20.gbff.gz",
        ],
        matching_aliases=["assembly_10", "assembly_10"],
    )

    assert results[0].genome_data is not None
    assert results[1].genome_data is None


def test_parse_input_mining_results_tries_alias_after_used_original_label(
    tmp_path,
    logger,
):
    """A used original label must not block a different unused alias."""
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()

    first_result = first_dir / "assembly_10.json"
    second_result = second_dir / "assembly_10.json"

    antismash_data = {
        "records": [
            {
                "id": "contig",
                "features": [
                    {
                        "type": "region",
                        "location": "[0:3]",
                        "qualifiers": {},
                    }
                ],
            }
        ]
    }

    first_result.write_text(json.dumps(antismash_data))
    second_result.write_text(json.dumps(antismash_data))

    genome_10 = tmp_path / "assembly_10.fasta"
    genome_20 = tmp_path / "assembly_20.fasta"
    genome_10.write_text(">contig\nATGC\n")
    genome_20.write_text(">contig\nATGCATGC\n")

    results = parse_input_mining_result_files(
        logger,
        load_config(),
        [first_result, second_result],
        [genome_10, genome_20],
        matching_aliases=["unused_name", "assembly_20"],
    )

    assert results[0].genome_data["contig"].seq_len == 4  # type: ignore
    assert results[1].genome_data["contig"].seq_len == 8  # type: ignore


def test_parse_genome_data_rejects_duplicate_labels(tmp_path):
    """Genome files with the same normalized basename are ambiguous."""
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()

    first_genome = first_dir / "assembly.fasta"
    second_genome = second_dir / "assembly.fasta"
    first_genome.write_text(">contig1\nATGC\n")
    second_genome.write_text(">contig2\nATGC\n")

    with pytest.raises(ValueError, match="same input label 'assembly'"):
        parse_genome_data([first_genome, second_genome])