from dataclasses import dataclass, field
from typing import Dict, List, Optional
from typing import Literal


@dataclass
class Bgc:
    """
    Class for BGCs.

    Attributes:
        bgc_id (str): The BGC id.
        sequence_id (str): The BGC sequence id.
        start (int): The start position of the BGC.
        end (int): The end position of the BGC.
        is_complete (Literal["True", "False", "Unknown"]): Whether the BGC is complete (True, False, Unknown).
        product_types (list): The product types of the BGC.
        metadata (dict): The metadata of the BGC, e.g. tool-specific metadata.
    """

    bgc_id: str
    sequence_id: str
    start: int = 0
    end: int = 0
    is_complete: Literal["True", "False", "Unknown"] = "Unknown"
    product_types: List[str] = field(default_factory=list)
    metadata: Optional[Dict] = None


@dataclass
class GenomeMiningResult:
    """
    Class for genome mining results. Contains information about the input file, mining tool, and regions.

    Attributes:
        input_file (str): The input file name.
        mining_tool (str): The mining tool name.
        bgcs (list): The BGCs.
    """

    input_file: str
    mining_tool: str
    bgcs: List[Bgc] = field(default_factory=list)


@dataclass
class QuastResult:
    """
    Class for QUAST results.
    """

    input_file: str
