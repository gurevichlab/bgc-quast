from dataclasses import dataclass, field
from enum import Enum

from src.genome_mining_result import Bgc


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


# Reference BGC status enum.
class Status(Enum):
    MISSED = 0
    PARTIALLY_COVERED = 1
    COVERED = 2
    COVERED_BY_FRAGMENTS = 3


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
