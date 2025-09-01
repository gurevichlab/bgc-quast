from pathlib import Path
from typing import Literal

import pytest

# Relative imports from the file under test.
from src.compare_to_ref_analyzer import (
    ReferenceBgc,
    Status,
    compute_coverage,
    compute_reference_coverage,
    determine_ref_bgc_status,
    get_asm_bgc_coords_on_ref,
    get_intersecting_bgcs_from_alignment,
)
from src.compare_to_ref_data import Intersection
from src.genome_mining_result import AlignmentInfo, Bgc, GenomeMiningResult, QuastResult

# ====================== Helper Create Functions ======================


def create_bgc(
    sequence_id="chr1",
    start=0,
    end=100,
    bgc_id="",
    completeness: Literal["Complete", "Incomplete", "Unknown"] = "Unknown",
    product_types=None,
    metadata=None,
):
    if product_types is None:
        product_types = []
    return Bgc(
        bgc_id=bgc_id,
        sequence_id=sequence_id,
        start=start,
        end=end,
        completeness=completeness,
        product_types=product_types,
        metadata=metadata,
    )


def create_reference_bgc(
    sequence_id="chr1",
    start=0,
    end=100,
    bgc_id="",
    completeness: Literal["Complete", "Incomplete", "Unknown"] = "Unknown",
    product_types=None,
    metadata=None,
    intersecting_assembly_bgcs=None,
):
    if product_types is None:
        product_types = []
    if intersecting_assembly_bgcs is None:
        intersecting_assembly_bgcs = []
    return ReferenceBgc(
        bgc_id=bgc_id,
        sequence_id=sequence_id,
        start=start,
        end=end,
        completeness=completeness,
        product_types=product_types,
        metadata=metadata,
        intersecting_assembly_bgcs=intersecting_assembly_bgcs,
    )


def create_genome_mining_result(
    input_file="dummy.fasta",
    input_file_label="dummy_label",
    mining_tool="dummy_tool",
    bgcs=None,
):
    if bgcs is None:
        bgcs = []
    return GenomeMiningResult(
        input_file=Path(input_file),
        input_file_label=input_file_label,
        mining_tool=mining_tool,
        bgcs=bgcs,
    )


def create_alignment_info(
    assembly_seq_id="asm_seq_id",
    ref_seq_id="ref_seq_id",
    ref_start=1000,
    ref_end=1100,
    assembly_start=100,
    assembly_end=200,
    len_diff=0,
):
    return AlignmentInfo(
        assembly_seq_id=assembly_seq_id,
        ref_seq_id=ref_seq_id,
        ref_start=ref_start,
        ref_end=ref_end,
        assembly_start=assembly_start,
        assembly_end=assembly_end,
        len_diff=len_diff,
    )


def create_quast_result(
    input_dir="dummy_dir",
    input_file_label="dummy_label",
    assembly_sequences=None,
    reference_sequences=None,
):
    if assembly_sequences is None:
        assembly_sequences = {}
    if reference_sequences is None:
        reference_sequences = {}
    return QuastResult(
        input_dir=Path(input_dir),
        input_file_label=input_file_label,
        assembly_sequences=assembly_sequences,
        reference_sequences=reference_sequences,
    )


# ====================== Tests for determine_status ======================


def test_determine_status_missed():
    # Create a reference BGC with no intersections.
    ref_bgc = create_reference_bgc(start=100, end=200)
    # Assuming intersecting_assembly_bgcs defaults empty.
    status = determine_ref_bgc_status(ref_bgc, allowed_gap=100)
    assert status == Status.MISSED


def test_determine_status_covered():
    # Create an Intersection that fully covers the reference.
    intersection = Intersection(
        start_in_ref=50,
        end_in_ref=250,
        assembly_bgc=create_bgc(start=0, end=200),
    )
    ref_bgc = create_reference_bgc(
        start=100, end=200, intersecting_assembly_bgcs=[intersection]
    )
    status = determine_ref_bgc_status(ref_bgc, allowed_gap=100)
    assert status == Status.FULLY_RECOVERED


def test_determine_status_partly_covered():
    # Create a reference BGC with an intersection that does not cover completely.
    intersection = Intersection(
        start_in_ref=120,
        end_in_ref=180,
        assembly_bgc=create_bgc(start=1, end=61),
    )
    ref_bgc = create_reference_bgc(
        start=100, end=200, intersecting_assembly_bgcs=[intersection]
    )
    status = determine_ref_bgc_status(ref_bgc, allowed_gap=100)
    assert status == Status.PARTIALLY_RECOVERED


def test_determine_status_partly_covered_non_contiguous_intersections():
    # Create a reference BGC with non contiguous intersections that do not cover
    # completely.
    intersection1 = Intersection(
        start_in_ref=50,
        end_in_ref=150,
        assembly_bgc=create_bgc(start=0, end=100),
    )
    intersection2 = Intersection(
        start_in_ref=152,
        end_in_ref=250,
        assembly_bgc=create_bgc(start=0, end=98),
    )
    ref_bgc = create_reference_bgc(
        start=100, end=200, intersecting_assembly_bgcs=[intersection1, intersection2]
    )
    status = determine_ref_bgc_status(ref_bgc, allowed_gap=1)
    assert status == Status.PARTIALLY_RECOVERED


def test_determine_status_covered_by_fragments():
    # Create a reference BGC where multiple intersections together cover the range.
    intersection1 = Intersection(
        start_in_ref=50,
        end_in_ref=150,
        assembly_bgc=create_bgc(start=0, end=100),
    )
    intersection2 = Intersection(
        start_in_ref=151,
        end_in_ref=252,
        assembly_bgc=create_bgc(start=3, end=103),
    )
    ref_bgc = create_reference_bgc(
        start=100, end=200, intersecting_assembly_bgcs=[intersection1, intersection2]
    )
    status = determine_ref_bgc_status(ref_bgc, allowed_gap=100)
    assert status == Status.FRAGMENTED_RECOVERY


def test_determine_status_covered_by_fragments_extra_intersections():
    # Create a reference BGC where multiple intersections together cover the range,
    # but there are extra intersections that do not contribute to coverage.
    intersection1 = Intersection(
        start_in_ref=50,
        end_in_ref=95,
        assembly_bgc=create_bgc(start=0, end=45),
    )
    intersection2 = Intersection(
        start_in_ref=99,
        end_in_ref=150,
        assembly_bgc=create_bgc(start=0, end=51),
    )
    intersection3 = Intersection(
        start_in_ref=130,
        end_in_ref=200,
        assembly_bgc=create_bgc(start=0, end=170),
    )
    ref_bgc = create_reference_bgc(
        start=100,
        end=200,
        intersecting_assembly_bgcs=[intersection1, intersection2, intersection3],
    )
    status = determine_ref_bgc_status(ref_bgc, allowed_gap=100)
    assert status == Status.FRAGMENTED_RECOVERY


# ====================== Tests for map_coordinates ======================


def test_map_coordinates_forward():
    # Forward alignment: assembly_start <= assembly_end.
    alignment = create_alignment_info(
        assembly_start=100,
        assembly_end=200,
        ref_start=1000,
        ref_end=1100,
        len_diff=0,
    )
    # Assembly BGC fully inside alignment.
    bgc_start, bgc_end = 120, 180
    new_start, new_end, reversed = get_asm_bgc_coords_on_ref(
        bgc_start, bgc_end, alignment
    )
    # Expected: new_start = 1000 + (120-100) = 1020, new_end = 1100 + (180-200) = 1080.
    assert new_start == 1020
    assert new_end == 1080
    assert reversed is False


def test_map_coordinates_reverse():
    # Reverse alignment: assembly_start > assembly_end.
    alignment = create_alignment_info(
        assembly_start=200,
        assembly_end=100,
        ref_start=900,
        ref_end=1005,
        len_diff=5,
    )
    bgc_start, bgc_end = 150, 180
    new_start, new_end, reversed = get_asm_bgc_coords_on_ref(
        bgc_start, bgc_end, alignment
    )
    # In reverse branch:
    # assembly_start = max(150, 100) = 150, assembly_end = min(180, 200) = 180.
    # diff_factor = (1005 - 900 + 1) / (200 - 100 +  1) = 106 / 101.
    # new_start = 900 + (200 - 180) * 106 / 101 = 900 + 20 * 1.0495 = 900 + 20.99 = 920.99.
    # new_end = 1005 - (150 - 100) * 106 / 101 = 1005 - 50 * 1.0495 = 1005 - 52.475 = 952.525.
    assert new_start == 920
    assert new_end == 952
    assert reversed is True


# ====================== Tests for get_intersecting_bgcs_from_alignment ===============


def test_get_intersecting_bgcs_from_alignment():
    ref_bgc = create_reference_bgc(start=110, end=200)
    alignment = create_alignment_info(
        assembly_start=10,
        assembly_end=100,
        ref_start=90,
        ref_end=180,
        len_diff=0,
        assembly_seq_id="chr1",
    )
    assembly_bgc_intersecting = create_bgc(sequence_id="chr1", start=20, end=90)
    assembly_bgc_not_intersecting = create_bgc(sequence_id="chr1", start=10, end=19)
    intersections = get_intersecting_bgcs_from_alignment(
        ref_bgc, alignment, [assembly_bgc_intersecting, assembly_bgc_not_intersecting]
    )
    # Expected mapped coordinates:
    # new_start = 90 + (max(20, 10) - 10) = 90 + (20 - 10) = 100,
    # new_end = 180 - (100 - min(90, 100)) = 180 - (100 - 90) = 170.
    assert len(intersections) == 1
    intr = intersections[0]
    assert intr.start_in_ref == 100
    assert intr.end_in_ref == 170


# ====================== Tests for compute_reference_coverage ======================


def test_compute_reference_coverage_no_intersections():
    asm_bgc = create_bgc(start=100, end=200)
    genome_mining_result = create_genome_mining_result(bgcs=[asm_bgc])
    ref_bgc = create_bgc(start=120, end=180)
    reference_genome_mining_result = create_genome_mining_result(bgcs=[ref_bgc])
    # QUAST result with no alignments for the reference.
    quast_result = create_quast_result(reference_sequences={})
    reference_bgcs = compute_reference_coverage(
        genome_mining_result,
        quast_result,
        reference_genome_mining_result,
        allowed_gap=100,
    )
    # With no alignment, the ReferenceBgc's intersecting_assembly_bgcs remains empty.
    assert len(reference_bgcs) == 1
    result_ref_bgc = reference_bgcs[0]
    assert result_ref_bgc.intersecting_assembly_bgcs == []
    status = determine_ref_bgc_status(result_ref_bgc, allowed_gap=100)
    assert status == Status.MISSED


def test_compute_reference_coverage_fully_covered():
    asm_bgc = create_bgc(sequence_id="asm_id", start=100, end=200)
    genome_mining_result = create_genome_mining_result(bgcs=[asm_bgc])
    ref_bgc = create_bgc(sequence_id="ref_id", start=120, end=180)
    reference_genome_mining_result = create_genome_mining_result(bgcs=[ref_bgc])
    alignment = create_alignment_info(
        assembly_start=50,
        assembly_end=250,
        ref_start=50,
        ref_end=250,
        len_diff=0,
        assembly_seq_id="asm_id",
    )
    quast_result = create_quast_result(reference_sequences={"ref_id": [alignment]})
    reference_bgcs = compute_reference_coverage(
        genome_mining_result,
        quast_result,
        reference_genome_mining_result,
        allowed_gap=100,
    )
    assert len(reference_bgcs) == 1
    result_ref_bgc = reference_bgcs[0]
    assert len(result_ref_bgc.intersecting_assembly_bgcs) == 1
    assert result_ref_bgc.status == Status.FULLY_RECOVERED


def test_compute_reference_coverage_covered_by_fragments_with_gap_closed():
    """
    Test compute_reference_coverage when two assembly BGCs from a single alignment,
    individually not fully covering the reference, together cover it continuously.
    """
    # Assembly BGCs on the same sequence that together cover the reference BGC.
    asm_bgc1 = create_bgc(sequence_id="asm_id", start=80, end=180)
    asm_bgc2 = create_bgc(sequence_id="asm_id", start=181, end=320)
    genome_mining_result = create_genome_mining_result(bgcs=[asm_bgc1, asm_bgc2])
    # Reference BGC that requires both intersections to be fully covered.
    ref_bgc = create_bgc(sequence_id="ref_id", start=100, end=250)
    reference_genome_mining_result = create_genome_mining_result(bgcs=[ref_bgc])
    # Single alignment mapping all assembly regions to the reference.
    alignment = create_alignment_info(
        assembly_seq_id="asm_id",
        ref_seq_id="ref_id",
        assembly_start=50,
        assembly_end=250,
        ref_start=50,
        ref_end=250,
        len_diff=0,
    )
    quast_result = create_quast_result(reference_sequences={"ref_id": [alignment]})

    reference_bgcs = compute_reference_coverage(
        genome_mining_result,
        quast_result,
        reference_genome_mining_result,
        allowed_gap=100,
    )
    assert len(reference_bgcs) == 1
    result_ref_bgc = reference_bgcs[0]
    # The union of the two intersections covers the reference even though neither does
    # individually.
    assert result_ref_bgc.status == Status.FRAGMENTED_RECOVERY
    assert result_ref_bgc.intersecting_assembly_bgcs[0].start_in_ref == 80
    assert result_ref_bgc.intersecting_assembly_bgcs[0].end_in_ref == 180
    assert result_ref_bgc.intersecting_assembly_bgcs[0].reversed is False
    assert result_ref_bgc.intersecting_assembly_bgcs[0].assembly_bgc == asm_bgc1

    assert result_ref_bgc.intersecting_assembly_bgcs[1].start_in_ref == 181
    assert result_ref_bgc.intersecting_assembly_bgcs[1].end_in_ref == 250
    assert result_ref_bgc.intersecting_assembly_bgcs[1].reversed is False
    assert result_ref_bgc.intersecting_assembly_bgcs[1].assembly_bgc == asm_bgc2


def test_compute_reference_coverage_multiple_alignments_different_asm_seq():
    """
    Test compute_reference_coverage when assembly BGCs originate from different
    alignment entries (i.e. different assembly_seq_ids) but both map to the same reference.
    The combined intersections should be merged to cover the reference.
    """
    # Create assembly BGCs on different assembly sequences.
    asm_bgc1 = create_bgc(sequence_id="asm_id_1", start=80, end=180)
    asm_bgc2 = create_bgc(sequence_id="asm_id_2", start=181, end=320)
    genome_mining_result = create_genome_mining_result(bgcs=[asm_bgc1, asm_bgc2])
    # Reference BGC on which both assembly BGCs will align.
    ref_bgc = create_bgc(sequence_id="ref_id", start=100, end=300)
    reference_genome_mining_result = create_genome_mining_result(bgcs=[ref_bgc])

    # Two alignments from different assembly sequences mapping onto the same reference.
    alignment1 = create_alignment_info(
        assembly_seq_id="asm_id_1",
        assembly_start=50,
        assembly_end=250,
        ref_start=50,
        ref_end=250,
        len_diff=0,
    )
    alignment2 = create_alignment_info(
        assembly_seq_id="asm_id_2",
        assembly_start=180,
        assembly_end=300,
        ref_start=180,
        ref_end=300,
        len_diff=0,
    )
    quast_result = create_quast_result(
        reference_sequences={"ref_id": [alignment1, alignment2]}
    )

    reference_bgcs = compute_reference_coverage(
        genome_mining_result,
        quast_result,
        reference_genome_mining_result,
        allowed_gap=100,
    )
    assert len(reference_bgcs) == 1
    result_ref_bgc = reference_bgcs[0]
    # The intersections from both alignments should merge and be recognized as covering
    # fragments.
    assert result_ref_bgc.status == Status.FRAGMENTED_RECOVERY
    assert len(result_ref_bgc.intersecting_assembly_bgcs) == 2
    assert result_ref_bgc.intersecting_assembly_bgcs[0].start_in_ref == 80
    assert result_ref_bgc.intersecting_assembly_bgcs[0].end_in_ref == 180
    assert result_ref_bgc.intersecting_assembly_bgcs[0].reversed is False
    assert result_ref_bgc.intersecting_assembly_bgcs[0].assembly_bgc == asm_bgc1

    assert result_ref_bgc.intersecting_assembly_bgcs[1].start_in_ref == 181
    assert result_ref_bgc.intersecting_assembly_bgcs[1].end_in_ref == 300
    assert result_ref_bgc.intersecting_assembly_bgcs[1].reversed is False
    assert result_ref_bgc.intersecting_assembly_bgcs[1].assembly_bgc == asm_bgc2


# ====================== Tests for compute_coverage ======================


def test_compute_coverage():
    asm_bgc = create_bgc(sequence_id="asm_id", start=100, end=200)
    genome_mining_result = create_genome_mining_result(
        input_file="asm.fasta", input_file_label="asm_label", bgcs=[asm_bgc]
    )
    genome_mining_results = [genome_mining_result]
    ref_bgc = create_bgc(sequence_id="ref_id", start=120, end=180)
    reference_genome_mining_result = create_genome_mining_result(bgcs=[ref_bgc])
    alignment = create_alignment_info(
        assembly_start=50,
        assembly_end=250,
        ref_start=50,
        ref_end=250,
        len_diff=0,
        assembly_seq_id="asm_id",
    )
    quast_result = create_quast_result(
        reference_sequences={"ref_id": [alignment]}, input_file_label="asm_label"
    )
    quast_results = [quast_result]
    coverage_list = compute_coverage(
        genome_mining_results,
        reference_genome_mining_result,
        quast_results,
        allowed_gap=100,
    )
    # The coverage_list should have one entry keyed by input_file.
    ref_coverage = coverage_list[0][1]
    assert isinstance(coverage_list, list)
    assert len(coverage_list) == 1
    status = ref_coverage[0].status
    assert status == Status.FULLY_RECOVERED


def test_compute_coverage_no_quast_result():
    # Create a genome mining result with a label that does not match any QUAST result.
    asm_bgc = create_bgc(sequence_id="asm_id", start=100, end=200)
    genome_mining_result = create_genome_mining_result(
        input_file="asm.fasta", input_file_label="asm_label", bgcs=[asm_bgc]
    )
    genome_mining_results = [genome_mining_result]

    # Create a reference genome mining result.
    ref_bgc = create_bgc(sequence_id="ref_id", start=120, end=180)
    reference_genome_mining_result = create_genome_mining_result(bgcs=[ref_bgc])

    # Create a QUAST result with a different input_file_label.
    quast_result = create_quast_result(
        reference_sequences={"ref_id": []}, input_file_label="wrong_label"
    )
    quast_results = [quast_result]

    with pytest.raises(ValueError) as excinfo:
        compute_coverage(
            genome_mining_results,
            reference_genome_mining_result,
            quast_results,
            allowed_gap=100,
        )
    assert "No QUAST result found" in str(excinfo.value)
