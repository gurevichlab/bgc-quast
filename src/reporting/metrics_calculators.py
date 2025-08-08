from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Callable, List

from src.genome_mining_result import Bgc, GenomeMiningResult
from src.reporting.metrics import GROUPING_REGISTRY, METRIC_REGISTRY
from src.reporting.report_config import ReportConfig
from src.reporting.report_data import MetricValue


class MetricsCalculator(ABC):
    """
    Abstract base class for metric calculators.
    """

    @abstractmethod
    def calculate_metrics(self) -> list[MetricValue]:
        """Calculate metrics for the given data."""
        pass


class BasicMetricsCalculator(MetricsCalculator):
    """Metrics calculator."""

    def __init__(self, results: list[GenomeMiningResult], config: ReportConfig):
        self.results = results
        self.config = config
        self.metric_names = [m.name for m in config.metrics]

    def calculate_metrics(self) -> list[MetricValue]:
        """
        Calculate metrics for all genome mining results.

        Args:
            metric_names: List of metric names to calculate
            grouping_dimensions: List of grouping dimension names

        Returns:
            List of all calculated MetricValue objects
        """
        metric_names = [m.name for m in self.config.metrics]
        all_metrics = []

        # Generate all combinations of grouping dimensions
        grouping_combinations = self._generate_grouping_combinations(self.config)

        for grouping_dims in grouping_combinations:
            # Calculate metrics for this grouping combination
            for result in self.results:
                try:
                    metrics = self._calculate_all_metrics_for_bgcs(
                        result.bgcs, result.input_file, metric_names, grouping_dims
                    )
                    all_metrics.extend(metrics)
                    
                except Exception as e:
                    print(
                        f"Warning: Error calculating metrics for {result.input_file}: {e}"
                    )
                    # Continue with other results

        return all_metrics

    def _calculate_all_metrics_for_bgcs(
        self,
        bgcs: List[Bgc],
        input_file: Path,
        metric_names: List[str],
        grouping_dimensions: List[str],
    ) -> List[MetricValue]:
        """
        Calculate all requested metrics with specified groupings.

        Args:
            bgcs: List of BGCs to calculate metrics for
            input_file: Path to the input file containing corresponding Genome Result
            metric_names: List of metric names to calculate
            grouping_dimensions: List of grouping dimension names

        Returns:
            List of MetricValue objects containing all calculated metrics.
        """
        results = []

        # Get grouping functions
        grouping_funcs = {
            dim: GROUPING_REGISTRY.get(dim) for dim in grouping_dimensions
        }

        # Group BGCs by all combinations of grouping dimensions.
        grouped_bgcs = self._group_bgcs(bgcs, grouping_funcs)

        # Calculate metrics for each group.
        for grouping_values, bgc_group in grouped_bgcs.items():
            for metric_name in metric_names:
                metric_func = METRIC_REGISTRY.get(metric_name)
                value = metric_func(bgc_group)

                # Create grouping dict from dimension names and values.
                # Example: {"product_type": "NRP", "completeness": "complete"}.
                # Empty dict for total grouping (no dimensions).
                grouping_dict = dict(zip(grouping_dimensions, grouping_values))

                results.append(
                    MetricValue(
                        file_path=input_file,
                        metric_name=metric_name,
                        value=value,
                        grouping=grouping_dict,
                    )
                )

        return results

    def _generate_grouping_combinations(self, config: ReportConfig) -> list[list[str]]:
        """
        Generate all combinations of grouping dimensions.

        For basic reports, this typically includes:
        - [] (no grouping - overall totals)
        - ["product_type"] (by product type)
        - ["completeness"] (by completeness)
        - ["product_type", "completeness"] (by both)
        """
        dimensions = list(config.grouping_dimensions.keys())

        combinations = []

        # Start with no grouping (overall totals)
        combinations.append([])

        # Add single dimension groupings
        for dim in dimensions:
            combinations.append([dim])

        if config.grouping_combinations:
            # Add specified multi-dimension combinations from config
            for combo in config.grouping_combinations:
                if all(dim in dimensions for dim in combo):
                    combinations.append(combo)

        return combinations

    def _group_bgcs(
        self, bgcs: list[Bgc], grouping_funcs: dict[str, Callable[[Bgc], str]]
    ) -> dict[tuple, list[Bgc]]:
        """
        Group BGCs by the specified grouping functions.

        Args:
            grouping_funcs: Dictionary of grouping functions to apply.

        Returns:
            Dictionary where keys are tuples of grouping values and values are lists of BGCs.
        """

        if not grouping_funcs:
            # No grouping - return all BGCs with empty tuple key
            return {(): bgcs}

        grouped = defaultdict(list)

        for bgc in bgcs:
            # Create grouping key tuple
            try:
                key = tuple(func(bgc) for func in grouping_funcs.values())
                grouped[key].append(bgc)
            except Exception as e:
                # Handle errors in grouping functions gracefully
                print(f"Warning: Error grouping BGC {bgc}: {e}")
                # Add to "unknown" category
                key = tuple("unknown" for _ in grouping_funcs.values())
                grouped[key].append(bgc)

        return dict(grouped)


class CompareToRefMetricsCalculator(MetricsCalculator):
    """Metrics calculator for comparing to a reference genome."""

    def __init__(self, results: list[GenomeMiningResult], config: ReportConfig):
        self.results = results
        self.config = config

    def calculate_metrics(self) -> list[MetricValue]:
        """
        Calculate metrics for comparing to a reference genome.

        Returns:
            List of all calculated MetricValue objects
        """
        # This method would implement the specific logic for comparing to a reference genome.
        # For now, it returns an empty list as a placeholder.
        return []