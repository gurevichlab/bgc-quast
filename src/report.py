from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any


@dataclass
class BasicReport:
    """
    Class for storing computed data for the BGC-QUAST report.

    Attributes:
        basic_metrics (Dict[Path, dict[str, dict[tuple, dict[str, Any]]]]): Basic statistics of genome mining results.
    """

    basic_metrics: Dict[Path, dict[str, dict[tuple, dict[str, Any]]]] = field(default_factory=dict)


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
