import re
from pathlib import Path
import pandas as pd
from collections import defaultdict
from typing import List

from . import utils
from .genome_mining_result import Bgc, GenomeMiningResult, QuastResult
from .utils import load_reverse_mapping, map_products
from .config import Config


class InvalidInputException(Exception):
    """Exception raised when input file cannot be parsed by a specific parser."""

    pass


def parse_antismash_json(config: Config, file_path: Path) -> List[Bgc]:
    """Parse antiSMASH JSON format."""
    product_to_class = load_reverse_mapping(config.product_mapping_config.product_yamls["antismash_product_mapping"])

    try:
        json_data = utils.get_json_from_file(file_path)
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
                    products_raw = qualifiers.get('product', ['Unknown'])
                    mapped_products = map_products(products_raw, product_to_class)
                    # TODO: extend metadata if needed, e.g., with feature content
                    metadata = {'product_details': products_raw}

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
    product_to_class = load_reverse_mapping(config.product_mapping_config.product_yamls["gecco_product_mapping"])

    try:
        df = pd.read_csv(file_path, sep='\t')
        # Check if this is a GECCO TSV output
        if 'type' not in df.columns.tolist():
            raise InvalidInputException("Not GECCO TSV - 'type' is missing")

        bgcs = list()

        # Predefine columns with Class probabilitity
        product_probability_cols = [
            'alkaloid_probability',
            'nrp_probability',
            'polyketide_probability',
            'ripp_probability',
            'saccharide_probability',
            'terpene_probability'
        ]
        for index, row in df.iterrows():
            sequence_id = row['sequence_id']
            bgc_id = row['cluster_id'].split('cluster_')[-1]
            start = row['start']
            end = row['end']

            # Get a list of products and classes
            products = row['type'].split(';')
            products_raw = [p.strip() for p in products if p.strip()]
            mapped_product = map_products(products_raw, product_to_class)

            # Build metadata
            metadata = {}
            if 'Unknown' in mapped_product:

                # Find the class with max probability
                max_col = row[product_probability_cols].idxmax()
                max_val = row[max_col]

                clean_col = max_col.replace('_probability', '')

                mapped_column = map_products([clean_col], product_to_class)

                metadata = {
                    'closest_product_match': mapped_column[0],  # mapped main class
                    'probability': round(max_val, 3)
                }

            # Create the Bgc object
            bgc = Bgc(
                bgc_id=f'{sequence_id}_{bgc_id}',
                sequence_id=sequence_id,
                start=start,
                end=end,
                is_complete='Unknown', # No completeness information for now
                product_types=mapped_product,
                metadata=metadata
            )

            bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse GECCO TSV format: {str(e)}")


def parse_deepbgc_tsv(config: Config, file_path: Path) -> List[Bgc]:
    """Parse deepBGC TSV format."""
    product_to_class = load_reverse_mapping(config.product_mapping_config.product_yamls["deepbgc_product_mapping"])
    try:
        df = pd.read_csv(file_path, sep='\t')
        # Check if this is a deepBGC TSV output
        if 'product_class' not in df.columns.tolist():
            raise InvalidInputException("Not deepBGC TSV - product_class is missing")

        # Replace NaN in the product_class
        df['product_class'] = df['product_class'].fillna('Unknown')

        # Initialize the counter of BGCs within the sequence_id
        sequence_id_counter = defaultdict(int)

        bgcs = list()

        # Predefine columns with Class probabilitity
        product_probability_cols = [
            'Alkaloid',
            'NRP',
            'Other',
            'Polyketide',
            'RiPP',
            'Saccharide',
            'Terpene'
        ]
        for index, row in df.iterrows():
            sequence_id = row['sequence_id']
            sequence_id_counter[sequence_id] += 1
            bgc_number = sequence_id_counter[sequence_id]
            bgc_id = f"{sequence_id}_{bgc_number}"
            start = row['nucl_start']
            end = row['nucl_end']

            # Get a list of products and classes
            products = row['product_class'].split('-')
            products_raw = [p.strip() for p in products if p.strip()]
            mapped_product = map_products(products_raw, product_to_class)

            # Build metadata
            metadata = {}
            if 'Unknown' in mapped_product:
                # Find the class with max probability
                max_col = row[product_probability_cols].idxmax()
                max_val = row[max_col]

                mapped_column = map_products([max_col], product_to_class)

                metadata = {
                    'closest_product_match': mapped_column[0],  # mapped main class
                    'probability': round(max_val, 3)
                }

            # Create a Bgc object
            bgc = Bgc(
                bgc_id=bgc_id,
                sequence_id=sequence_id,
                start=start,
                end=end,
                is_complete='Unknown', # No completeness information for now
                product_types=mapped_product,
                metadata=metadata
            )

            bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse deepBGC TSV format: {str(e)}")


def parse_deepbgc_json(config: Config, file_path: Path) -> List[Bgc]:
    """Parse deepBGC TSV format."""
    product_to_class = load_reverse_mapping(config.product_mapping_config.product_yamls["deepbgc_product_mapping"])

    try:
        data = utils.get_json_from_file(file_path)

        bgcs = list()

        # Loop over each record (e.g., contig/scaffold)
        for record in data.get('records', []):
            sequence_id = record.get('name')

            # Each subregion is a BGC
            subregions = record.get('subregions', [])
            for idx, subregion in enumerate(subregions, start=1):
                try:
                    start = subregion.get('start')
                    end = subregion.get('end')
                except Exception:
                    print(f"Warning: Invalid location in sequence {sequence_id}. Skipping.")
                    continue

                # Get a list of products and classes
                product_class_raw = subregion.get('details', {}).get('product_class', 'Unknown')
                products = product_class_raw.split('-')
                products_raw = [p.strip() for p in products if p.strip()]

                if 'no confident class' in [p for p in products_raw]:
                    mapped_product = ["Unknown"]
                else:
                    mapped_product = map_products(products_raw, product_to_class)

                # Build metadata
                metadata = {}
                metadata['product_details'] = product_class_raw

                bgc = Bgc(
                    bgc_id=f'{sequence_id}_{idx}',
                    sequence_id=sequence_id,
                    start=start,
                    end=end,
                    is_complete="Unknown",  # No completeness information for now
                    product_types=mapped_product,
                    metadata=metadata
                )

                bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse deepBGC format: {str(e)}")


def parse_input_files(config: Config, file_paths: List[Path]) -> List[GenomeMiningResult]:
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
                results.append(GenomeMiningResult(file_path, tool_name, bgcs))
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
    """Parse QUAST output directory."""
    try:
        # TODO: Implement QUAST output directory parsing
        raise NotImplementedError("QUAST output directory parsing not implemented yet")
    except Exception as e:
        raise InvalidInputException(f"Failed to parse QUAST output directory: {str(e)}")
