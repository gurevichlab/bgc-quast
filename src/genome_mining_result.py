from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, Optional


@dataclass
class Bgc:
    """
    Class for BGCs.

    Attributes:
        bgc_id (str): The BGC id.
        sequence_id (str): The BGC sequence id.
        start (int): The start position of the BGC.
        end (int): The end position of the BGC.
        completeness (Literal["Complete", "Incomplete", "Unknown"]): Whether the BGC is complete (Complete, Incomplete, Unknown).
        product_types (list): The product types of the BGC.
        metadata (dict): The metadata of the BGC, e.g. tool-specific metadata.
    """

    bgc_id: str
    sequence_id: str
    start: int = 0
    end: int = 0
    completeness: Literal["Complete", "Incomplete", "Unknown"] = "Unknown"
    product_types: List[str] = field(default_factory=list)
    metadata: Optional[Dict] = None


@dataclass
class GenomeMiningResult:
    """
    Class for genome mining results. Contains information about the input file, mining tool, and regions.

    Attributes:
        input_file (Path): The input file name.
        input_file_label (str): The input file label.
        mining_tool (str): The mining tool name.
        bgcs (list): The BGCs.
    """

    input_file: Path
    input_file_label: str
    mining_tool: str
    bgcs: List[Bgc] = field(default_factory=list)


@dataclass
class AlignmentInfo:
    """
    Class for alignment information between assembly and reference sequences.

    Attributes:
        assembly_seq_id (str): Assembly sequence ID
        ref_seq_id (str): Reference sequence ID
        ref_start (int): Start position in reference
        ref_end (int): End position in reference
        assembly_start (int): Start position in assembly
        assembly_end (int): End position in assembly
        len_diff (int): Length difference between aligned regions
    """

    assembly_seq_id: str
    ref_seq_id: str
    ref_start: int
    ref_end: int
    assembly_start: int
    assembly_end: int
    len_diff: int


@dataclass
class QuastResult:
    """
    Class for QUAST results.
    Attributes:
        input_dir (Path): The input directory.
        input_file_label (str): The input file label.
        assembly_sequences (dict): A dictionary of alignment info for each assembly sequence.
        reference_sequences (dict): A dictionary of alignment info for each reference sequence.
    """

    input_dir: Path
    input_file_label: str
    assembly_sequences: Dict[str, List[AlignmentInfo]] = field(
        default_factory=lambda: defaultdict(list)
    )
    reference_sequences: Dict[str, List[AlignmentInfo]] = field(
        default_factory=lambda: defaultdict(list)
    )
