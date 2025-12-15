import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

import pandas as pd
from Bio import SeqIO

from . import input_utils
from .config import Config
from .genome_mining_result import (
    AlignmentInfo,
    Bgc,
    ContigData,
    GenomeMiningResult,
    QuastResult,
)
from .input_utils import (
    get_file_label_from_path,
    load_reverse_mapping,
    map_products,
    open_file,
)
from .logger import Logger


class InvalidInputException(Exception):
    """Exception raised when input file cannot be parsed by a specific parser."""

    pass


def _count_genes_in_bgc(bgc: Bgc, contig_data: Optional[ContigData]) -> int:
    """Counts the number of genes in a BGC."""
    if not contig_data:
        return 0
    count = 0
    for gene_start, gene_end in contig_data.genes:
        if bgc.start <= gene_start and gene_end <= bgc.end:
            count += 1
    return count


def parse_antismash_json(
    config: Config, file_path: Path, seq_data_map: Union[Dict[str, ContigData], None]
) -> List[Bgc]:
    """Parse antiSMASH JSON format."""
    product_to_class = load_reverse_mapping(
        config.product_mapping_config.product_yamls["antismash_product_mapping"]
    )

    try:
        json_data = input_utils.get_json_from_file(file_path)
        records = json_data["records"]
        bgcs = list()
        for record in records:
            for feature in record["features"]:
                if feature["type"] == "region":
                    location = feature["location"]
                    # Extract start and end positions from the location string
                    # Example location: "[0:39844](+)", "[0:39844](-)", "[0:39844]"
                    pattern = r"\[(\d+):(\d+)\](?:\((\+|-)\))?"
                    match = re.match(pattern, location)
                    if match:
                        start = int(match.group(1))
                        end = int(match.group(2))
                    else:
                        raise ValueError(f"Invalid location format: {location}")
                    sequence_id = record["id"]
                    qualifiers = feature.get("qualifiers", {})

                    # Get a list of products and classes
                    # TODO: checkme
                    products_raw = qualifiers.get("product", ["Unknown product"])
                    mapped_products = map_products(products_raw, product_to_class)
                    # TODO: extend metadata if needed, e.g., with feature content
                    metadata = {"product_details": products_raw}

                    bgc_id = (
                        sequence_id + "." + qualifiers.get("region_number", ["1"])[0]
                    )
                    completeness = get_completeness(
                        config, seq_data_map, sequence_id, start, end
                    )
                    bgc = Bgc(
                        bgc_id=bgc_id,
                        sequence_id=sequence_id,
                        start=start,
                        end=end,
                        completeness=completeness,
                        product_types=mapped_products,
                        metadata=metadata,
                    )
                    if seq_data_map and sequence_id in seq_data_map:
                        bgc.gene_count = _count_genes_in_bgc(
                            bgc, seq_data_map.get(sequence_id)
                        )
                    bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse antiSMASH format: {str(e)}")


def parse_gecco_tsv(
    config: Config, file_path: Path, seq_data_map: Union[Dict[str, ContigData], None]
) -> List[Bgc]:
    """Parse GECCO TSV format."""
    product_to_class = load_reverse_mapping(
        config.product_mapping_config.product_yamls["gecco_product_mapping"]
    )

    try:
        df = pd.read_csv(file_path, sep="\t")
        # Check if this is a GECCO TSV output
        if "type" not in df.columns.tolist():
            raise InvalidInputException("Not GECCO TSV - 'type' is missing")

        bgcs = list()

        # Predefine columns with Class probability
        product_probability_cols = [
            "alkaloid_probability",
            "nrp_probability",
            "polyketide_probability",
            "ripp_probability",
            "saccharide_probability",
            "terpene_probability",
        ]
        for index, row in df.iterrows():
            sequence_id = row["sequence_id"]
            bgc_id = row["cluster_id"].split("cluster_")[-1]
            start = row["start"]
            end = row["end"]

            # Get a list of products and classes
            products = row["type"].split(";")
            products_raw = [p.strip() for p in products if p.strip()]
            mapped_product = map_products(products_raw, product_to_class)

            # Build metadata
            metadata = {}
            if "Unknown product" in mapped_product:
                # Find the class with max probability
                max_col = str(row[product_probability_cols].idxmax())
                max_val = row[max_col]

                clean_col = max_col.replace("_probability", "")

                mapped_column = map_products([clean_col], product_to_class)

                metadata = {
                    "closest_product_match": mapped_column[0],  # mapped main class
                    "probability": round(max_val, 3),
                }

            completeness = get_completeness(
                config, seq_data_map, sequence_id, start, end
            )

            # Create the Bgc object
            bgc = Bgc(
                bgc_id=f"{sequence_id}_{bgc_id}",
                sequence_id=sequence_id,
                start=start,
                end=end,
                completeness=completeness,
                product_types=mapped_product,
                metadata=metadata,
            )
            if seq_data_map and sequence_id in seq_data_map:
                bgc.gene_count = _count_genes_in_bgc(bgc, seq_data_map.get(sequence_id))

            bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse GECCO TSV format: {str(e)}")


def parse_deepbgc_tsv(
    config: Config, file_path: Path, seq_data_map: Union[Dict[str, ContigData], None]
) -> List[Bgc]:
    """Parse deepBGC TSV format."""
    product_to_class = load_reverse_mapping(
        config.product_mapping_config.product_yamls["deepbgc_product_mapping"]
    )
    try:
        df = pd.read_csv(file_path, sep="\t")
        # Check if this is a deepBGC TSV output
        if "product_class" not in df.columns.tolist():
            raise InvalidInputException("Not deepBGC TSV - product_class is missing")

        # Replace NaN in the product_class
        df["product_class"] = df["product_class"].fillna("Unknown product")

        # Initialize the counter of BGCs within the sequence_id
        sequence_id_counter = defaultdict(int)

        bgcs = list()

        # Predefine columns with Class probability
        product_probability_cols = [
            "Alkaloid",
            "NRP",
            "Other",
            "Polyketide",
            "RiPP",
            "Saccharide",
            "Terpene",
        ]
        for index, row in df.iterrows():
            sequence_id = row["sequence_id"]
            sequence_id_counter[sequence_id] += 1
            bgc_number = sequence_id_counter[sequence_id]
            bgc_id = f"{sequence_id}_{bgc_number}"
            start = row["nucl_start"]
            end = row["nucl_end"]

            # Get a list of products and classes
            products = row["product_class"].split("-")
            products_raw = [p.strip() for p in products if p.strip()]
            mapped_product = map_products(products_raw, product_to_class)

            # Build metadata
            metadata = {}
            if "Unknown product" in mapped_product:
                # Find the class with max probability
                max_col = str(row[product_probability_cols].idxmax())
                max_val = row[max_col]

                mapped_column = map_products([max_col], product_to_class)

                metadata = {
                    "closest_product_match": mapped_column[0],  # mapped main class
                    "probability": round(max_val, 3),
                }

            completeness = get_completeness(
                config, seq_data_map, sequence_id, start, end
            )

            # Create a Bgc object
            bgc = Bgc(
                bgc_id=bgc_id,
                sequence_id=sequence_id,
                start=start,
                end=end,
                completeness=completeness,
                product_types=mapped_product,
                metadata=metadata,
            )
            if seq_data_map and sequence_id in seq_data_map:
                bgc.gene_count = _count_genes_in_bgc(bgc, seq_data_map.get(sequence_id))

            bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse deepBGC TSV format: {str(e)}")


def parse_deepbgc_json(
    config: Config, file_path: Path, seq_data_map: Union[Dict[str, ContigData], None]
) -> List[Bgc]:
    """Parse deepBGC JSON format."""
    product_to_class = load_reverse_mapping(
        config.product_mapping_config.product_yamls["deepbgc_product_mapping"]
    )

    try:
        data = input_utils.get_json_from_file(file_path)

        bgcs = list()

        # Loop over each record (e.g., contig/scaffold)
        for record in data.get("records", []):
            sequence_id = record.get("name")

            # Each subregion is a BGC
            subregions = record.get("subregions", [])
            for idx, subregion in enumerate(subregions, start=1):
                start = subregion.get("start")
                end = subregion.get("end")

                # Get a list of products and classes
                product_class_raw = subregion.get("details", {}).get(
                    "product_class", "Unknown product"
                )
                products = product_class_raw.split("-")
                products_raw = [p.strip() for p in products if p.strip()]

                if "no confident class" in [p for p in products_raw]:
                    mapped_product = ["Unknown product"]
                else:
                    mapped_product = map_products(products_raw, product_to_class)

                # Build metadata
                metadata = {}
                metadata["product_details"] = product_class_raw
                completeness = get_completeness(
                    config, seq_data_map, sequence_id, start, end
                )

                bgc = Bgc(
                    bgc_id=f"{sequence_id}_{idx}",
                    sequence_id=sequence_id,
                    start=start,
                    end=end,
                    completeness=completeness,
                    product_types=mapped_product,
                    metadata=metadata,
                )
                if seq_data_map and sequence_id in seq_data_map:
                    bgc.gene_count = _count_genes_in_bgc(
                        bgc, seq_data_map.get(sequence_id)
                    )

                bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse deepBGC format: {str(e)}")


def parse_input_mining_result_files(
    log: Logger,
    config: Config,
    file_paths: List[Path],
    genome_data: Optional[List[Path]] = None,
) -> List[GenomeMiningResult]:
    """
    Parse input files by trying different parsers.

    Args:
        log: Logger instance for logging information
        config: Config
        file_paths: List of input file paths
        genome_data: Optional genome data for sequence completeness estimation

    Returns:
        A list of GenomeMiningResult objects
    """

    # Get genome sequence data.
    genome_seq_data_maps: Dict[str, Dict[str, ContigData]] = {}
    if genome_data:
        try:
            genome_seq_data_maps = parse_genome_data(genome_data)
        except Exception as e:
            log.error(f"Failed to parse genome data: {str(e)}")
            raise e

    parsers = {
        parse_antismash_json: "antiSMASH",
        parse_gecco_tsv: "GECCO",
        parse_deepbgc_tsv: "deepBGC",
        parse_deepbgc_json: "deepBGC",
    }

    results = []

    for file_path in file_paths:
        if not file_path.exists():
            raise InvalidInputException(f"Input file does not exist: {file_path}")

        # Get sequence length map for the current file.
        try:
            seq_data_map = get_seq_data_map(genome_seq_data_maps, file_path)
        except Exception as e:
            log.warning(
                f"Failed to get sequence length map for {file_path}  -- BGC"
                f" completeness will not be calculated for this input. "
                f"Problem occurred: {str(e)}"
            )
            seq_data_map = None

        for parser, tool_name in parsers.items():
            try:
                bgcs = parser(config, file_path, seq_data_map)

                # Apply length-based filtering
                min_len = config.min_bgc_length
                filtered_count = 0

                if min_len is None or min_len == 0:
                    # No filtering requested
                    kept_bgcs = bgcs
                else:
                    kept_bgcs = []
                    for bgc in bgcs:
                        length = bgc.end - bgc.start
                        # Same convention as mean_bgc_length: use end - start
                        if length >= min_len:
                            kept_bgcs.append(bgc)
                        else:
                            filtered_count += 1

                if filtered_count > 0:
                    log.info(
                        f"Filtered out {filtered_count} BGC(s) shorter than "
                        f"{min_len} bp for {file_path}"
                    )

                file_label = get_file_label_from_path(file_path)
                results.append(
                    GenomeMiningResult(
                        input_file=file_path.resolve(),
                        input_file_label=file_label,
                        display_label=file_label,
                        mining_tool=tool_name,
                        bgcs=kept_bgcs,
                        genome_data=seq_data_map,
                        filtered_bgcs_by_length=filtered_count,
                    )
                )
                break  # If parsing succeeded, move to next file
            except InvalidInputException:
                continue  # Try next parser
            except Exception as e:
                raise Exception(f"Unexpected error while parsing {file_path}: {str(e)}")
        else:
            raise InvalidInputException(
                f"Could not parse file {file_path} with any available parser"
            )

    return results


def get_seq_data_map(
    genome_seq_data_maps: Dict[str, Dict[str, ContigData]], file_path: Path
) -> Optional[Dict[str, ContigData]]:
    """
    Get sequence length map for a given file path.

    Args:
        genome_seq_data_maps: Dictionary mapping file label to a dict mapping sequence
        name to sequence length
        file_path: Path to the input file

    Returns:
        Sequence length map for the given file path, or None if not found
    """
    seq_data_map: Optional[Dict[str, ContigData]] = None

    if genome_seq_data_maps is not None:
        seq_data_map = genome_seq_data_maps.get(
            get_file_label_from_path(file_path), None
        )

    # If genome_seq_data_maps is None, try to get the sequence length map from the file
    # directly.
    if seq_data_map is None:
        seq_data_map = get_genome_data_from_mining_result(file_path)
    return seq_data_map


def parse_reference_genome_mining_result(
    log: Logger,
    config: Config,
    file_path: Path,
    ref_genome_data: Union[Path, None],
) -> GenomeMiningResult:
    """
    Parse reference genome mining result file.

    Args:
        config: Config
        file_path: Path to the reference genome mining result file
        genome_data: Optional genome data for BGC completeness estimation

    Returns:
        GenomeMiningResult object for the reference genome
    """
    return parse_input_mining_result_files(
        log,
        config,
        [file_path],
        [ref_genome_data] if ref_genome_data else None,
    )[0]


def parse_quast_output_dir(quast_output_dir: Path) -> List[QuastResult]:
    """Parse QUAST output directory.
    Args:
        quast_output_dir: Path to the QUAST output directory
    Returns:
    """
    try:
        # Read all .coords files in quast_output_dir/contigs_reports/minimap_output
        quast_coords_dir = quast_output_dir / "contigs_reports" / "minimap_output"
        if not quast_coords_dir.exists():
            raise InvalidInputException(
                f"QUAST output directory does not exist: {quast_coords_dir}"
            )
        quast_results = []
        for coords_file in quast_coords_dir.glob("*.coords"):
            with open(coords_file, "r") as f:
                lines = f.readlines()
            quast_result = QuastResult(
                input_dir=quast_output_dir,
                input_file_label=get_file_label_from_path(coords_file),
            )
            for line in lines:
                line = line.split(" | ")
                ref_start, ref_end = map(int, line[0].split())
                assembly_start, assembly_end = map(int, line[1].split())
                len_diff = abs(int(line[2].split()[0]) - int(line[2].split()[1]))
                ref_seq_id, assembly_seq_id = line[4].split()
                quast_result.assembly_sequences[assembly_seq_id].append(
                    AlignmentInfo(
                        assembly_seq_id,
                        ref_seq_id,
                        ref_start,
                        ref_end,
                        assembly_start,
                        assembly_end,
                        len_diff,
                    )
                )
                quast_result.reference_sequences[ref_seq_id].append(
                    AlignmentInfo(
                        assembly_seq_id,
                        ref_seq_id,
                        ref_start,
                        ref_end,
                        assembly_start,
                        assembly_end,
                        len_diff,
                    )
                )
            quast_results.append(quast_result)
        if not quast_results:
            raise InvalidInputException(
                f"No QUAST results found in the output directory: {quast_output_dir}"
            )
        return quast_results
    except Exception as e:
        raise InvalidInputException(f"Failed to parse QUAST output directory: {str(e)}")


def parse_genome_data(file_paths: List[Path]) -> Dict[str, Dict[str, ContigData]]:
    """
    Parse genome data from FASTA or GBFF files, including gzipped files.

    Args:
        file_paths: List of paths to the genome data files.

    Returns:
        Dictionary mapping file label to a dict mapping sequence name to sequence
        length.
    """
    result: Dict[str, Dict[str, ContigData]] = {}
    for file_path in file_paths:
        label = get_file_label_from_path(file_path)
        contigs: Dict[str, ContigData] = {}

        base_extension = input_utils.get_base_extension(file_path)
        if base_extension in [".fa", ".fasta", ".fna"]:
            try:
                with open_file(file_path) as handle:
                    for record in SeqIO.parse(handle, "fasta"):
                        contigs[record.id] = ContigData(seq_len=len(record.seq))
            except Exception as e:
                raise Exception(f"Error parsing FASTA file {file_path}: {str(e)}")
        elif base_extension in [".gb", ".gbff", ".gbk"]:
            try:
                with open_file(file_path) as handle:
                    for record in SeqIO.parse(handle, "genbank"):
                        genes = [
                            (int(f.location.start), int(f.location.end))
                            for f in record.features
                            if f.type in ["gene", "CDS"]
                        ]
                        contigs[record.id] = ContigData(
                            seq_len=len(record.seq), genes=genes
                        )
            except Exception as e:
                raise Exception(f"Error parsing GenBank file {file_path}: {str(e)}")
        else:
            raise ValueError(f"Unsupported file extension for genome data: {file_path}")

        result[label] = contigs
    return result


def get_genome_data_from_mining_result(
    file_path: Path,
) -> Optional[Dict[str, ContigData]]:
    """
    Parse genome data from the input file if it's an antiSMASH JSON.
    The function extracts sequences (contigs) from the 'records' and computes their
    lengths.

    Args:
        file_path: Path to the input file.

    Returns:
        Dictionary mapping sequence name to computed sequence length, or None if not
        a valid antiSMASH JSON.
    """
    if input_utils.get_base_extension(file_path) != ".json":
        return None

    try:
        data = input_utils.get_json_from_file(file_path)
        records = data.get("records", [])
        contigs = {}
        for record in records:
            if "id" in record and "seq" in record and "data" in record["seq"]:
                genes = [
                    (
                        int(f["location"].split("[")[1].split(":")[0]),
                        int(f["location"].split(":")[1].split("]")[0]),
                    )
                    for f in record.get("features", [])
                    if f.get("type") == "gene"
                ]
                contigs[record["id"]] = ContigData(
                    seq_len=len(record["seq"]["data"]), genes=genes
                )
        return contigs if contigs else None
    except (json.JSONDecodeError, TypeError, AttributeError, KeyError):
        return None


def get_completeness(
    config: Config,
    seq_data_map: Union[dict[str, ContigData], None],
    sequence_id: str,
    start: int,
    end: int,
) -> Literal["Complete", "Incomplete", "Unknown completeness"]:
    """
    Get the completeness status of a BGC based on the corresponding sequence length.

    Args:
        config (Config): The configuration object containing completeness margin.
        seq_data_map (dict): A dictionary mapping sequence IDs to their lengths.
        sequence_id (str): The ID of the sequence to check.
        start (int): The start position of the BGC in the sequence.
        end (int): The end position of the BGC in the sequence.

    Returns:
        str: "Complete", "Incomplete", or "Unknown completeness" based on the BGC's completeness.
    """
    if seq_data_map and sequence_id in seq_data_map:
        completeness = (
            "Complete"
            if end + config.bgc_completeness_margin <= seq_data_map[sequence_id].seq_len
            and start >= config.bgc_completeness_margin
            else "Incomplete"
        )
    else:
        completeness = "Unknown completeness"
    return completeness
