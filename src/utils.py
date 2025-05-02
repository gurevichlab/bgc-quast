import gzip
import json
from pathlib import Path
from typing import Dict, TextIO, Union


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
