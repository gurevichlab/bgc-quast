import base64
import csv
import html
from pathlib import Path


def _file_to_base64(path: Path) -> str:
    """Encode an asset so it can be embedded directly into the standalone HTML."""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _format_bgc_cell(value: str) -> str:
    """Escape a TSV cell and display multiple BGC predictions on separate lines."""
    escaped = html.escape(value)

    if escaped == "N/A":
        return "-"

    # Separate BGC predictions use semicolons in the TSV; display each on its own line.
    return escaped.replace("; ", ";<br>")


def write_overlapping_bgc_html(
    tsv_path: Path,
    output_path: Path,
) -> None:
    """Create the standalone overlapping-BGC HTML report from its TSV output."""

    # The TSV contains two header rows followed by one row per genomic interval.
    with open(tsv_path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh, delimiter="\t"))

    if len(rows) < 2:
        raise ValueError("Overlapping BGC TSV must contain two header rows.")

    labels = rows[0]
    tools = rows[1]
    data_rows = rows[2:]

    header_cells = [
        "<th>Sequence ID</th>",
        "<th>Interval start</th>",
        "<th>Interval end</th>",
    ]

    # Build one visual header cell per genome-mining tool.
    # Each tool cell shows the input label above the tool name.
    for label, tool in zip(labels[3:], tools[3:]):
        header_cells.append(
            '<th class="tool-header">'
            f'<span class="file-label">{html.escape(label)}</span>'
            f'<span class="tool-name">{html.escape(tool)}</span>'
            '</th>'
        )

    # Add one filter field for each table column.
    # Sequence and product columns use text matching, while interval coordinates
    # use numeric minimum/maximum boundaries.
    filter_cells = [
        '<th><input class="column-filter" type="text" '
        'data-column="0" data-filter-type="text" '
        'placeholder="Sequence ID"></th>',

        '<th><input class="column-filter" type="number" '
        'data-column="1" data-filter-type="min" '
        'min="1" step="1" placeholder="Min"></th>',

        '<th><input class="column-filter" type="number" '
        'data-column="2" data-filter-type="max" '
        'min="1" step="1" placeholder="Max"></th>',
    ]

    for column_index in range(3, len(labels)):
        filter_cells.append(
            '<th><input class="column-filter" type="text" '
            f'data-column="{column_index}" data-filter-type="text" '
            'placeholder="Product"></th>'
        )

    body_rows = []

    # Convert TSV interval rows into HTML table rows.
    for row in data_rows:
        cells = [
            f"<td>{html.escape(row[0])}</td>",
            f"<td>{html.escape(row[1])}</td>",
            f"<td>{html.escape(row[2])}</td>",
        ]

        for value in row[3:]:
            cells.append(f'<td class="bgc-cell">{_format_bgc_cell(value)}</td>')

        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    table_html = (
        '<table class="bgc-overlap-table">'
        "<thead>"
        f'<tr class="column-header-row">{"".join(header_cells)}</tr>'
        f'<tr class="filter-row">{"".join(filter_cells)}</tr>'
        "</thead>"
        f'<tbody>{"".join(body_rows)}</tbody>'
        "</table>"
    )

    # Reuse the main report styling and embed assets to keep the HTML standalone.
    asset_dir = Path(__file__).resolve().parent.parent / "html_report"

    logo_path = asset_dir / "github-mark-white.svg"
    logo_b64 = _file_to_base64(logo_path)
    logo_data_uri = f"data:image/svg+xml;base64,{logo_b64}"

    template = (asset_dir / "bgc_overlaps_template.html").read_text(encoding="utf-8")
    report_css = (asset_dir / "report.css").read_text(encoding="utf-8")
    overlaps_css = (asset_dir / "bgc_overlaps.css").read_text(encoding="utf-8")
    overlaps_js = (asset_dir / "build_bgc_overlaps.js").read_text(encoding="utf-8")

    html_filled = (
        template
        .replace("{{ style_css }}", report_css)
        .replace("{{ overlaps_style_css }}", overlaps_css)
        .replace("{{ table_html }}", table_html)
        .replace("{{ github_logo }}", logo_data_uri)
        .replace("{{ overlaps_script_js }}", overlaps_js)
    )

    output_path.write_text(html_filled, encoding="utf-8")
