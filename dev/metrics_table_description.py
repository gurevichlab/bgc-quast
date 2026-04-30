"""
Utility script for generating/updating metric table descriptions.

Run as:
    python -m dev.metrics_table_description
"""

from pathlib import Path
from src.reporting.report_config import ReportConfigManager

config_manager = ReportConfigManager()

report_modes = [
    ("all", config_manager.get_config("basic_report")),
    ("compare-to-reference", config_manager.get_config("compare_to_reference")),
    ("compare-tools", config_manager.get_config("compare_tools")),
]

metrics_table = ['### Metrics description']

metrics_table.append(
    "Metric | Description | Analysis mode\n"
    "-------|-------------|----------------"
)

for mode_name, report in report_modes:
    for metric in report.metrics:
        metrics_table.append(
            f'`{metric.display_name}` | {metric.description} | `{mode_name}`'
        )

metrics_md = "\n".join(metrics_table)

repo_root = Path(__file__).resolve().parents[1]
output_path = repo_root / "METRICS.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(metrics_md)