from dataclasses import dataclass
from enum import Enum
from typing import Any
from dataclasses import field
from pathlib import Path

import pandas as pd


class RunningMode(Enum):
    """
    Running mode.
    """

    COMPARE_TO_REFERENCE = "compare_to_reference"
    COMPARE_TOOLS = "compare_tools"
    COMPARE_SAMPLES = "compare_samples"
    UNKNOWN = "unknown"


@dataclass
class ReportData:
    """
    Class for storing computed data for the BGC-QUAST report.

    Attributes:
        metrics_df (pd.DataFrame): DataFrame containing the computed metrics.
        running_mode (RunningMode): The running mode of the report, indicating
        how the data was processed and compared.
        metadata (dict[str, Any]): Any additional information associated with the report.
        The keys are descriptive names, and the values can be any type of data.
    """

    metrics_df: pd.DataFrame
    running_mode: RunningMode
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricValue:
    """
    Container for metric values with metadata.

    Attributes:
        file_path (Path): Path to the file associated with this metric.
        metric_name (str): Name of the metric.
        value (Any): The value of the metric.
        grouping (dict[str, str]): Additional grouping information as key-value pairs.
        This can include dimensions like product type, completeness, etc.
        The keys are dimension names, and the values are the corresponding values.
    """

    file_path: Path
    metric_name: str
    value: Any
    grouping: dict[str, str] = field(default_factory=dict)

    def to_series_row(self) -> dict[str, Any]:
        """Convert to a dictionary suitable for pandas DataFrame row."""
        row = {
            "file_path": str(self.file_path),
            "metric_name": self.metric_name,
            "value": self.value,
        }
        row.update(self.grouping)
        return row


def create_dataframe_from_metrics(metric_values: list[MetricValue]) -> pd.DataFrame:
    """Create a pandas DataFrame from a list of MetricValue objects."""
    if not metric_values:
        return pd.DataFrame(columns=["file_path", "metric_name", "value"])

    rows = [mv.to_series_row() for mv in metric_values]
    return pd.DataFrame(rows)
