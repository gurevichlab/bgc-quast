from collections import defaultdict
from statistics import mean
from typing import Any, Callable, Iterable

from src.genome_mining_result import Bgc

GROUPING_KEY_REGISTRY: dict[str, Callable[[Bgc], Any]] = {}
METRIC_REGISTRY: dict[str, Callable[[Iterable[Bgc]], Any]] = {}


def grouping_key(name: str) -> Callable[[Callable[[Bgc], Any]], Callable[[Bgc], Any]]:
    """
    Decorator to register a grouping key function.
    The function should take a Bgc object and return a value to group by.
    """

    def wrapper(func: Callable[[Bgc], Any]) -> Callable[[Bgc], Any]:
        GROUPING_KEY_REGISTRY[name] = func
        return func

    return wrapper


def metric(
    name: str,
) -> Callable[[Callable[[Iterable[Bgc]], Any]], Callable[[Iterable[Bgc]], Any]]:
    """
    Decorator to register a metric function.
    The function should take an iterable of Bgc objects and return a metric value.
    """

    def wrapper(func: Callable[[Iterable[Bgc]], Any]) -> Callable[[Iterable[Bgc]], Any]:
        METRIC_REGISTRY[name] = func
        return func

    return wrapper


# Grouping key functions:


@grouping_key("completeness")
def by_completeness(bgc: Bgc) -> str:
    return bgc.completeness


@grouping_key("product_type")
def by_product_type(bgc: Bgc) -> str:
    if len(bgc.product_types) == 1:
        return bgc.product_types[0]
    # If there are multiple product types, return "Hybrid"
    if len(bgc.product_types) > 1:
        return "Hybrid"
    return "Unknown"


# Metric functions:


@metric("total_bgc_count")
def total_count(bgcs: Iterable[Bgc]) -> int:
    return len(list(bgcs))


@metric("mean_bgc_length")
def mean_length(bgcs: Iterable[Bgc]) -> float:
    values = [b.end - b.start for b in bgcs if b.end > b.start]
    return mean(values) if values else 0


class MetricsEngine:
    """
    Class to compute metrics for a list of BGCs.
    It groups the BGCs by specified keys and computes metrics for each group.

    Attributes:
        bgcs (list[Bgc]): List of BGCs to compute metrics for.
    """

    def __init__(self, bgcs: list[Bgc]):
        self.bgcs = bgcs

    def compute(self, group_by: list[str]) -> dict[tuple, dict[str, Any]]:
        """
        Compute metrics for the BGCs, grouped by the specified keys.

        Args:
            group_by (list[str]): List of keys to group by. Each key should be a registered
            grouping key.

        Returns:
            dict[tuple, dict[str, Any]]: A dictionary where keys are tuples of grouping
            key values and values are dictionaries of metrics.
        """
        if not all(k in GROUPING_KEY_REGISTRY for k in group_by):
            raise ValueError(
                f"Invalid grouping keys: {', '.join(k for k in group_by if k not in GROUPING_KEY_REGISTRY)}"
            )
        if not all(k in METRIC_REGISTRY for k in METRIC_REGISTRY):
            raise ValueError(
                f"Invalid metric keys: {', '.join(k for k in METRIC_REGISTRY if k not in METRIC_REGISTRY)}"
            )

        key_funcs = [GROUPING_KEY_REGISTRY[k] for k in group_by]
        result = defaultdict(dict)
        grouped = defaultdict(list)

        for bgc in self.bgcs:
            key = tuple(func(bgc) for func in key_funcs)
            grouped[key].append(bgc)

        for key, group in grouped.items():
            for name, func in METRIC_REGISTRY.items():
                result[key][name] = func(group)

        return result
