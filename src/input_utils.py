import gzip
import json
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union

import yaml

from src.genome_mining_result import GenomeMiningResult
from src.reporting.report_data import RunningMode
from src.option_parser import ValidationError


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
    mode: str,
    reference_genome_mining_result: Optional[GenomeMiningResult],
    assembly_genome_mining_results: List[GenomeMiningResult],
) -> RunningMode:
    """
    Determine and validate the running mode based on the requested mode and
    the available genome mining results.

    - If mode == "auto", try to infer the running mode from the inputs
      (using labels and mining tools) and return one of:
      COMPARE_TO_REFERENCE, COMPARE_TOOLS, COMPARE_SAMPLES.
      If inference fails or inputs are inconsistent, raise ValidationError with an explanation.

    - If mode is one of the explicit modes ("compare-reference",
      "compare-tools", "compare-samples"), validate that the inputs are
      consistent with that mode and return the corresponding RunningMode.
      If validation fails, raise ValidationError with an explanation.

    The running mode can be one of the following:
    - COMPARE_TO_REFERENCE: If a reference genome mining result is provided.
    - COMPARE_TOOLS: If the input file labels are the same with same or different mining tools.
    - COMPARE_SAMPLES: If the input file labels are different but the same mining tool is used.
    - UNKNOWN: If the input file labels are different and different mining tools are used.

    Args:
        mode (str): Requested mode ("auto", "compare-reference", "compare-tools", "compare-samples").
        reference_genome_mining_result (GenomeMiningResult): The reference genome mining result.
        assembly_genome_mining_results (List[GenomeMiningResult]): List of genome mining results.

    Returns:
        RunningMode: The determined running mode.
    """

    has_reference = reference_genome_mining_result is not None
    num_assemblies = len(assembly_genome_mining_results)

    if num_assemblies == 0:
        raise ValidationError(
            "No genome mining results were provided. "
            "Please specify at least one genome mining result file."
        )

    distinct_tools = {
        result.mining_tool for result in assembly_genome_mining_results
    }

    # ----- AUTO MODE -----
    if mode == "auto":
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

        if has_reference:
            if different_mining_tools:
                raise ValidationError(
                    "Auto mode could not determine the running mode: "
                    "several mining tools were detected but reference was provided. Please ensure that reference and "
                    "input genomes are mined with the same tool."
                )
            return RunningMode.COMPARE_TO_REFERENCE

        # No reference
        if different_file_labels and different_mining_tools:
            raise ValidationError(
                "Auto mode could not determine the running mode: "
                "genome mining inputs have different file labels and different mining tools. "
                "Please either rename the files or rerun with --mode compare-tools or --mode compare-samples "
                "explicitly."
            )
        elif num_assemblies == 1 or different_file_labels:
            return RunningMode.COMPARE_SAMPLES
        else:
            # All file labels are the same regardless of tools
            return RunningMode.COMPARE_TOOLS

    # ----- EXPLICIT MODES -----
    if mode == "compare-reference":
        # Rules:
        # - reference must be present
        # - at least one assembly
        # - exactly one mining tool across reference + assemblies
        if not has_reference:
            raise ValidationError(
                "--mode compare-reference requires reference data, but no "
                "reference genome mining result was found."
            )

        tools_with_reference = set(distinct_tools)
        tools_with_reference.add(
            reference_genome_mining_result.mining_tool  # type: ignore[union-attr]
        )
        if len(tools_with_reference) != 1:
            raise ValidationError(
                "--mode compare-reference requires a single mining tool for "
                "reference and input genomes. Found tools: "
                f"{', '.join(sorted(tools_with_reference))}."
            )

        return RunningMode.COMPARE_TO_REFERENCE

    if mode == "compare-tools":
        # Rules:
        # - no reference
        # - at least 2 assemblies
        # - >= 1 mining tool
        if has_reference:
            raise ValidationError(
                "--mode compare-tools does not support reference data. "
                "Please remove the reference genome mining result or use "
                "--mode compare-reference."
            )

        if num_assemblies < 2:
            raise ValidationError(
                "--mode compare-tools requires at least 2 genome mining runs. "
                f"Found only {num_assemblies}."
            )

        return RunningMode.COMPARE_TOOLS

    if mode == "compare-samples":
        # Rules:
        # - no reference
        # - at least 1 assembly (already guaranteed)
        # - exactly 1 mining tool across all assemblies
        if has_reference:
            raise ValidationError(
                "--mode compare-samples does not support reference data. "
                "Please remove the reference genome mining result or use "
                "--mode compare-reference."
            )

        if len(distinct_tools) != 1:
            raise ValidationError(
                "--mode compare-samples requires a single mining tool for all "
                "input genomes. Found tools: "
                f"{', '.join(sorted(distinct_tools))}."
            )

        return RunningMode.COMPARE_SAMPLES

    # Should not happen because argparse restricts choices,
    # but keep a defensive branch.
    raise ValidationError(f"Unsupported mode: {mode}")



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

    # Strip primary extension (e.g., .json, .tsv)
    file_path = file_path.with_suffix("")

    # TEMPORARY FIX: strip tool/aux markers from the end (e.g., '.antismash', '.clusters')
    # TODO: re-write the mechanism for mode choosing
    temp_markers = {".antismash", ".clusters", ".bgc"}
    bio_suffixes = {".fasta", ".fa", ".fna", ".fastq", ".fq"}

    while file_path.suffix in temp_markers:
        file_path = file_path.with_suffix("")

        # If a raw-data suffix remains, drop it
    if file_path.suffix in bio_suffixes:
        file_path = file_path.with_suffix("")

    return file_path.name  # Remove an extension


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
