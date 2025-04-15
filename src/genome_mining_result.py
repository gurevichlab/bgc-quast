from dataclasses import dataclass, field
from typing import Dict, List, Optional
from typing import Literal


@dataclass
class Region:
    """
    Class for regions (BGCs).

    Attributes:
        contig_id (str): The region contig id.
        start (int): The start position of the region.
        end (int): The end position of the region.
        is_complete (Literal["True", "False", "Unknown"]): Whether the region is complete (True, False, Unknown).
        product_types (list): The product types of the region.
        metadata (dict): The metadata of the region, e.g. tool-specific metadata.
    """

    contig_id: str
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
        regions (dict): The regions grouped by contig id.
    """

    input_file: str
    mining_tool: str
    regions: Dict[str, List[Region]] = field(default_factory=dict)


@dataclass
class QuastResult:
    """
    Class for QUAST results.
    """

    input_file: str
