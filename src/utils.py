import gzip
import json
import yaml
from pathlib import Path
from typing import Dict, TextIO, Union, List


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
    """Load mapping YAML and return product-to-class dictionary."""
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


def map_products(product_list: List[str], product_to_class: Dict[str, str]) -> List[str]:
    """ Map a list of products to their main classes. """
    mapped_class = set()
    for product in product_list:
        bgc_class = product_to_class.get(product, product)  # Fall back to itself if unmapped
        mapped_class.add(bgc_class)
    return list(mapped_class)

