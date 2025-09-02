import gzip
import json
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union

import yaml

from src.genome_mining_result import GenomeMiningResult
from src.reporting.report_data import RunningMode


def open_file(file_path: Path) -> Union[TextIO, gzip.GzipFile]:
    """
    Open a file, automatically handling gzip compression if needed.

    Args:
        file_path: Path to the file to open

    Returns:
        File object that can be read
    """
    if file_path.suffix == ".gz":
        return gzip.open(file_path, "rt")
    return open(file_path, "r")


def get_json_from_file(filename: Path) -> Dict:
    """
    Read a JSON file and return the data as a dictionary.
    Supports gzip-compressed files.

    Args:
        filename (Path): The path to the JSON file.

    Returns:
        Dict: The data from the JSON file.
    """
    with open_file(filename) as f:
        json_data = json.load(f)
    return json_data


# ---- Functions to map BGC product to BGC class ----
def load_reverse_mapping(yaml_path: Path) -> Dict[str, str]:
    """Load mapping YAML and return product-to-class dictionary.

    Args:
        yaml_path (Path): Path to the YAML file containing the mapping.

    Returns:
        Dict[str, str]: A dictionary mapping product names to their main classes.
    """
    with open(yaml_path, "r") as f:
        mapping = yaml.safe_load(f)

    if mapping is None:
        return {}

    # Reverse mapping
    product_to_class = {}
    for main_class, products in mapping.items():
        for product in products:
            product_to_class[product] = main_class

    return product_to_class


def map_products(
    product_list: List[str], product_to_class: Dict[str, str]
) -> List[str]:
    """Map a list of products to their main classes.

    Args:
        product_list (List[str]): A list of product names to be mapped.
        product_to_class (Dict[str, str]): A dictionary mapping product names to their main classes.

    Returns:
        List[str]: A list of unique main classes corresponding to the input products.
    """
    mapped_class = set()
    for product in product_list:
        bgc_class = product_to_class.get(
            product, product
        )  # Fall back to itself if unmapped
        mapped_class.add(bgc_class)
    return list(mapped_class)


def determine_running_mode(
    reference_genome_mining_result: Optional[GenomeMiningResult],
    assembly_genome_mining_results: List[GenomeMiningResult],
) -> RunningMode:
    """
    Determine the running mode based on the genome mining results and reference mining result.
    The running mode can be one of the following:
    - COMPARE_TO_REFERENCE: If a reference genome mining result is provided.
    - COMPARE_TOOLS: If the input file labels are the same with same or different mining tools.
    - COMPARE_SAMPLES: If the input file labels are different but the same mining tool is used.
    - UNKNOWN: If the input file labels are different and different mining tools are used.

    Args:
        reference_genome_mining_result (GenomeMiningResult): The reference genome mining result.
        assembly_genome_mining_results (List[GenomeMiningResult]): List of genome mining results.

    Returns:
        RunningMode: The determined running mode.
    """
    different_mining_tools = not all(
        tool == assembly_genome_mining_results[0].mining_tool
        for tool in (result.mining_tool for result in assembly_genome_mining_results)
    )
    different_file_labels = not all(
        label == assembly_genome_mining_results[0].input_file_label
        for label in (
            result.input_file_label for result in assembly_genome_mining_results
        )
    )
    if reference_genome_mining_result is not None:
        if different_mining_tools:
            # Different mining tools are not allowed for the COMPARE_TO_REFERENCE mode.
            return RunningMode.UNKNOWN
        return RunningMode.COMPARE_TO_REFERENCE
    elif different_file_labels and different_mining_tools:
        return RunningMode.UNKNOWN
    elif len(assembly_genome_mining_results) == 1 or different_file_labels:
        return RunningMode.COMPARE_SAMPLES
    else:
        # If all mining results have the same file label regardless of the mining tools.
        return RunningMode.COMPARE_TOOLS


def get_file_label_from_path(file_path: Path) -> str:
    """
    Extract the file label from the file path.
    The file label is considered to be the name of the file without its extensions.
    Example: "example.txt.gz" -> "example", "kittens.fastq" -> "kittens",
    "best.sample.json" -> "best.sample".

    Args:
        file_path (Path): The path to the file.

    Returns:
        str: The file label.
    """
    if not file_path.is_file():
        raise ValueError(f"Provided path {file_path} is not a valid file.")

    compression_suffixes = [".gz", ".bz2", ".bgz", ".zst", ".xz", ".zip", ".bgzf"]

    if file_path.suffix in compression_suffixes:
        file_path = file_path.with_suffix(
            ""
        )  # Remove compression suffix for label extraction
    return file_path.with_suffix("").name  # Remove an extension


def get_base_extension(file_path: Path) -> str:
    """
    Get the base extension of a file, excluding any compression suffixes.
    Example: "example.txt.gz" -> ".txt", "kittens.fastq" -> ".fastq".

    Args:
        file_path (Path): The path to the file.

    Returns:
        str: The base extension of the file.
    """
    compression_suffixes = [".gz", ".bz2", ".bgz", ".zst", ".xz", ".zip", ".bgzf"]
    if file_path.suffix.lower() in compression_suffixes:
        return file_path.with_suffix("").suffix.lower()
    return file_path.suffix.lower()
