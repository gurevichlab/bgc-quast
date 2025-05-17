from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict


@dataclass
class BasicStats:
    """
    Class for storing basic report statistics.

    Attributes:
        total_bgcs (int): Total number of BGCs.
        complete_bgcs (int): Total number of complete BGCs.
        fragmented_bgcs (int): Total number of fragmented BGCs.
        avg_bgc_length (float): Average length of BGCs.
        product_type_counts (dict): Counts of each product type.
    """

    # TODO: decide what exactly should be included in the stats.
    total_bgcs: int = 0
    complete_bgcs: int = 0
    fragmented_bgcs: int = 0
    avg_bgc_length: float = 0.0
    product_type_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class BasicReport:
    """
    Class for storing computed data for the BGC-QUAST report.

    Attributes:
        basic_stats (Dict[Path, BasicStats]): Basic statistics of genome mining results.
    """

    basic_stats: Dict[Path, BasicStats] = field(default_factory=dict)


@dataclass
class CompareToRefReport(BasicReport):
    """
    Class for storing computed data for the COMPARE_TO_REFERENCE mode.

    Attributes:
        TODO
    """

    ...


@dataclass
class CompareToolsReport(BasicReport):
    """
    Class for storing computed data for the COMPARE_TOOLS mode.

    Attributes:
        TODO
    """

    ...


@dataclass
class CompareSamplesReport(BasicReport):
    """
    Class for storing computed data for the COMPARE_SAMPLES mode.

    Attributes:
        TODO
    """

    ...


class RunningMode(Enum):
    """
    Running mode.
    """

    COMPARE_TO_REFERENCE = 1
    COMPARE_TOOLS = 2
    COMPARE_SAMPLES = 3
    UNKNOWN = 4
