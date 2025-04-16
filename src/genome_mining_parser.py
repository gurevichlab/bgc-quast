from typing import Dict, List

from .genome_mining_result import GenomeMiningResult, Bgc, QuastResult


class InvalidInputException(Exception):
    """Exception raised when input file cannot be parsed by a specific parser."""

    pass


def parse_antismash_json(file_path: str) -> Dict[str, List[Bgc]]:
    """Parse antiSMASH JSON format."""
    try:
        # TODO: Implement antiSMASH JSON parsing
        raise NotImplementedError("antiSMASH JSON parsing not implemented yet")
    except Exception as e:
        raise InvalidInputException(f"Failed to parse antiSMASH format: {str(e)}")


def parse_gecco_tsv(file_path: str) -> Dict[str, List[Bgc]]:
    """Parse GECCO TSV format."""
    try:
        # TODO: Implement GECCO TSV parsing
        raise NotImplementedError("GECCO TSV parsing not implemented yet")
    except Exception as e:
        raise InvalidInputException(f"Failed to parse GECCO TSV format: {str(e)}")


def parse_deepbgc_tsv(file_path: str) -> Dict[str, List[Bgc]]:
    """Parse deepBGC TSV format."""
    try:
        # TODO: Implement deepBGC TSV parsing
        raise NotImplementedError("deepBGC TSV parsing not implemented yet")
    except Exception as e:
        raise InvalidInputException(f"Failed to parse deepBGC TSV format: {str(e)}")


def parse_deepbgc_json(file_path: str) -> Dict[str, List[Bgc]]:
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
    parsers = [
        parse_antismash_json,
        parse_gecco_tsv,
        parse_deepbgc_tsv,
        parse_deepbgc_json,
    ]

    results = []

    for file_path in file_paths:
        for parser in parsers:
            try:
                bgcs = parser(file_path)
                results.extend(GenomeMiningResult(file_path, parser.__name__, bgcs))
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
