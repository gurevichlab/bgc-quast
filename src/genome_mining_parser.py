import re
from collections import defaultdict
from pathlib import Path
from typing import List

import pandas as pd

from . import input_utils
from .config import Config
from .genome_mining_result import AlignmentInfo, Bgc, GenomeMiningResult, QuastResult
from .input_utils import load_reverse_mapping, map_products


class InvalidInputException(Exception):
    """Exception raised when input file cannot be parsed by a specific parser."""

    pass


def parse_antismash_json(config: Config, file_path: Path) -> List[Bgc]:
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
                    products_raw = qualifiers.get("product", ["Unknown"])
                    mapped_products = map_products(products_raw, product_to_class)
                    # TODO: extend metadata if needed, e.g., with feature content
                    metadata = {"product_details": products_raw}

                    bgc_id = (
                        sequence_id + "." + qualifiers.get("region_number", ["1"])[0]
                    )
                    # TODO: https://github.com/gurevichlab/bgc-quast/issues/9 -
                    # Implement a way to determine if the BGC is complete using contig length.
                    is_complete = "Unknown"
                    bgc = Bgc(
                        bgc_id=bgc_id,
                        sequence_id=sequence_id,
                        start=start,
                        end=end,
                        is_complete=is_complete,
                        product_types=mapped_products,
                        metadata=metadata,
                    )
                    bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse antiSMASH format: {str(e)}")


def parse_gecco_tsv(config: Config, file_path: Path) -> List[Bgc]:
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

        # Predefine columns with Class probabilitity
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
            if "Unknown" in mapped_product:
                # Find the class with max probability
                max_col = row[product_probability_cols].idxmax()
                max_val = row[max_col]

                clean_col = max_col.replace("_probability", "")

                mapped_column = map_products([clean_col], product_to_class)

                metadata = {
                    "closest_product_match": mapped_column[0],  # mapped main class
                    "probability": round(max_val, 3),
                }

            # Create the Bgc object
            bgc = Bgc(
                bgc_id=f"{sequence_id}_{bgc_id}",
                sequence_id=sequence_id,
                start=start,
                end=end,
                is_complete="Unknown",  # No completeness information for now
                product_types=mapped_product,
                metadata=metadata,
            )

            bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse GECCO TSV format: {str(e)}")


def parse_deepbgc_tsv(config: Config, file_path: Path) -> List[Bgc]:
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
        df["product_class"] = df["product_class"].fillna("Unknown")

        # Initialize the counter of BGCs within the sequence_id
        sequence_id_counter = defaultdict(int)

        bgcs = list()

        # Predefine columns with Class probabilitity
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
            if "Unknown" in mapped_product:
                # Find the class with max probability
                max_col = row[product_probability_cols].idxmax()
                max_val = row[max_col]

                mapped_column = map_products([max_col], product_to_class)

                metadata = {
                    "closest_product_match": mapped_column[0],  # mapped main class
                    "probability": round(max_val, 3),
                }

            # Create a Bgc object
            bgc = Bgc(
                bgc_id=bgc_id,
                sequence_id=sequence_id,
                start=start,
                end=end,
                is_complete="Unknown",  # No completeness information for now
                product_types=mapped_product,
                metadata=metadata,
            )

            bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse deepBGC TSV format: {str(e)}")


def parse_deepbgc_json(config: Config, file_path: Path) -> List[Bgc]:
    """Parse deepBGC TSV format."""
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
                    "product_class", "Unknown"
                )
                products = product_class_raw.split("-")
                products_raw = [p.strip() for p in products if p.strip()]

                if "no confident class" in [p for p in products_raw]:
                    mapped_product = ["Unknown"]
                else:
                    mapped_product = map_products(products_raw, product_to_class)

                # Build metadata
                metadata = {}
                metadata["product_details"] = product_class_raw

                bgc = Bgc(
                    bgc_id=f"{sequence_id}_{idx}",
                    sequence_id=sequence_id,
                    start=start,
                    end=end,
                    is_complete="Unknown",  # No completeness information for now
                    product_types=mapped_product,
                    metadata=metadata,
                )

                bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse deepBGC format: {str(e)}")


def parse_input_files(
    config: Config, file_paths: List[Path]
) -> List[GenomeMiningResult]:
    """
    Parse input files by trying different parsers.

    Args:
        config: Config
        file_paths: List of input file paths

    Returns:
        A list of GenomeMiningResult objects
    """
    parsers = {
        parse_antismash_json: "antiSMASH",
        parse_gecco_tsv: "GECCO",
        parse_deepbgc_tsv: "deepBGC TSV",
        parse_deepbgc_json: "deepBGC JSON",
    }

    results = []

    for file_path in file_paths:
        for parser, tool_name in parsers.items():
            try:
                bgcs = parser(config, file_path)
                results.append(
                    GenomeMiningResult(
                        file_path.resolve(),
                        file_path.name.split(".")[0],
                        tool_name,
                        bgcs,
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
                input_file_label=coords_file.name.split(".")[0],
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
