import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from Bio import SeqIO

from bgc_quast.genome_mining_result import GenomeMiningResult
from bgc_quast.input_utils import open_file
from bgc_quast.output.genbank_writer import normalize_id


def _format_int(value: int) -> str:
    # return f"{value:,}"
    return f"{value}"


def _format_product_types(product_types) -> str:
    if not product_types:
        return "N/A"
    return ", ".join(product_types)


def _format_bgc_cell(start: int, end: int, product_groups: List[str]) -> str:
    if not product_groups:
        return "N/A"

    # using GenBank coordinates style
    display_start = start + 1
    display_end = end

    return f"{_format_int(display_start)} - {_format_int(display_end)} " + "; ".join(
        f"({products})" for products in product_groups
    )


def _collapse_same_tool_bgcs(bgcs) -> str:
    if not bgcs:
        return "N/A"

    start = bgcs[0].start
    end = bgcs[0].end
    product_groups = [_format_product_types(bgc.product_types) for bgc in bgcs]

    return _format_bgc_cell(start, end, product_groups)


def _collapse_multiple_bgcs(bgcs) -> str:
    if not bgcs:
        return "N/A"

    bgcs_sorted = sorted(bgcs, key=lambda bgc: (bgc.start, bgc.end, tuple(bgc.product_types)))
    return "; ".join(
        _format_bgc_cell(bgc.start, bgc.end, [_format_product_types(bgc.product_types)])
        for bgc in bgcs_sorted
    )


def _natural_sort_key(text: str):
    parts = re.split(r"(\d+)", str(text))
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def _load_sequence_order_from_genome(genome_file: Path) -> Optional[Dict[str, int]]:
    for fmt in ("genbank", "fasta"):
        with open_file(genome_file) as handle:
            try:
                records = list(SeqIO.parse(handle, fmt))
            except Exception:
                records = []

        if records:
            return {normalize_id(record.id): i for i, record in enumerate(records)}

    return None


def _prepare_bgc_groups(genome_mining_results: List[GenomeMiningResult]):
    tools = [result.mining_tool for result in genome_mining_results]
    labels = [result.display_label for result in genome_mining_results]

    grouped: Dict[Tuple[str, int, int], Dict[str, list]] = defaultdict(
        lambda: defaultdict(list)
    )
    contig_display_names: Dict[str, str] = {}
    all_sequence_ids = set()

    for result in genome_mining_results:
        tool = result.mining_tool
        for bgc in result.bgcs:
            if bgc.start is None or bgc.end is None:
                continue

            sequence_id = str(bgc.sequence_id)
            normalized_sequence_id = normalize_id(sequence_id)
            all_sequence_ids.add(normalized_sequence_id)

            if normalized_sequence_id not in contig_display_names:
                contig_display_names[normalized_sequence_id] = sequence_id

            key = (normalized_sequence_id, bgc.start, bgc.end)
            grouped[key][tool].append(bgc)

    return tools, labels, grouped, contig_display_names, all_sequence_ids


def _sort_grouped_keys(grouped_keys, contig_display_names, all_sequence_ids, genome_file):
    genome_sequence_order = (
        _load_sequence_order_from_genome(genome_file) if genome_file is not None else None
    )

    if genome_sequence_order is not None:
        missing_sequence_ids = sorted(
            [seq_id for seq_id in all_sequence_ids if seq_id not in genome_sequence_order],
            key=_natural_sort_key,
        )
        next_index = len(genome_sequence_order)
        for seq_id in missing_sequence_ids:
            genome_sequence_order[seq_id] = next_index
            next_index += 1

        return sorted(
            grouped_keys,
            key=lambda x: (genome_sequence_order[x[0]], x[1], x[2]),
        )

    return sorted(
        grouped_keys,
        key=lambda x: (_natural_sort_key(contig_display_names[x[0]]), x[1], x[2]),
    )


def write_bgc_tsv(
    genome_mining_results: List[GenomeMiningResult],
    output_path: Path,
    genome_file: Optional[Path] = None,
) -> None:
    tools, labels, grouped, contig_display_names, all_sequence_ids = _prepare_bgc_groups(
        genome_mining_results
    )

    sorted_keys = _sort_grouped_keys(
        grouped.keys(), contig_display_names, all_sequence_ids, genome_file
    )

    with open(output_path, "w", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["file_label", *labels])
        writer.writerow(["Genome mining tool", *tools])

        for normalized_contig_id, start, end in sorted_keys:
            tool_to_bgcs = grouped[(normalized_contig_id, start, end)]
            row = [contig_display_names[normalized_contig_id]]
            for tool in tools:
                row.append(_collapse_same_tool_bgcs(tool_to_bgcs.get(tool, [])))
            writer.writerow(row)


def write_overlapping_bgc_tsv(
    genome_mining_results: List[GenomeMiningResult],
    output_path: Path,
    genome_file: Optional[Path] = None,
) -> None:
    tools = [result.mining_tool for result in genome_mining_results]
    labels = [result.display_label for result in genome_mining_results]

    contig_display_names: Dict[str, str] = {}
    all_sequence_ids = set()
    bgcs_by_contig: Dict[str, List[tuple]] = defaultdict(list)

    for result in genome_mining_results:
        tool = result.mining_tool
        for bgc in result.bgcs:
            if bgc.start is None or bgc.end is None:
                continue

            sequence_id = str(bgc.sequence_id)
            normalized_sequence_id = normalize_id(sequence_id)
            all_sequence_ids.add(normalized_sequence_id)

            if normalized_sequence_id not in contig_display_names:
                contig_display_names[normalized_sequence_id] = sequence_id

            bgcs_by_contig[normalized_sequence_id].append((bgc.start, bgc.end, tool, bgc))

    sorted_contigs = _sort_grouped_keys(
        [(seq_id, 0, 0) for seq_id in bgcs_by_contig.keys()],
        contig_display_names,
        all_sequence_ids,
        genome_file,
    )

    with open(output_path, "w", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["sequence_id", "interval_start", "interval_end", *labels])
        writer.writerow(["", "", "", *tools])

        for normalized_contig_id, _, _ in sorted_contigs:
            entries = sorted(bgcs_by_contig[normalized_contig_id], key=lambda x: (x[0], x[1]))
            if not entries:
                continue

            current_start, current_end = entries[0][0], entries[0][1]
            current_bgcs = [entries[0]]

            merged_intervals = []

            for start, end, tool, bgc in entries[1:]:
                if start <= current_end:
                    current_end = max(current_end, end)
                    current_bgcs.append((start, end, tool, bgc))
                else:
                    merged_intervals.append((current_start, current_end, current_bgcs))
                    current_start, current_end = start, end
                    current_bgcs = [(start, end, tool, bgc)]

            merged_intervals.append((current_start, current_end, current_bgcs))

            for interval_start, interval_end, interval_bgcs in merged_intervals:
                per_tool_bgcs: Dict[str, List] = defaultdict(list)
                for _, _, tool, bgc in interval_bgcs:
                    per_tool_bgcs[tool].append(bgc)

                row = [
                    contig_display_names[normalized_contig_id],
                    interval_start + 1,
                    interval_end,
                ]
                for tool in tools:
                    row.append(_collapse_multiple_bgcs(per_tool_bgcs.get(tool, [])))
                writer.writerow(row)