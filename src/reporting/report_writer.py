"""Unified report writer for BGC-QUAST reports."""

from pathlib import Path
from typing import Optional

from src.reporting.report_config import ReportConfigManager
from src.reporting.report_data import ReportData
from src.reporting.report_formatter import ReportFormatter


def write_report(
    report_data: ReportData,
    txt_destination: Optional[Path] = None,
    html_destination: Optional[Path] = None,
    tsv_destination: Optional[Path] = None,
) -> None:
    """
    Write the report to text, HTML, and/or TSV files.

    Args:
        report_data: The ReportData object containing structured data.
        txt_destination: Path to the text report file.
        html_destination: Path to the HTML report file.
        tsv_destination: Path to the TSV report file.
        config_path: Path to the report configuration file.
    """
    # Load configuration
    config_manager = ReportConfigManager()
    config = config_manager.get_combined_config(
        ["basic_report", report_data.running_mode.value]
    )

    # Create formatter
    formatter = ReportFormatter(config)

    # Write each requested format
    if txt_destination:
        formatter.write_txt(report_data, txt_destination)
    if html_destination:
        formatter.write_html(report_data, html_destination)
    if tsv_destination:
        formatter.write_tsv(report_data, tsv_destination)


def write_all_formats(
    report_data: ReportData,
    output_dir: Path,
    base_filename: str = "bgc_quast_report",
) -> None:
    """
    Convenience function to write a report in all formats to standard locations.

    Args:
        report_data: The ReportData to write
        output_dir: Output directory
        base_filename: Base filename for output files
        config_path: Path to configuration file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    write_report(
        report_data=report_data,
        txt_destination=output_dir / f"{base_filename}.txt",
        html_destination=output_dir / f"{base_filename}.html",
        tsv_destination=output_dir / f"{base_filename}.tsv",
    )
