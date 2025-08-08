from statistics import mean
from typing import Any, Callable, Iterable

from src.genome_mining_result import Bgc


class GroupingKeyRegistry:
    """Registry for grouping key functions."""

    def __init__(self):
        self._functions: dict[str, Callable[[Any], str]] = {}

    def register(self, name: str, func: Callable[[Any], str]) -> None:
        """Register a grouping key function."""
        self._functions[name] = func

    def get(self, name: str) -> Callable[[Any], str]:
        """Get a grouping key function by name."""
        if name not in self._functions:
            raise ValueError(f"Unknown grouping key: {name}")
        return self._functions[name]

    def list_keys(self) -> list[str]:
        """list available grouping keys."""
        return list(self._functions.keys())


class MetricRegistry:
    """Registry for metric calculation functions."""

    def __init__(self):
        self._functions: dict[str, Callable[[Iterable[Any]], Any]] = {}

    def register(self, name: str, func: Callable[[Iterable[Any]], Any]) -> None:
        """Register a metric calculation function."""
        self._functions[name] = func

    def get(self, name: str) -> Callable[[Iterable[Any]], Any]:
        """Get a metric function by name."""
        if name not in self._functions:
            raise ValueError(f"Unknown metric: {name}")
        return self._functions[name]

    def list_metrics(self) -> list[str]:
        """list available metrics."""
        return list(self._functions.keys())


# Global registries
GROUPING_REGISTRY = GroupingKeyRegistry()
METRIC_REGISTRY = MetricRegistry()


def grouping_key(name: str):
    """Decorator to register a grouping key function."""

    def decorator(func: Callable[[Any], str]) -> Callable[[Any], str]:
        GROUPING_REGISTRY.register(name, func)
        return func

    return decorator


def metric(name: str):
    """Decorator to register a metric function."""

    def decorator(
        func: Callable[[Iterable[Any]], Any],
    ) -> Callable[[Iterable[Any]], Any]:
        METRIC_REGISTRY.register(name, func)
        return func

    return decorator


# Grouping key functions
@grouping_key("completeness")
def by_completeness(bgc: Bgc) -> str:
    """Group by BGC completeness."""
    return bgc.completeness


@grouping_key("product_type")
def by_product_type(bgc: Bgc) -> str:
    """Group by BGC product type."""
    if len(bgc.product_types) == 1:
        return bgc.product_types[0]
    elif len(bgc.product_types) > 1:
        return "Hybrid"
    else:
        return "Unknown"


# Basic metric functions
@metric("total_bgc_count")
def total_bgc_count(bgcs: Iterable[Bgc]) -> int:
    """Count total number of BGCs."""
    return len(list(bgcs))


@metric("mean_bgc_length")
def mean_bgc_length(bgcs: Iterable[Bgc]) -> float:
    """Calculate mean BGC length."""
    bgc_list = list(bgcs)
    if not bgc_list:
        return 0.0

    lengths = [bgc.end - bgc.start for bgc in bgc_list if bgc.end > bgc.start]
    return mean(lengths) if lengths else 0.0
