# src/visualization/venn_diagram.py
from pathlib import Path
from itertools import combinations
import re

import matplotlib.pyplot as plt
from matplotlib_venn import venn2


def _normalize_tool_label(name: str) -> str:
    """Collapse common variants to a clean label for display & filenames."""
    s = name.strip()
    low = s.lower()
    if low.startswith("deepbgc"):
        return "deepBGC"
    if low.startswith("antismash"):
        return "antiSMASH"
    if low.startswith("gecco"):
        return "GECCO"
    return s


def plot_pairwise_venn_from_meta(
    meta: dict,
    toolA: str,
    toolB: str,
    threshold: float,
    save_path: Path | None = None,
    *,
    set_colors: tuple[str, str] = ("#2e808f", "#FFBC42"),
    min_intersection_for_shape: int = 6,
) -> Path | None:
    """
    left  = A→B 'unique'
    center= "A→B non_unique / B→A non_unique"
    right = B→A 'unique'
    """
    pairwise = meta.get("pairwise_by_tool", {}) or {}
    A_row = pairwise.get(toolA, {}).get(toolB, {}) or {}
    B_row = pairwise.get(toolB, {}).get(toolA, {}) or {}

    # Directional counts
    nA_unique      = int(A_row.get("unique", 0))
    nA_non_unique  = int(A_row.get("non_unique", 0))
    nB_unique      = int(B_row.get("unique", 0))
    nB_non_unique  = int(B_row.get("non_unique", 0))

    # Pretty labels (UI) and also for filenames
    labelA = _normalize_tool_label(toolA)
    labelB = _normalize_tool_label(toolB)

    # venn2 needs numeric areas just to draw shapes; we’ll override text.
    # Enforce non-zero lobes and a minimally visible overlap.
    inter_numeric = max(min(nA_non_unique, nB_non_unique), min_intersection_for_shape if (nA_non_unique or nB_non_unique) else 1)
    left_numeric  = max(nA_unique, 1)
    right_numeric = max(nB_unique, 1)

    plt.figure(figsize=(5, 5), dpi=300)
    v = venn2(
        subsets=(10, 10, inter_numeric),
        set_labels=(labelA, labelB),
        set_colors=set_colors,
        alpha=0.7,
    )

    # Override labels with the exact numbers
    if v.get_label_by_id("10"):
        v.get_label_by_id("10").set_text(str(nA_unique))
        v.get_label_by_id("10").set_fontsize(16)

    if v.get_label_by_id("01"):
        v.get_label_by_id("01").set_text(str(nB_unique))
        v.get_label_by_id("01").set_fontsize(16)

    if v.get_label_by_id("11"):
        center_text = f"{nA_non_unique} / {nB_non_unique}"
        # Auto-shrink center font when text is long (e.g., "1234 / 5678")
        fs = 15
        v.get_label_by_id("11").set_text(center_text)
        v.get_label_by_id("11").set_fontsize(fs)

    plt.title(f"Overlap between {labelA} and {labelB}\n(overlap threshold={int(round(threshold*100))}%)")

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path)
        plt.close()
        return save_path
    else:
        plt.show()
        return None


def generate_pairwise_venn_diagrams(
    meta: dict,
    output_dir: Path,
    threshold: float,
    subfolder: str = "venn_overlaps",
) -> list[Path]:
    """
    Make one PNG per unordered pair from meta['pairwise_by_tool'].

    Filenames: {ToolA}_{ToolB}_{threshold*100}.png
    Saved to:  output_dir / subfolder
    """
    pairwise = meta.get("pairwise_by_tool", {}) or {}
    tools = sorted(pairwise.keys())
    out_dir = output_dir / subfolder
    out_dir.mkdir(parents=True, exist_ok=True)

    thr_pct = int(round(threshold * 100))
    saved: list[Path] = []

    for A, B in combinations(tools, 2):
        fname = f"{_normalize_tool_label(A)}_{_normalize_tool_label(B)}_{thr_pct}.png"
        fpath = out_dir / fname
        plot_pairwise_venn_from_meta(
            meta=meta,
            toolA=A,
            toolB=B,
            threshold=threshold,
            save_path=fpath,
        )
        saved.append(fpath)

    return saved
