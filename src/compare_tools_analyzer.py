from typing import Dict, Iterable, List, Tuple
from collections import defaultdict

from src.genome_mining_result import GenomeMiningResult, Bgc

# ------------------------ Basic geometry helpers ------------------------- #
def overlap_len(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    """Overlap length for CLOSED intervals [a_start, a_end] and [b_start, b_end].
    Example: [10,20] ∩ [20,30] -> 1 (the base at 20).
    """
    if a_end < a_start:
        a_start, a_end = a_end, a_start
    if b_end < b_start:
        b_start, b_end = b_end, b_start

    left = max(a_start, b_start)
    right = min(a_end, b_end)
    if right < left:
        return 0
    return right - left + 1


def coverage_of_a_by_b(a: Bgc, b: Bgc) -> float:
    """Directional coverage of A by B: |A ∩ B| / |A| with CLOSED intervals."""
    a_len = max(0, a.end - a.start + 1)
    if a_len == 0:
        return 0.0
    ov = overlap_len(a.start, a.end, b.start, b.end)
    return ov / a_len


def _is_unique_against_candidates(
    bgc_a: Bgc,
    candidates: Iterable[Bgc],
    overlap_threshold: float,
) -> bool:
    """Return True if no candidate covers bgc_a by >= overlap_threshold."""
    if not (0.0 <= overlap_threshold <= 1.0):
        raise ValueError(f"The overlap threshold must be in [0,1], got {overlap_threshold}")

    for b in candidates:
        cov = coverage_of_a_by_b(bgc_a, b)
        if cov > 0.0 and cov >= overlap_threshold:
            return False
    return True


# ------------------------------- Tool comparisons ------------------------------ #
def compute_uniqueness(
    results: List[GenomeMiningResult],
    overlap_threshold: float,
) -> Tuple[List[Tuple[GenomeMiningResult, List[Bgc], List[Bgc]]], Dict[str, dict]]:
    """
    Compute unique and non-unique BGCs per result/tool, and also produce
    directional pairwise counts for visualization.

    Returns:
        (
          results_uniques,
          meta
        )

        where:

        results_uniques: List aligned with input order:
            [
              (result_i, [unique_bgcs_for_result_i], [non_unique_bgcs_for_result_i]),
              ...
            ]

        meta: {
          "totals_by_tool": {
              "<run_label>": {"unique": int, "non_unique": int, "total": int}, ...
          },
          "pairwise_by_tool": {
              "<run_labelA>": {
                  "<run_labelB>": {"unique": int, "non_unique": int},   # A against B (directional)
                  ...
              },
              ...
          },
        }
    """
    if not results:
        return [], {"totals_by_tool": {}, "pairwise_by_tool": {}}

    # Index all BGCs by sequence with owning result index and tool
    by_seq: Dict[str, List[Tuple[int, str, int, Bgc]]] = defaultdict(list)
    for i, res in enumerate(results):
        for j, bgc in enumerate(res.bgcs):
            by_seq[bgc.sequence_id].append((i, res.mining_tool, j, bgc))

    # Convenience: per-sequence, per-run lookup (for fast pairwise checks)
    by_seq_by_run: Dict[str, Dict[int, List[Bgc]]] = defaultdict(lambda: defaultdict(list))
    for seq, entries in by_seq.items():
        for (run_idx, _tool, _j, b) in entries:
            by_seq_by_run[seq][run_idx].append(b)

    # Build run labels once, using already-deduplicated input_file_label
    run_labels: List[str] = [
        f"{(res.display_label or res.input_file_label)} [{res.mining_tool}]"
        for res in results
    ]

    # Aggregates for totals, keyed by run label
    totals_by_tool: Dict[str, Dict[str, int]] = {
        run_label: {"unique": 0, "non_unique": 0, "total": 0}
        for run_label in run_labels
    }

    # Directional pairwise maps: A_run -> B_run -> counts for A against B,
    # only for cross-tool comparisons (same semantics as before).
    pairwise_by_tool: Dict[str, Dict[str, Dict[str, int]]] = {}
    for i, res in enumerate(results):
        A_label = run_labels[i]
        A_tool = res.mining_tool
        pairwise_by_tool[A_label] = {}
        for j, other in enumerate(results):
            if j == i:
                continue
            # skip exact same file (same path)
            if other.input_file == res.input_file:
                continue
            B_label = run_labels[j]
            pairwise_by_tool[A_label][B_label] = {"unique": 0, "non_unique": 0}

    results_uniques: List[Tuple[GenomeMiningResult, List[Bgc], List[Bgc]]] = []

    # Main pass: per result (run)
    for i, res in enumerate(results):
        A_tool = res.mining_tool
        A_label = run_labels[i]
        uniques_for_res: List[Bgc] = []
        non_uniques_for_res: List[Bgc] = []

        for a in res.bgcs:
            seq = a.sequence_id

            # -------- Global uniqueness (vs ANY other tool) -------- #
            # Candidates: same sequence, different tool (unchanged behaviour)
            global_candidates = [
                b for (_k, other_tool, _jj, b) in by_seq.get(seq, [])
                if other_tool != A_tool
            ]
            is_unique_global = _is_unique_against_candidates(a, global_candidates, overlap_threshold)
            if is_unique_global:
                uniques_for_res.append(a)
                totals_by_tool[A_label]["unique"] += 1
            else:
                non_uniques_for_res.append(a)
                totals_by_tool[A_label]["non_unique"] += 1

            totals_by_tool[A_label]["total"] += 1

            # -------- Directional pairwise (A run against each B run of other tools) -------- #
            for j, res_B in enumerate(results):
                if j == i:
                    continue
                # skip exact same file (same path)
                if res_B.input_file == res.input_file:
                    continue

                B_label = run_labels[j]
                if B_label not in pairwise_by_tool.get(A_label, {}):
                    continue

                overlapped_by_B = False
                for b in by_seq_by_run.get(seq, {}).get(j, []):
                    cov = coverage_of_a_by_b(a, b)
                    if cov > 0.0 and cov >= overlap_threshold:
                        overlapped_by_B = True
                        break

                if overlapped_by_B:
                    pairwise_by_tool[A_label][B_label]["non_unique"] += 1
                else:
                    pairwise_by_tool[A_label][B_label]["unique"] += 1

        results_uniques.append((res, uniques_for_res, non_uniques_for_res))

    meta = {
        "totals_by_tool": totals_by_tool,
        "pairwise_by_tool": pairwise_by_tool,
    }
    return results_uniques, meta












