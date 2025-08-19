"""Configuration management for BGC-QUAST reports."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class MetricConfig:
    """Configuration for a single metric."""

    name: str
    display_name: str
    description: str = ""


@dataclass
class GroupingDimensionConfig:
    """Configuration for a grouping dimension."""

    include_total: bool = True
    order: List[str] = field(default_factory=list)


@dataclass
class ReportConfig:
    """Configuration for a specific report type."""

    metrics: List[MetricConfig] = field(default_factory=list)
    grouping_dimensions: Dict[str, GroupingDimensionConfig] = field(
        default_factory=dict
    )
    grouping_combinations: List[List[str]] = field(default_factory=list)


class ReportConfigManager:
    """Manages loading and accessing report configurations."""

    def __init__(self):
        self.config_path = Path.joinpath(
            Path(__file__).parent.parent.parent.resolve(),
            "configs",
            "report_config.yaml",
        )
        self._configs: Dict[str, ReportConfig] = {}
        self._load_configs()

    def _load_configs(self) -> None:
        """Load configurations from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                raw_config = yaml.safe_load(f)

            for report_type, config_data in raw_config.items():
                self._configs[report_type] = self._parse_report_config(config_data)

        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")

    def _parse_report_config(self, config_data: Dict[str, Any]) -> ReportConfig:
        """Parse raw configuration data into ReportConfig."""
        # Parse metrics
        metrics = []
        for metric_data in config_data.get("metrics", []):
            metrics.append(
                MetricConfig(
                    name=metric_data["name"],
                    display_name=metric_data["display_name"],
                    description=metric_data.get("description", ""),
                )
            )

        # Parse grouping dimensions
        grouping_dimensions = {}
        for dim_name, dim_data in config_data.get("grouping_dimensions", {}).items():
            grouping_dimensions[dim_name] = GroupingDimensionConfig(
                include_total=dim_data.get("include_total", True),
                order=dim_data.get("order", []),
            )

        grouping_combinations = config_data.get("grouping_combinations", [])

        return ReportConfig(
            metrics=metrics,
            grouping_dimensions=grouping_dimensions,
            grouping_combinations=grouping_combinations,
        )

    def get_config(self, report_type: str) -> ReportConfig:
        """Get configuration for a specific report type."""
        if report_type not in self._configs:
            raise ValueError(f"Unknown report type: {report_type}")
        return self._configs[report_type]

    def get_combined_config(self, report_types: List[str]) -> ReportConfig:
        """Get combined configuration for multiple report types."""
        combined_config = ReportConfig()
        for report_type in report_types:
            if report_type not in self._configs:
                raise ValueError(f"Unknown report type: {report_type}")
            config = self._configs[report_type]
            combined_config.metrics.extend(config.metrics)
            combined_config.grouping_dimensions.update(config.grouping_dimensions)
            combined_config.grouping_combinations.extend(config.grouping_combinations)

        # Remove duplicates in metrics and grouping combinations.
        combined_config.metrics = list(
            {m.name: m for m in combined_config.metrics}.values()
        )
        combined_config.grouping_combinations = list(
            {
                tuple(comb): comb for comb in combined_config.grouping_combinations
            }.values()
        )
        return combined_config

    def list_report_types(self) -> List[str]:
        """List available report types."""
        return list(self._configs.keys())
