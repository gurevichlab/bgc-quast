from collections import defaultdict
from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt

from src.report import BasicReport


def write_report(
    report: BasicReport,
    txt_destination: Path,
    html_destination: Path,
) -> None:
    """
    Write the report to both text and HTML files.

    Args:
        report (BasicReport): The report object containing metrics.
        txt_destination (Path): Path to the text report file.
        html_destination (Path): Path to the HTML report file.
    """

    # Write the text report
    _write_text_report(report, txt_destination)

    # Write the HTML report
    _write_html_report(report, html_destination)


def _write_text_report(report: BasicReport, destination: Path) -> None:
    """
    Write the report to a text file in a readable format.

    Args:
        report (BasicReport): The report object containing metrics.
        destination (Path): Path to the text report file.
    """
    with destination.open("w") as f:
        f.write("BGC-QUAST Report\n")
        f.write("=" * 40 + "\n\n")

        for file_path, metrics_by_group in report.basic_metrics.items():
            f.write(f"File: {file_path}\n")
            for group_name, grouped_metrics in metrics_by_group.items():
                f.write(f"  Group name: {group_name}\n")
                for group, metrics in grouped_metrics.items():
                    group_str = (
                        ", ".join(group) if isinstance(group, tuple) else str(group)
                    )
                    f.write(f"  Group: {group_str}\n")
                    for metric_name, value in metrics.items():
                        f.write(f"    {metric_name}: {value}\n")
                f.write("\n")
            f.write("\n")


def _write_html_report(report: BasicReport, destination: Path) -> None:
    """
    Write the report to an HTML file with diagrams.

    Args:
        report (BasicReport): The report object containing metrics.
        destination (Path): Path to the HTML report file.
    """
    html_content = ["<html>", "<head><title>BGC-QUAST Report</title></head>", "<body>"]
    html_content.append("<h1>BGC-QUAST Report</h1>")

    for file_path, metrics_by_group in report.basic_metrics.items():
        html_content.append(f"<h2>File: {file_path}</h2>")
        for group_name, grouped_metrics in metrics_by_group.items():
            diagram_dict = defaultdict(list)
            html_content.append(f"<h2>Group name: {group_name}</h2>")
            for group, metrics in grouped_metrics.items():
                group_str = ", ".join(group) if isinstance(group, tuple) else str(group)
                group_str = "overall" if group_str == "" else group_str
                html_content.append(f"<h3>Group: {group_str}</h3>")
                html_content.append("<ul>")
                for metric_name, value in metrics.items():
                    html_content.append(f"<li>{metric_name}: {value}</li>")
                    diagram_dict[metric_name].append((group_str, value))
                html_content.append("</ul>")

            # Generate and embed a diagram for the group
            for metric_name, values in diagram_dict.items():
                if len(values) < 2:
                    continue
                diagram_path = _generate_diagram(
                    file_path, group_name, metric_name, values, destination.parent
                )
                if diagram_path:
                    html_content.append(
                        f'<img src="{diagram_path}" alt="Diagram for {metric_name}">'
                    )

    html_content.append("</body></html>")

    with destination.open("w") as f:
        f.write("\n".join(html_content))


def _generate_diagram(
    file_path: Path,
    group_name: str,
    metric_name: str,
    values: list[tuple[str, float]],
    output_dir: Path,
) -> Union[str, None]:
    """
    Generate a diagram for the given metrics and save it as an image.

    Args:
        file_path (Path): The file path associated with the metrics.
        group_name (str): The group name.
        metric_name (str): The metric name.
        values (list): The metrics to visualize.
        output_dir (Path): The directory to save the diagram.

    Returns:
        str: The relative path to the saved diagram, or None if no diagram was generated.
    """
    try:
        # Use metric names as labels and their values as data
        values = sorted(values, key=lambda x: x[1], reverse=True)
        labels = [value[0] for value in values]
        values_data = [value[1] for value in values]

        plt.figure(figsize=(8, 6))
        plt.bar(labels, values_data, color="skyblue")
        plt.title(f"Metrics for {metric_name} {group_name}")
        # plt.xlabel("Metric")
        plt.ylabel(metric_name)
        plt.xticks(rotation=45, ha="right")

        diagram_filename = f"{file_path.stem}_{metric_name.replace(', ', '_')}_{group_name}_diagram.png"
        diagram_path = output_dir / diagram_filename
        plt.tight_layout()
        plt.savefig(diagram_path)
        plt.close()

        return diagram_filename
    except Exception as e:
        print(f"Failed to generate diagram for {metric_name}: {e}")
        return None
