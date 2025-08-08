from pathlib import Path
from src.compare_to_ref_data import (
    Intersection,
    ReferenceBgc,
    Status,
)
from src.genome_mining_result import AlignmentInfo, Bgc, GenomeMiningResult, QuastResult


def compute_coverage(
    genome_mining_results: list[GenomeMiningResult],
    reference_genome_mining_result: GenomeMiningResult,
    quast_results: list[QuastResult],
) -> dict[Path, list[ReferenceBgc]]:
    """
    Compute reference BGC coverage for mining results.

    Match genome mining results with QUAST results by input_file_label.
    Each genome mining result should have a corresponding QUAST result.
    Process each pair independently to calculate reference coverage.

    Args:
        genome_mining_results (list): List of genome mining results.
        reference_genome_mining_result (GenomeMiningResult): Reference genome mining
        result.
        quast_results (list): Parsed QUAST results.

    Returns:
        dict[Path, list[ReferenceBgc]]: Dictionary mapping input file paths to ReferenceBgc
        objects with computed statistics.
    """
    ref_bgc_coverage = {}

    for genome_mining_result in genome_mining_results:
        corresponding_quast_result = next(
            (
                quast
                for quast in quast_results
                if quast.input_file_label == genome_mining_result.input_file_label
            ),
            None,
        )
        if not corresponding_quast_result:
            raise ValueError(
                f"No QUAST result found for genome mining result: "
                f"{genome_mining_result.input_file_label}"
            )
        ref_bgc_coverage[genome_mining_result.input_file] = (
            compute_reference_coverage(
                genome_mining_result,
                corresponding_quast_result,
                reference_genome_mining_result,
            )
        )

    return ref_bgc_coverage


def compute_reference_coverage(
    genome_mining_result: GenomeMiningResult,
    corresponding_quast_result: QuastResult,
    reference_genome_mining_result: GenomeMiningResult,
) -> list[ReferenceBgc]:
    """
    Compute the reference coverage for the given genome mining result and QUAST result.

    For each BGC in the reference genome mining result, get assembly bgcs on the same
    sequence using quast alignment.
    For each assembly BGC, map its coordinates into reference sequence and check if it
    intersects with the reference BGC.
    If it does, create an Intersection object and add it to the
    intersecting_assembly_bgcs list of the reference BGC.
    Compute the status of the reference BGC based on the intersecting assembly BGCs.

    Args:
        genome_mining_result (GenomeMiningResult): Genome mining result for the
        assembly.
        corresponding_quast_result (QuastResult): QUAST result corresponding to the
        assembly.
        reference_genome_mining_result (GenomeMiningResult): Reference genome mining
        result.

    Returns:
        list[ReferenceBgc]: List of ReferenceBgc objects representing the reference BGCs
        with their intersecting assembly BGCs.
    """

    assembly_bgcs_by_seq_id = {bgc.sequence_id: [] for bgc in genome_mining_result.bgcs}
    for bgc in genome_mining_result.bgcs:
        assembly_bgcs_by_seq_id[bgc.sequence_id].append(bgc)

    ref_bgcs = []
    # Iterate over reference BGCs and find corresponding assembly BGCs.
    for ref_bgc in reference_genome_mining_result.bgcs:
        # Initialize the reference BGC as a ReferenceBgc object.
        ref_bgc = ReferenceBgc.from_bgc(ref_bgc)

        relevant_alignments = corresponding_quast_result.reference_sequences.get(
            ref_bgc.sequence_id, []
        )
        intersections = []
        # Find intersecting assembly BGCs for the reference BGC for each alignment.
        for alignment in relevant_alignments:
            bgcs_on_aligned_sequence = assembly_bgcs_by_seq_id.get(
                alignment.assembly_seq_id, []
            )
            intersections.extend(
                get_intersecting_bgcs_from_alignment(
                    ref_bgc, alignment, bgcs_on_aligned_sequence
                )
            )

        ref_bgc.intersecting_assembly_bgcs = sorted(
            intersections, key=lambda x: x.start_in_ref
        )
        # Determine the status of the reference BGC based on intersections.
        ref_bgc.status = determine_ref_bgc_status(ref_bgc)
        ref_bgcs.append(ref_bgc)
    return ref_bgcs


def determine_ref_bgc_status(ref_bgc: ReferenceBgc) -> Status:
    """
    Determine the status of the reference BGC based on its intersecting assembly BGCs.

    If there are no intersecting assembly BGCs, the status is MISSED.
    If there is at least one intersecting assembly BGC that fully covers the reference BGC,
    the status is COVERED.
    If multiple intersecting assembly BGCs fully cover the reference BGC,
    the status is COVERED_BY_FRAGMENTS.
    If there are intersecting assembly BGCs but none fully cover the reference BGC,
    the status is PARTIALLY_COVERED.

    Args:
        ref_bgc (ReferenceBgc): Reference BGC to determine status for.

    Returns:
        Status: Status of the reference BGC.
    """
    if len(ref_bgc.intersecting_assembly_bgcs) == 0:
        return Status.MISSED

    # Find start and end of the continuous range.
    # Note: this assumes that intersecting_assembly_bgcs are sorted by start_in_ref.
    min_start = ref_bgc.intersecting_assembly_bgcs[0].start_in_ref
    max_end = ref_bgc.intersecting_assembly_bgcs[0].end_in_ref
    for intersection in ref_bgc.intersecting_assembly_bgcs:
        # Check if the assembly BGC fully covers the reference BGC.
        if (
            intersection.start_in_ref <= ref_bgc.start
            and intersection.end_in_ref >= ref_bgc.end
        ):
            return Status.COVERED

        if intersection.start_in_ref > max_end + 1:
            # If there is a gap between the current intersection and the previous one,
            # update min_start and max_end for the covered range.
            min_start = intersection.start_in_ref
            max_end = intersection.end_in_ref
        else:
            # Extend the range if the intersection overlaps.
            max_end = max(max_end, intersection.end_in_ref)

    if min_start <= ref_bgc.start and max_end >= ref_bgc.end:
        return Status.COVERED_BY_FRAGMENTS
    return Status.PARTIALLY_COVERED


def get_intersecting_bgcs_from_alignment(
    ref_bgc: ReferenceBgc, alignment: AlignmentInfo, bgcs_on_aligned_sequence: list[Bgc]
) -> list[Intersection]:
    """
    Get assembly BGCs from the alignment that intersect with the reference BGC.

    Args:
        ref_bgc (ReferenceBgc): Reference BGC to check intersections against.
        alignment (AlignmentInfo): Alignment information between assembly and reference.
        bgcs_on_aligned_sequence (list[Bgc]): List of assembly BGCs on the aligned sequence.

    Returns:
        list[Intersection]: List of Intersection objects representing intersections
        between assembly BGCs and the reference BGC.
    """

    intersections = []
    for assembly_bgc in bgcs_on_aligned_sequence:
        # Map assembly BGC coordinates to reference sequence.
        # Note: alignment.assembly_start and alignment.assembly_end may be reversed.
        if assembly_bgc.start <= max(
            alignment.assembly_end, alignment.assembly_start
        ) and assembly_bgc.end >= min(alignment.assembly_start, alignment.assembly_end):
            # Calculate intersection coordinates.
            assembly_bgc_start_in_ref, assembly_bgc_end_in_ref, reversed = (
                get_asm_bgc_coords_on_ref(
                    assembly_bgc.start, assembly_bgc.end, alignment
                )
            )
            if (
                assembly_bgc_start_in_ref <= ref_bgc.end
                and assembly_bgc_end_in_ref >= ref_bgc.start
            ):
                # Create Intersection object.
                intersection = Intersection(
                    assembly_bgc=assembly_bgc,
                    start_in_ref=assembly_bgc_start_in_ref,
                    end_in_ref=assembly_bgc_end_in_ref,
                    reversed=reversed,
                )
                intersections.append(intersection)
    return intersections


def get_asm_bgc_coords_on_ref(
    assembly_bgc_start, assembly_bgc_end, alignment: AlignmentInfo
) -> tuple[int, int, bool]:
    """
    Map BGC coordinates in assembly to coordinates on reference based on
    assembly-to-reference alignment info.

    Example:
        If assembly BGC starts at 61 and ends at 80 (length 20), and the alignment
        maps assembly coordinates 51-110 (length 60) to reference coordinates 11-76
        (length 66), the mapped coordinates will be: 22-43 (length 22). Note that
        the length of the mapped BGC grew 10% due to the 10% alignment length
        difference.

    Args:
        assembly_bgc_start (int): BGC start position in assembly.
        assembly_bgc_end (int): BGC end position in assembly.
        alignment (AlignmentInfo): Alignment information.

    Returns:
        Tuple[int, int, bool]: Mapped start and end positions in reference, whether
        the coordinates are reversed.
    """
    diff_factor = (alignment.ref_end - alignment.ref_start + 1) / (
        abs(alignment.assembly_end - alignment.assembly_start) + 1
    )
    reversed = alignment.assembly_start > alignment.assembly_end
    if not reversed:
        # Cut assembly bgc if it is bigger than the aligned part.
        assembly_bgc_start = max(assembly_bgc_start, alignment.assembly_start)
        assembly_bgc_end = min(assembly_bgc_end, alignment.assembly_end)

        mapped_assembly_bgc_start = (
            alignment.ref_start
            + (assembly_bgc_start - alignment.assembly_start) * diff_factor
        )
        mapped_assembly_bgc_end = (
            alignment.ref_end
            - (alignment.assembly_end - assembly_bgc_end) * diff_factor
        )
    else:
        # Cut assembly bgc if it is bigger than the aligned part.
        assembly_bgc_start = max(assembly_bgc_start, alignment.assembly_end)
        assembly_bgc_end = min(assembly_bgc_end, alignment.assembly_start)

        mapped_assembly_bgc_start = (
            alignment.ref_start
            + (alignment.assembly_start - assembly_bgc_end) * diff_factor
        )
        mapped_assembly_bgc_end = (
            alignment.ref_end
            - (assembly_bgc_start - alignment.assembly_end) * diff_factor
        )
    return int(mapped_assembly_bgc_start), int(mapped_assembly_bgc_end), reversed
