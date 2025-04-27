import re
from typing import List

from . import utils
from .genome_mining_result import Bgc, GenomeMiningResult, QuastResult


class InvalidInputException(Exception):
    """Exception raised when input file cannot be parsed by a specific parser."""

    pass


def parse_antismash_json(file_path: str) -> List[Bgc]:
    """Parse antiSMASH JSON format."""
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
                    products = qualifiers.get("product", [])
                    bgc_id = (
                        sequence_id + "." + qualifiers.get("region_number", ["1"])[0]
                    )
                    contig_edge = qualifiers.get("contig_edge", ["Unknown"])[0]
                    if contig_edge == "False":
                        is_complete = "True"
                    elif contig_edge == "True":
                        is_complete = "False"
                    else:
                        is_complete = "Unknown"
                    bgc = Bgc(
                        bgc_id=bgc_id,
                        sequence_id=sequence_id,
                        start=start,
                        end=end,
                        is_complete=is_complete,
                        product_types=products,
                        metadata=feature,
                    )
                    bgcs.append(bgc)
        return bgcs
    except Exception as e:
        raise InvalidInputException(f"Failed to parse antiSMASH format: {str(e)}")


def parse_gecco_tsv(file_path: str) -> List[Bgc]:
    """Parse GECCO TSV format."""
    try:
        # TODO: Implement GECCO TSV parsing
        raise NotImplementedError("GECCO TSV parsing not implemented yet")
    except Exception as e:
        raise InvalidInputException(f"Failed to parse GECCO TSV format: {str(e)}")


def parse_deepbgc_tsv(file_path: str) -> List[Bgc]:
    """Parse deepBGC TSV format."""
    try:
        # TODO: Implement deepBGC TSV parsing
        raise NotImplementedError("deepBGC TSV parsing not implemented yet")
    except Exception as e:
        raise InvalidInputException(f"Failed to parse deepBGC TSV format: {str(e)}")


def parse_deepbgc_json(file_path: str) -> List[Bgc]:
    """Parse deepBGC JSON format."""
    try:
        # TODO: Implement deepBGC JSON parsing
        raise NotImplementedError("deepBGC JSON parsing not implemented yet")
    except Exception as e:
        raise InvalidInputException(f"Failed to parse deepBGC JSON format: {str(e)}")


def parse_input_files(file_paths: List[str]) -> List[GenomeMiningResult]:
    """
    Parse input files by trying different parsers.

    Args:
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
                bgcs = parser(file_path)
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


def parse_quast_output_dir(quast_output_dir: str) -> List[QuastResult]:
    """Parse QUAST output directory."""
    try:
        # TODO: Implement QUAST output directory parsing
        raise NotImplementedError("QUAST output directory parsing not implemented yet")
    except Exception as e:
        raise InvalidInputException(f"Failed to parse QUAST output directory: {str(e)}")
