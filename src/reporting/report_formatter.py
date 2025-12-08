"""Unified report formatters for different output formats."""

from pathlib import Path

import pandas as pd
import json
import math
import base64
from src.reporting.report_config import ReportConfig
from src.reporting.report_data import ReportData


class DataFrameTableBuilder:
    """Builds pivot tables from ReportData for formatting."""

    def __init__(self, config: ReportConfig):
        self.config = config

    def build_pivot_table(self, data: ReportData) -> pd.DataFrame:
        """
        Build a pivot table from ReportData using metrics as rows, files as columns, and grouping dimensions.
        """

        df = data.metrics_df.copy()

        # Create hierarchical row labels and sort keys
        df["row_label"], df["sort_key"] = zip(
            *[self._create_row_label_and_sort_key(row) for _, row in df.iterrows()]
        )

        # Sort the dataframe by the sort keys
        df = df.sort_values("sort_key").drop("sort_key", axis=1)

        # Always use file_label as columns
        pivot_table = df.pivot_table(
            index="row_label",
            columns=["file_label", "mining_tool"]
            if "file_label" in df.columns
            else None,
            values="value",
            aggfunc="first",
            sort=False,
        )

        pivot_table.index.name = None
        pivot_table = pivot_table.fillna(0)

        return pivot_table

    def _create_row_label_and_sort_key(self, row: pd.Series) -> tuple[str, tuple]:
        """Create hierarchical row labels and sort keys from metric names and grouping columns,
        respecting config order."""
        exclude = {
            "metric_name",
            "value",
            "file_label",
            "row_label",
            "sort_key",
            "mining_tool",
        }

        # Use grouping_combinations from config if present, else all grouping columns
        grouping_combinations = self.config.grouping_combinations
        if grouping_combinations:
            # Use the first combination for ordering/grouping
            grouping_dims = grouping_combinations[0]
        else:
            grouping_dims = [col for col in row.index if col not in exclude]

        metric_display = self._get_metric_display_name(row["metric_name"])

        # Start with metric order
        metric_order = self._get_metric_order(row["metric_name"])

        # Determine grouping category and build sort key
        grouping_parts = []
        non_total_values = []

        for group_dim in grouping_dims:
            if group_dim in row and pd.notna(row[group_dim]):
                value = str(row[group_dim])
                grouping_parts.append(value)
                non_total_values.append((group_dim, value))

        # Determine the grouping category for sorting
        if not non_total_values:
            # This is a total row
            grouping_category = 0
            sort_key_parts = [metric_order, grouping_category]
        elif len(non_total_values) == 1:
            # Single dimension grouping
            dim_name, dim_value = non_total_values[0]
            grouping_category = 1
            dim_order = self._get_dimension_value_order(dim_name, dim_value)
            # For single dimensions, we want them ordered by their position in grouping_dims
            dim_position = (
                grouping_dims.index(dim_name) if dim_name in grouping_dims else 999
            )
            sort_key_parts = [metric_order, grouping_category, dim_position, dim_order]
        else:
            # Multi-dimension grouping
            grouping_category = 2
            # Sort by the values in the order of grouping_dims
            dim_sort_parts = []
            for group_dim in grouping_dims:
                found_value = None
                for dim_name, dim_value in non_total_values:
                    if dim_name == group_dim:
                        found_value = dim_value
                        break

                if found_value:
                    dim_order = self._get_dimension_value_order(group_dim, found_value)
                    dim_sort_parts.append(dim_order)
                else:
                    dim_sort_parts.append(float("inf"))

            sort_key_parts = [metric_order, grouping_category] + dim_sort_parts

        # Create the label
        if grouping_parts:
            label = f"{metric_display} ({', '.join(grouping_parts)})"
        else:
            label = f"{metric_display} (Total)"

        return label, tuple(sort_key_parts)

    def _get_metric_order(self, metric_name: str) -> int:
        """Get the order index for a metric based on config."""
        for i, metric_config in enumerate(self.config.metrics):
            if metric_config.name == metric_name:
                return i
        return len(self.config.metrics)  # Unknown metrics go last

    def _get_dimension_value_order(self, dimension_name: str, value: str) -> int:
        """Get the order index for a dimension value based on config."""
        if dimension_name in self.config.grouping_dimensions:
            dimension_config = self.config.grouping_dimensions[dimension_name]
            if value in dimension_config.order:
                return dimension_config.order.index(value)
            else:
                # Unknown values go after known ones
                return len(dimension_config.order)
        return 0  # Default order if dimension not configured

    def _get_metric_display_name(self, metric_name: str) -> str:
        """Get display name for a metric."""
        for metric_config in self.config.metrics:
            if metric_config.name == metric_name:
                return metric_config.display_name
        return metric_name  # Fallback to original name


class ReportFormatter:
    """Unified report formatter that can output to multiple formats."""

    def __init__(self, config: ReportConfig):
        self.config = config
        self.table_builder = DataFrameTableBuilder(config)

    def write_txt(self, data: ReportData, output_path: Path) -> None:
        """Format and save report as plain text table."""

        pivot_table = self.table_builder.build_pivot_table(data)

        # In compare-to-reference mode, make sure the reference column
        # (identified by its file label in metadata) is always the first column.
        ref_label = None
        if isinstance(getattr(data, "metadata", None), dict):
            ref_label = data.metadata.get("reference_file_label")
        if ref_label:
            cols = list(pivot_table.columns)

            def _is_ref(col):
                # MultiIndex columns come as tuples (file_label, mining_tool)
                file_label = col[0] if isinstance(col, tuple) else col
                return file_label == ref_label

            ref_cols = [c for c in cols if _is_ref(c)]
            other_cols = [c for c in cols if not _is_ref(c)]
            if ref_cols:
                pivot_table = pivot_table.reindex(columns=ref_cols + other_cols)

        txt = pivot_table.to_string()
        output_path.write_text(txt, encoding="utf-8")

    def write_html(self, data: ReportData, output_path: Path) -> None:
        """Format and save report as HTML with basic styling."""
        def file_to_base64(path):
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            return encoded

        # Save the running mode information
        mode = data.running_mode.value

        pivot_table = self.table_builder.build_pivot_table(data)

        # In compare-to-reference mode, make sure the reference column
        # (identified by its file label in metadata) is always the first column.
        ref_label = None
        if isinstance(getattr(data, "metadata", None), dict):
            ref_label = data.metadata.get("reference_file_label")
        if ref_label:
            cols = list(pivot_table.columns)

            def _is_ref(col):
                file_label = col[0] if isinstance(col, tuple) else col
                return file_label == ref_label

            ref_cols = [c for c in cols if _is_ref(c)]
            other_cols = [c for c in cols if not _is_ref(c)]
            if ref_cols:
                pivot_table = pivot_table.reindex(columns=ref_cols + other_cols)

        file_labels = ["file_label"]
        mining_tools = ["mining_tool"]
        for file_label, mining_tool in pivot_table.columns:
            file_labels.append(str(file_label))
            mining_tools.append(str(mining_tool))

        # Build rows array (convert blanks/NaN to "0" for numeric cells)
        rows = [file_labels, mining_tools]
        for idx, row in pivot_table.iterrows():
            out = [str(idx)]
            for v in row.tolist():
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    out.append("0")
                else:
                    out.append(str(v))
            rows.append(out)

        # Collect metadata for compare_tools mode ---
        if data.running_mode.value == "compare_tools":
            metadata_to_dump = data.metadata
        else:
            # For now we don't expose metadata in other modes
            metadata_to_dump = {}
        metadata_json = json.dumps(metadata_to_dump, ensure_ascii=False)
        # Load the assets and inject JSON
        asset_dir = Path(__file__).resolve().parent.parent / "html_report"
        logo_path = asset_dir / "github-mark-white.svg"
        logo_b64 = file_to_base64(logo_path)
        logo_mime = "image/svg+xml"
        logo_data_uri = f"data:{logo_mime};base64,{logo_b64}"

        template = (asset_dir / "report_template.html").read_text(encoding="utf-8")
        style_css = (asset_dir / "report.css").read_text(encoding="utf-8")
        script_js = (asset_dir / "build_report.js").read_text(encoding="utf-8")

        data_json = json.dumps(rows, ensure_ascii=False)
        html_filled = (
            template
            .replace("{{ style_css }}", style_css)
            .replace("{{ script_js }}", script_js)
            .replace("{{ report_json }}", data_json)
            .replace("{{ report_mode }}", mode)
            .replace("{{ metadata_json }}", metadata_json)
            .replace("{{ github_logo }}", logo_data_uri)
        )

        # Write final HTML
        output_path.write_text(html_filled, encoding="utf-8")

    def write_tsv(self, data: ReportData, output_path: Path) -> None:
        """Format and save report as TSV."""
        pivot_table = self.table_builder.build_pivot_table(data)

        # In compare-to-reference mode, make sure the reference column
        # (identified by its file label in metadata) is always the first column.
        ref_label = None
        if isinstance(getattr(data, "metadata", None), dict):
            ref_label = data.metadata.get("reference_file_label")
        if ref_label:
            cols = list(pivot_table.columns)

            def _is_ref(col):
                file_label = col[0] if isinstance(col, tuple) else col
                return file_label == ref_label

            ref_cols = [c for c in cols if _is_ref(c)]
            other_cols = [c for c in cols if not _is_ref(c)]
            if ref_cols:
                pivot_table = pivot_table.reindex(columns=ref_cols + other_cols)

        pivot_table.to_csv(output_path, sep="\t")
