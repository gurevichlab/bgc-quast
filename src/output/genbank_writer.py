from pathlib import Path
from typing import List

from Bio import SeqIO
from Bio.SeqFeature import SeqFeature, FeatureLocation
from Bio.SeqRecord import SeqRecord

from src.genome_mining_result import GenomeMiningResult
from src.input_utils import open_file


class UnsupportedGenomeFormatError(Exception):
    pass


# Note some tools convert LOCUS/contig names to lowercase
# TODO: some tools might also skip everything after the first space (do we need to support this?)
def normalize_id(x):
    return str(x).strip().lower()


def make_bgc_feature(bgc, tool: str) -> SeqFeature:
    return SeqFeature(
        FeatureLocation(bgc.start, bgc.end + 1),  # Biopython uses 0-based, end-exclusive
        type="BGC",
        qualifiers={
            "product": [",".join(bgc.product_types)],
            "tool": [str(tool)],
            "bgc_id": [str(bgc.bgc_id)],
            "completeness": [str(bgc.completeness)],
        },
    )


def prepare_fasta_record_for_genbank(record):
    new_record = SeqRecord(
        seq=record.seq,
        id=record.id,
        name=record.name,
        description=record.description or record.id,
    )
    new_record.annotations["molecule_type"] = "DNA"
    new_record.features = []
    return new_record


def load_input_genome_records(genome_file: Path):
    format_error_msg = (
        f"Input genome file ({genome_file}) must be in GenBank or FASTA format; "
        "other formats are currently not supported."
    )

    for format in ("genbank", "fasta"):
        with open_file(genome_file) as handle:
            try:
                records = list(SeqIO.parse(handle, format))
            except Exception:
                records = []

        if records:
            if format == "fasta":
                records = [prepare_fasta_record_for_genbank(record) for record in records]
            return records

    raise UnsupportedGenomeFormatError(format_error_msg)


def write_genbank(
    genome_file: Path,
    genome_mining_results: List[GenomeMiningResult],
    output_path: Path,
):
    records = load_input_genome_records(genome_file)

    record_by_id = {}
    for record in records:
        key = normalize_id(record.id)
        if key in record_by_id:
            raise ValueError(f"Duplicate record ID after normalization: {record.id}")
        record_by_id[key] = record

    missing_ids = set()
    invalid_bgcs = []

    for result in genome_mining_results:
        tool = result.mining_tool

        for bgc in result.bgcs:
            record = record_by_id.get(normalize_id(bgc.sequence_id))
            if record is None:
                missing_ids.add(str(bgc.sequence_id))
                continue

            record_len = len(record.seq)

            if bgc.start is None or bgc.end is None:
                invalid_bgcs.append(
                    f"{bgc.bgc_id}: missing coordinates on sequence {bgc.sequence_id}"
                )
                continue

            if bgc.start < 0 or bgc.end < 0:
                invalid_bgcs.append(
                    f"{bgc.bgc_id}: invalid coordinates {bgc.start}..{bgc.end} "
                    f"on sequence {bgc.sequence_id} (coordinates must be >= 1)"
                )
                continue

            if bgc.start > bgc.end:
                invalid_bgcs.append(
                    f"{bgc.bgc_id}: invalid coordinates {bgc.start}..{bgc.end} "
                    f"on sequence {bgc.sequence_id} (start > end)"
                )
                continue

            if bgc.end >= record_len:
                invalid_bgcs.append(
                    f"{bgc.bgc_id}: invalid coordinates {bgc.start}..{bgc.end} "
                    f"on sequence {bgc.sequence_id} (record length = {record_len})"
                )
                continue

            record.features.append(make_bgc_feature(bgc, tool))

    if missing_ids:
        raise ValueError(
            "Could not find matching GenBank record(s) for sequence ID(s). "
            "Have you provided the same genome sequence used for the genome mining? "
            + ", ".join(sorted(missing_ids))
        )
    # TODO: uncomment once coordinate issues are fixed in the parsing module
    # if invalid_bgcs:
    #     raise ValueError(
    #         "Some BGC coordinates are invalid:\n" + "\n".join(invalid_bgcs)
    #     )

    SeqIO.write(records, output_path, "genbank")