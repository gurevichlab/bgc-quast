from typing import Optional
from bgc_quast.logger import Logger
from bgc_quast.option_parser import ValidationError

from bgc_quast.compare_to_ref_data import (
    Intersection,
    RecoveryContiguity,
    ReferenceBgc,
    Status,
)
from bgc_quast.genome_mining_result import AlignmentInfo, Bgc, GenomeMiningResult, QuastResult

INPUT_NAMING_DOCS_URL = (
    "https://github.com/gurevichlab/bgc-quast/blob/main/README.md#sec_naming"
)


#TODO: refactor the matching of genome mining labels to QUAST labels (.coords)
# and corresponding validations & errors into a separate function
def compute_coverage(
    log: Logger,
    genome_mining_results: list[GenomeMiningResult],
    reference_genome_mining_result: GenomeMiningResult,
    quast_results: list[QuastResult],
    allowed_gap: int,
    matching_aliases: Optional[list[str]] = None,
) -> list[tuple[GenomeMiningResult, list[ReferenceBgc]]]:
    """
    Compute reference BGC coverage for mining results.

    QUAST results are matched first by the original input_file_label.
    If that fails, the corresponding positional --names value is used
    as a fallback alias.

    Each QUAST result can be associated with only one mining result.
    """
    quast_results_by_label: dict[str, QuastResult] = {}
    duplicate_quast_labels = set()

    for quast_result in quast_results:
        label = quast_result.input_file_label

        if label in quast_results_by_label:
            duplicate_quast_labels.add(label)
        else:
            quast_results_by_label[label] = quast_result

    if duplicate_quast_labels:
        duplicate_files = ", ".join(
            f"{label}.coords" for label in sorted(duplicate_quast_labels)
        )
        raise ValidationError(
            "Duplicate QUAST file labels were detected after filename "
            f"normalization: {duplicate_files}. QUAST .coords files must "
            "have unique basenames."
        )

    used_quast_labels: set[str] = set()
    ref_bgc_coverage = []

    for result_index, genome_mining_result in enumerate(genome_mining_results):
        original_label = genome_mining_result.input_file_label
        matching_alias = (
            matching_aliases[result_index]
            if matching_aliases is not None
            else None
        )

        corresponding_quast_result = None
        matched_by_alias = False

        # Primary match: original filename-derived label.
        original_quast_result = quast_results_by_label.get(original_label)
        if (
            original_quast_result is not None
            and original_label not in used_quast_labels
        ):
            corresponding_quast_result = original_quast_result

        # Fallback match: positional value supplied through --names.
        if (
            corresponding_quast_result is None
            and matching_alias is not None
            and matching_alias != original_label
        ):
            alias_quast_result = quast_results_by_label.get(matching_alias)

            if (
                alias_quast_result is not None
                and matching_alias not in used_quast_labels
            ):
                corresponding_quast_result = alias_quast_result
                matched_by_alias = True

        if corresponding_quast_result is None:
            attempted_labels = f"original label '{original_label}'"

            if matching_alias is not None and matching_alias != original_label:
                attempted_labels += (
                    f" and --names alias '{matching_alias}'"
                )

            mining_result_details = []
            for index, result in enumerate(genome_mining_results):
                alias = (
                    matching_aliases[index]
                    if matching_aliases is not None
                    else None
                )
                alias_text = (
                    f", --names alias '{alias}'"
                    if alias is not None
                    else ""
                )
                mining_result_details.append(
                    f"  - {result.input_file} "
                    f"(original label '{result.input_file_label}'"
                    f"{alias_text})"
                )

            quast_file_details = [
                f"  - {label}.coords"
                for label in sorted(quast_results_by_label)
            ]

            newline_char = '\n'
            raise ValidationError(
                f"Could not find a QUAST .coords file matching genome mining result "
                f"'{genome_mining_result.input_file}'.\n\n"
                f"Tried matching against:\n"
                f"{attempted_labels}\n\n"
                f"Genome mining results:\n"
                f"{newline_char.join(mining_result_details)}\n\n"
                f"QUAST .coords files found:\n"
                f"{newline_char.join(quast_file_details)}\n\n"
                f"BGC-QUAST matches QUAST files using their original basenames first. "
                f"If that fails, it uses the corresponding positional --names value. "
                f"Each QUAST .coords file can only be matched once.\n\n"
                f"To fix this, rerun BGC-QUAST with one --names value per genome mining "
                f"input file, in the same order. Each value should match the basename of "
                f"the corresponding QUAST .coords file (without the .coords extension).\n\n"
                f"Example:\n"
                f"  --names assembly_10,assembly_20\n\n"
                f"If the files still cannot be matched, rerun QUAST using assembly "
                f"filenames compatible with the genome mining result filenames.\n\n"
                f"See the BGC-QUAST input-naming documentation for more detail: {INPUT_NAMING_DOCS_URL}"
            )

        used_quast_labels.add(corresponding_quast_result.input_file_label)

        if matched_by_alias:
            log.info(
                f"Matched genome mining result "
                f"'{genome_mining_result.input_file}' to QUAST file "
                f"'{matching_alias}.coords' using its --names alias, because "
                f"the original input label '{original_label}' did not match "
                f"an available QUAST result."
            )

        ref_bgc_coverage.append(
            (
                genome_mining_result,
                compute_reference_coverage(
                    genome_mining_result,
                    corresponding_quast_result,
                    reference_genome_mining_result,
                    allowed_gap=allowed_gap,
                ),
            )
        )

    return ref_bgc_coverage


def compute_reference_coverage(
    genome_mining_result: GenomeMiningResult,
    corresponding_quast_result: QuastResult,
    reference_genome_mining_result: GenomeMiningResult,
    allowed_gap: int,
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
        allowed_gap (int): Allowed gap for fragmented recovery.

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
        ref_bgc.status = determine_ref_bgc_status(ref_bgc, allowed_gap)
        ref_bgcs.append(ref_bgc)
    return ref_bgcs

def count_recovery_blocks(ref_bgc: ReferenceBgc, allowed_gap: int) -> int:
    """
    Count disjoint recovery blocks for the reference BGC.

    Intersections separated by more than allowed_gap are treated as distinct recovery
    blocks. This does not change recovery logic; it only annotates whether recovery is
    single-contig or multi-contig.
    """
    if not ref_bgc.intersecting_assembly_bgcs:
        return 0

    block_count = 1
    max_end = ref_bgc.intersecting_assembly_bgcs[0].end_in_ref
    for intersection in ref_bgc.intersecting_assembly_bgcs[1:]:
        if intersection.start_in_ref > max_end + allowed_gap:
            block_count += 1
        max_end = max(max_end, intersection.end_in_ref)

    return block_count


def determine_ref_bgc_status(ref_bgc: ReferenceBgc, allowed_gap: int) -> Status:
    """
    Determine the status of the reference BGC based on its intersecting assembly BGCs.

    If there are no intersecting assembly BGCs, the status is MISSED.
    If there is at least one intersecting assembly BGC that fully covers the reference BGC,
    the status is FULLY_RECOVERED.
    If recovery comes from multiple disjoint recovery blocks and reaches full coverage,
    the status is still FULLY_RECOVERED, but recovery_contiguity is MULTI_CONTIG.
    If there are intersecting assembly BGCs but coverage is only partial,
    the status is PARTIALLY_RECOVERED with contiguity annotation.

    Args:
        ref_bgc (ReferenceBgc): Reference BGC to determine status for.
        allowed_gap (int): Allowed gap between assembly BGCs for fragmented recovery.

    Returns:
        Status: Status of the reference BGC.
    """
    if not ref_bgc.intersecting_assembly_bgcs:
        return Status.MISSED

    # Check for FULLY_RECOVERED by a single BGC
    for intersection in ref_bgc.intersecting_assembly_bgcs:
        coverage = min(ref_bgc.end, intersection.end_in_ref) - max(
            ref_bgc.start, intersection.start_in_ref
        )
        if coverage >= 0.95 * (ref_bgc.end - ref_bgc.start):
            ref_bgc.main_covering_assembly_bgc = intersection.assembly_bgc
            ref_bgc.recovered_product_types = intersection.assembly_bgc.product_types
            ref_bgc.recovery_contiguity = RecoveryContiguity.SINGLE_CONTIG
            return Status.FULLY_RECOVERED

    # Check for fully or partially recovered status using the existing multi-block logic.
    # Note: this assumes that intersecting_assembly_bgcs are sorted by start_in_ref.
    block_count = count_recovery_blocks(ref_bgc, allowed_gap)

    min_start = ref_bgc.intersecting_assembly_bgcs[0].start_in_ref
    max_end = ref_bgc.intersecting_assembly_bgcs[0].end_in_ref
    product_types = ref_bgc.intersecting_assembly_bgcs[0].assembly_bgc.product_types
    for intersection in ref_bgc.intersecting_assembly_bgcs[1:]:
        if intersection.start_in_ref > max_end + allowed_gap:
            min_start = intersection.start_in_ref
            product_types = intersection.assembly_bgc.product_types
        max_end = max(max_end, intersection.end_in_ref)

    total_coverage = min(ref_bgc.end, max_end) - max(ref_bgc.start, min_start)
    coverage_percentage = total_coverage / (ref_bgc.end - ref_bgc.start)

    recovery_contiguity = (
        RecoveryContiguity.SINGLE_CONTIG
        if block_count == 1
        else RecoveryContiguity.MULTI_CONTIG
    )

    if coverage_percentage >= 0.95:
        ref_bgc.recovered_product_types = product_types
        ref_bgc.recovery_contiguity = recovery_contiguity
        return Status.FULLY_RECOVERED
    if 0.10 <= coverage_percentage < 0.95:
        ref_bgc.recovered_product_types = product_types
        ref_bgc.recovery_contiguity = recovery_contiguity
        return Status.PARTIALLY_RECOVERED

    return Status.MISSED


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
