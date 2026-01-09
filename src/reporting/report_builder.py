"""Report builder for creating structured reports from genome mining results."""

from typing import List, Optional
from collections import defaultdict

import src.compare_to_ref_analyzer as compare_to_ref_analyzer
from src.compare_tools_analyzer import compute_uniqueness
import src.input_utils as input_utils
from src.config import Config
from src.genome_mining_result import GenomeMiningResult, QuastResult
from src.reporting.metrics_calculators import (
    BasicMetricsCalculator,
    CompareToRefMetricsCalculator,
    CompareToolsMetricsCalculator
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
        self.report_config_manager = config_manager

    def build_report(
        self,
        config: Config,
        results: List[GenomeMiningResult],
        running_mode: RunningMode,
        quast_results: Optional[list[QuastResult]] = None,
        reference_genome_mining_result: Optional[GenomeMiningResult] = None,
        label_renaming_log: Optional[list[dict]] = None,
    ) -> ReportData:
        """
        Build a report from genome mining results.

        Args:
            config: Config of the run.
            results: List of GenomeMiningResult objects
            running_mode: Running mode of the report
            (e.g., COMPARE_TO_REFERENCE, COMPARE_TOOLS, COMPARE_SAMPLES).
            quast_results: Optional list of QuastResult objects for QUAST analysis.
            reference_genome_mining_result: Optional GenomeMiningResult for reference
            genome comparison.

        Returns:
            ReportData object with structured metrics
        """
        report_config = self.report_config_manager.get_config("basic_report")
        if not report_config:
            raise ValueError("No configuration found for running mode: basic_report")


        basic_metrics_calculator = BasicMetricsCalculator(
            results=results,
            config=report_config,
        )
        metrics = basic_metrics_calculator.calculate_metrics()
        if not metrics:
            raise ValueError("No metrics were calculated. Check your input data.")

        metadata = {
            "running_mode": running_mode.value,
            "results_count": len(results),
            "min_bgc_length": config.min_bgc_length,
        }

        if running_mode == RunningMode.COMPARE_TO_REFERENCE:
            mode_config = self.report_config_manager.get_config("compare_to_reference")
            if not mode_config:
                raise ValueError(
                    "No configuration found for running mode: compare_to_reference"
                )

            reference_bgcs = compare_to_ref_analyzer.compute_coverage(
                results,
                reference_genome_mining_result,  # type: ignore
                quast_results,  # type: ignore
                config.allowed_gap_for_fragmented_recovery
            )

            mode_metrics_calculator = CompareToRefMetricsCalculator(
                results_with_ref_bgcs=reference_bgcs,
                config=mode_config,
            )
            metrics.extend(mode_metrics_calculator.calculate_metrics())

            # Add reference as a third column for basic metrics only
            if reference_genome_mining_result is not None:
                ref_basic_calc = BasicMetricsCalculator(
                    results=[reference_genome_mining_result],
                    config=report_config,
                )
                metrics.extend(ref_basic_calc.calculate_metrics())

            metadata.update({"reference_bgcs": reference_bgcs})

            if reference_genome_mining_result is not None:
                metadata.update(
                    {
                        "reference_input_file": str(reference_genome_mining_result.input_file),
                        "reference_file_label": (reference_genome_mining_result.display_label
                                                 or reference_genome_mining_result.input_file_label),
                    }
                )

        elif running_mode == RunningMode.COMPARE_TOOLS:
            mode_config = self.report_config_manager.get_config("compare_tools")
            if not mode_config:
                raise ValueError("No configuration found for running mode: compare_tools")

            results_with_unique_nonunique, meta = compute_uniqueness(results,
                                                                     overlap_threshold=config.compare_tools_overlap_threshold)

            mode_metrics_calculator = CompareToolsMetricsCalculator(
                results_with_unique_nonunique_bgcs=results_with_unique_nonunique,
                config=mode_config,
            )
            metrics.extend(mode_metrics_calculator.calculate_metrics())

            # keep in metadata so users/finders can locate them
            metadata.update({
                "compare_tools_overlap_threshold": config.compare_tools_overlap_threshold,
                "totals_by_run": meta.get("totals_by_run", {}),
                "pairwise_by_run": meta.get("pairwise_by_run", {}),
            })

        elif running_mode == RunningMode.COMPARE_SAMPLES:
            # TODO: Implement sample comparison metrics if needed.
            ...

        # Create DataFrame.
        df = create_dataframe_from_metrics(metrics)
        # Create a mapping from file_path to mining_tool
        path_to_tool = {str(r.input_file): r.mining_tool for r in results}
        path_to_label = {str(r.input_file): (r.display_label or r.input_file_label) for r in results}

        # Add a mapping for reference as well
        if reference_genome_mining_result is not None:
            path_to_tool[str(reference_genome_mining_result.input_file)] = (
                reference_genome_mining_result.mining_tool
            )
            path_to_label[str(reference_genome_mining_result.input_file)] = (
                    reference_genome_mining_result.display_label or reference_genome_mining_result.input_file_label
            )

        file_paths_str = df["file_path"].astype(str)

        df["mining_tool"] = df["file_path"].astype(str).map(path_to_tool)
        df["file_label"] = file_paths_str.map(path_to_label)
        df["input_file"] = file_paths_str

        df.drop(columns=["file_path"], inplace=True, errors="ignore")

        metadata["label_renaming_log"] = label_renaming_log or []

        return ReportData(metrics_df=df, running_mode=running_mode, metadata=metadata)
