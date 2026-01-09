import gzip
import json
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union
from collections import defaultdict
from src.logger import Logger
import yaml

from src.genome_mining_result import GenomeMiningResult
from src.reporting.report_data import RunningMode
from src.option_parser import ValidationError


def validate_no_duplicate_paths(paths: list[Path]) -> None:
    normalized = [p.expanduser().resolve() for p in paths]
    duplicates = {p for p in normalized if normalized.count(p) > 1}
    if duplicates:
        raise ValidationError(
            "Duplicate input files were provided (each file must be listed only once):\n"
            + "\n".join(f"- {p}" for p in sorted(duplicates))
        )


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
    log: Optional[Logger] = None,
) -> RunningMode:
    """
    Determine and validate the running mode based on the requested mode and
    the available genome mining results.

    - If mode == "auto", try to infer the running mode from the inputs
      (using labels and mining tools) and return one of:
      COMPARE_TO_REFERENCE, COMPARE_TOOLS, COMPARE_SAMPLES.
      If inference fails or inputs are inconsistent, raise ValidationError with an explanation.

    - If mode is one of the explicit modes ("compare-to-reference",
      "compare-tools", "compare-samples"), validate that the inputs are
      consistent with that mode and return the corresponding RunningMode.
      If validation fails, raise ValidationError with an explanation.

    The running mode can be one of the following:
    - COMPARE_TO_REFERENCE: If a reference genome mining result is provided.
    - COMPARE_TOOLS: If the input file labels are the same with same or different mining tools.
    - COMPARE_SAMPLES: If the input file labels are different but the same mining tool is used.
    - UNKNOWN: If the input file labels are different and different mining tools are used.

    Args:
        mode (str): Requested mode ("auto", "compare-to-reference", "compare-tools", "compare-samples").
        reference_genome_mining_result (GenomeMiningResult): The reference genome mining result.
        assembly_genome_mining_results (List[GenomeMiningResult]): List of genome mining results.

    Returns:
        RunningMode: The determined running mode.
    """

    has_reference = reference_genome_mining_result is not None
    num_assemblies = len(assembly_genome_mining_results)

    distinct_tools = {
        result.mining_tool for result in assembly_genome_mining_results
    }

    # ----- AUTO MODE -----
    if mode == "auto":
        if log:
            log.info("Mode AUTO selected: choosing the running mode based on file labels "
                     "and mining tools.")
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
            if log:
                log.info("Reference detected.", indent=1)
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
            if num_assemblies == 1:
                if log:
                    log.info(
                        "Only one assembly provided, choosing COMPARE_SAMPLES.",
                        indent=1,
                    )
            elif log:
                log.info(
                    "Different file labels detected, choosing COMPARE_SAMPLES.",
                    indent=1,
                )
            return RunningMode.COMPARE_SAMPLES
        else:
            if log:
                log.info(
                    "All file labels identical, choosing COMPARE_TOOLS regardless of the provided mining tools.",
                    indent=1,
                )
            # All file labels are the same regardless of tools
            return RunningMode.COMPARE_TOOLS

    # ----- EXPLICIT MODES -----
    if mode == "compare-to-reference":
        if log:
            log.info("Mode COMPARE_REFERENCE selected")
        # Rules:
        # - reference must be present
        # - at least one assembly
        # - exactly one mining tool across reference + assemblies
        if not has_reference:
            raise ValidationError(
                "--mode compare-to-reference requires reference data, but no "
                "reference genome mining result was found."
            )

        tools_with_reference = set(distinct_tools)
        tools_with_reference.add(
            reference_genome_mining_result.mining_tool  # type: ignore[union-attr]
        )
        if len(tools_with_reference) != 1:
            raise ValidationError(
                "--mode compare-to-reference requires the same genome mining tool for "
                "reference and input genomes. Found tools: "
                f"{', '.join(sorted(tools_with_reference))}."
            )

        return RunningMode.COMPARE_TO_REFERENCE

    if mode == "compare-tools":
        if log:
            log.info("Mode COMPARE_TOOLS selected")
        # Rules:
        # - no reference
        # - at least 2 assemblies
        # - >= 1 mining tool
        if has_reference:
            raise ValidationError(
                "--mode compare-tools does not support reference data. "
                "Please remove the reference genome mining result or use "
                "--mode compare-to-reference."
            )

        if num_assemblies < 2:
            raise ValidationError(
                "--mode compare-tools requires at least 2 genome mining runs. "
                f"Found only {num_assemblies}."
            )

        return RunningMode.COMPARE_TOOLS

    if mode == "compare-samples":
        if log:
            log.info("Mode COMPARE_SAMPLES selected")
        # Rules:
        # - no reference
        # - at least 1 assembly
        # - exactly 1 mining tool across all assemblies
        if has_reference:
            raise ValidationError(
                "--mode compare-samples does not support reference data. "
                "Please remove the reference genome mining result or use "
                "--mode compare-to-reference."
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

def _parse_names_arg(names_arg: Optional[str]) -> Optional[List[str]]:
    if names_arg is None:
        return None
    names = [n.strip() for n in names_arg.split(",")]
    names = [n for n in names if n != ""]
    return names if names else None


def assign_and_deduplicate_display_labels(
    assembly_results: List[GenomeMiningResult],
    reference_result: Optional[GenomeMiningResult],
    names_arg: Optional[str],
    ref_name: Optional[str],
) -> List[dict]:
    """
    Assign display_label for assembly/reference results and deduplicate
    (display_label, mining_tool) collisions by suffixing _1, _2, ...

    - Strict: --names count must match number of assembly results.
    - --names affects assemblies only (in the order provided).
    - Reference uses --ref-name if provided; otherwise its current display_label
      (or input_file_label if display_label is None).
    - Never modifies input_file_label (auto-mode relies on it).

    Returns a renaming log for  messages
    """
    names = _parse_names_arg(names_arg)

    if names is not None and len(names) != len(assembly_results):
        raise ValidationError(
            f"--names must contain exactly {len(assembly_results)} name(s) "
            f"to match the number of input genome mining result files, but got {len(names)}."
        )

    # initial assignment
    for i, res in enumerate(assembly_results):
        if names is not None:
            res.display_label = names[i]
        else:
            # preserve whatever parser set; fall back if needed
            res.display_label = res.display_label or res.input_file_label

    if reference_result is not None:
        if ref_name is not None:
            reference_result.display_label = ref_name
        else:
            reference_result.display_label = (
                reference_result.display_label or reference_result.input_file_label
            )

    # suffix duplicates of (display_label, mining_tool)
    all_results = list(assembly_results)
    if reference_result is not None:
        all_results.append(reference_result)

    counts = defaultdict(int)
    renaming_log: List[dict] = []

    for res in all_results:
        base = res.display_label or res.input_file_label
        key = (base, res.mining_tool)

        counts[key] += 1
        idx = counts[key] - 1  # 0 for first occurrence
        new_label = base if idx == 0 else f"{base}_{idx}"

        if new_label != base:
            renaming_log.append(
                {"path": str(res.input_file), "old_label": base, "new_label": new_label}
            )
            res.display_label = new_label

    return renaming_log