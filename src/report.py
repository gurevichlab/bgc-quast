from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any
from src.genome_mining_result import Bgc


@dataclass
class BasicReport:
    """
    Class for storing computed data for the BGC-QUAST report.

    Attributes:
        basic_metrics (Dict[Path, dict[str, dict[tuple, dict[str, Any]]]]):
        Basic statistics of genome mining results.
    """

    basic_metrics: Dict[Path, dict[str, dict[tuple, dict[str, Any]]]] = field(
        default_factory=dict
    )


# Reference BGC status enum.
class Status(Enum):
    MISSED = 0
    FRAGMENTED = 1
    COVERED = 2
    COVERED_BY_FRAGMENTS = 3


@dataclass
class Intersection:
    """
    Class for intersection between assembly and reference BGCs.

    Attributes:
        assembly_bgc (Bgc): The assembly BGC.
        start_in_ref (int): Start position in the reference sequence.
        end_in_ref (int): End position in the reference sequence.
        reversed (bool): Indicates if the assembly BGC coordinates are reversed.
    """

    assembly_bgc: Bgc
    start_in_ref: int
    end_in_ref: int
    reversed: bool = False


@dataclass
class ReferenceBgc(Bgc):
    """
    Class for reference BGCs. Inherits from Bgc and adds analysis attributes.

    Attributes:
        status (Status): The status of the BGC.
        intersecting_assembly_bgcs (list[Intersection]): assembly BGCs that intersect
        with this BGC.
    """

    status: Status = Status.MISSED
    intersecting_assembly_bgcs: list[Intersection] = field(default_factory=list)

    @classmethod
    def from_bgc(cls, bgc: Bgc) -> "ReferenceBgc":
        """
        Create a ReferenceBgc instance from a Bgc instance.

        Args:
            bgc (Bgc): The BGC to convert.

        Returns:
            ReferenceBgc: The converted reference BGC.
        """
        return cls(
            bgc_id=bgc.bgc_id,
            sequence_id=bgc.sequence_id,
            start=bgc.start,
            end=bgc.end,
            completeness=bgc.completeness,
            product_types=bgc.product_types,
            metadata=bgc.metadata,
        )


@dataclass
class CompareToRefReport(BasicReport):
    """
    Class for storing computed data for the COMPARE_TO_REFERENCE mode.

    Attributes:
        ref_bgc_coverage (Dict[Path, list[ReferenceBgc]]):
        Coverage information for reference BGCs by genome mining result.
    """

    ref_bgc_coverage: Dict[Path, list[ReferenceBgc]] = field(default_factory=dict)

    @classmethod
    def from_basic(cls, basic: BasicReport) -> "CompareToRefReport":
        return cls(
            basic_metrics=basic.basic_metrics,
        )


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
