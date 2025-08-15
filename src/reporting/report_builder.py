"""Report builder for creating structured reports from genome mining results."""

from typing import List, Optional

import src.compare_to_ref_analyzer as compare_to_ref_analyzer
import src.input_utils as input_utils
from src.genome_mining_result import GenomeMiningResult, QuastResult
from src.reporting.metrics_calculators import (
    BasicMetricsCalculator,
    CompareToRefMetricsCalculator,
)
from src.reporting.report_config import ReportConfigManager
from src.reporting.report_data import (
    ReportData,
    RunningMode,
    create_dataframe_from_metrics,
)


class ReportBuilder:
    """Builds structured reports from genome mining results."""

    def __init__(self, config_manager: ReportConfigManager):
        self.config_manager = config_manager

    def build_report(
        self,
        results: List[GenomeMiningResult],
        running_mode: RunningMode,
        quast_results: Optional[list[QuastResult]] = None,
        reference_genome_mining_result: Optional[GenomeMiningResult] = None,
    ) -> ReportData:
        """
        Build a report from genome mining results.

        Args:
            results: List of GenomeMiningResult objects

        Returns:
            ReportData object with structured metrics
        """
        config = self.config_manager.get_config("basic_report")
        if not config:
            raise ValueError("No configuration found for running mode: basic_report")

        basic_metrics_calculator = BasicMetricsCalculator(
            results=results,
            config=config,
        )
        metrics = basic_metrics_calculator.calculate_metrics()
        if not metrics:
            raise ValueError("No metrics were calculated. Check your input data.")

        metadata = {
            "running_mode": running_mode.value,
            "results_count": len(results),
        }

        if running_mode == RunningMode.COMPARE_TO_REFERENCE:
            reference_bgcs = compare_to_ref_analyzer.compute_coverage(
                results,
                reference_genome_mining_result,  # type: ignore
                quast_results,  # type: ignore
            )

            mode_config = self.config_manager.get_config("compare_to_reference")
            if not mode_config:
                raise ValueError(
                    "No configuration found for running mode: compare_to_reference"
                )

            mode_metrics_calculator = CompareToRefMetricsCalculator(
                results=results,
                config=mode_config,
            )
            metrics.extend(mode_metrics_calculator.calculate_metrics())

            metadata.update({"reference_bgcs": reference_bgcs})

        elif running_mode == RunningMode.COMPARE_TOOLS:
            # TODO: Implement tool comparison metrics if needed.
            ...
        elif running_mode == RunningMode.COMPARE_SAMPLES:
            # TODO: Implement sample comparison metrics if needed.
            ...

        # Create DataFrame.
        df = create_dataframe_from_metrics(metrics)
        df["file_label"] = df["file_path"].apply(
            lambda x: input_utils.get_file_label_from_path(x)
        )
        df.drop(columns=["file_path"], inplace=True, errors="ignore")

        return ReportData(metrics_df=df, running_mode=running_mode, metadata=metadata)
