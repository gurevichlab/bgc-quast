from bgc_quast.output.bgc_overlaps_html_writer import write_overlapping_bgc_html


def test_write_overlapping_bgc_html(tmp_path):
    """Test that the overlapping-BGC HTML report is generated with expected content."""
    tsv_path = tmp_path / "all_tools.bgcs.overlaps.tsv"
    html_path = tmp_path / "all_tools.bgcs.overlaps.html"

    tsv_path.write_text(
        "sequence_id\tinterval_start\tinterval_end\tassembly_1\tassembly_1\n"
        "\t\t\tantiSMASH\tDeepBGC\n"
        "CONTIG_1\t100\t500\t100 - 300 (NRPS)\tN/A\n"
        "CONTIG_2\t1000\t5000\t"
        "1000 - 2000 (PKS); 3000 - 5000 (RiPP)\t1000 - 5000 (PKS)\n",
        encoding="utf-8",
    )

    write_overlapping_bgc_html(
        tsv_path=tsv_path,
        output_path=html_path,
    )

    assert html_path.exists()

    html = html_path.read_text(encoding="utf-8")

    # TSV content is represented in the generated table.
    assert "assembly_1" in html
    assert "antiSMASH" in html
    assert "DeepBGC" in html
    assert "CONTIG_1" in html
    assert "100 - 300 (NRPS)" in html

    # Multiple predictions from one tool are displayed on separate lines.
    assert "1000 - 2000 (PKS);<br>3000 - 5000 (RiPP)" in html

    # The generated report contains its navigation and interactive table code.
    assert "Back to main report" in html
    assert "column-filter" in html
    assert "rows-per-page" in html
    assert "const columnFilters" in html