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
        if coverage_of_a_by_b(bgc_a, b) >= overlap_threshold:
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
              "<tool>": {"unique": int, "non_unique": int, "total": int}, ...
          },
          "pairwise_by_tool": {
              "<tool_A>": {
                  "<tool_B>": {"unique": int, "non_unique": int},   # A against B (directional)
                  ...
              },
              ...
          },
        }
    """
    # Index all BGCs by sequence with owning result index and tool
    by_seq: Dict[str, List[Tuple[int, str, int, Bgc]]] = defaultdict(list)
    tools: List[str] = []
    for i, res in enumerate(results):
        tools.append(res.mining_tool)
        for j, bgc in enumerate(res.bgcs):
            by_seq[bgc.sequence_id].append((i, res.mining_tool, j, bgc))
    tool_names = sorted(set(tools))

    # Convenience: per-sequence, per-tool lookup (for fast pairwise checks)
    by_seq_by_tool: Dict[str, Dict[str, List[Bgc]]] = defaultdict(lambda: defaultdict(list))
    for seq, entries in by_seq.items():
        for (_i, t, _j, b) in entries:
            by_seq_by_tool[seq][t].append(b)

    results_uniques: List[Tuple[GenomeMiningResult, List[Bgc], List[Bgc]]] = []

    # Aggregates for totals
    totals_by_tool: Dict[str, Dict[str, int]] = {t: {"unique": 0, "non_unique": 0, "total": 0} for t in tool_names}

    # Directional pairwise maps: A -> B -> counts for A against B
    pairwise_by_tool: Dict[str, Dict[str, Dict[str, int]]] = {
        A: {B: {"unique": 0, "non_unique": 0} for B in tool_names if B != A}
        for A in tool_names
    }

    # Main pass: per result
    for i, res in enumerate(results):
        A_tool = res.mining_tool
        uniques_for_res: List[Bgc] = []
        non_uniques_for_res: List[Bgc] = []

        for j, a in enumerate(res.bgcs):
            seq = a.sequence_id

            # -------- Global uniqueness (vs ANY other tool) -------- #
            # Candidates: same sequence, different tool
            global_candidates = [b for (_k, other_tool, _jj, b) in by_seq.get(seq, [])
                                 if other_tool != A_tool]
            is_unique_global = _is_unique_against_candidates(a, global_candidates, overlap_threshold)
            if is_unique_global:
                uniques_for_res.append(a)
                totals_by_tool[A_tool]["unique"] += 1
            else:
                non_uniques_for_res.append(a)
                totals_by_tool[A_tool]["non_unique"] += 1

            totals_by_tool[A_tool]["total"] += 1

            # -------- Directional pairwise (A against each B != A) -------- #
            # For each other tool B, count this A BGC once as overlapped or not by B.
            for B_tool in tool_names:
                if B_tool == A_tool:
                    continue
                overlapped_by_B = False
                for b in by_seq_by_tool.get(seq, {}).get(B_tool, []):
                    if coverage_of_a_by_b(a, b) >= overlap_threshold:
                        overlapped_by_B = True
                        break
                if overlapped_by_B:
                    pairwise_by_tool[A_tool][B_tool]["non_unique"] += 1
                else:
                    pairwise_by_tool[A_tool][B_tool]["unique"] += 1

        results_uniques.append((res, uniques_for_res, non_uniques_for_res))

    meta = {
        "totals_by_tool": totals_by_tool,
        "pairwise_by_tool": pairwise_by_tool,
    }
    # Example:
    # Totals by tool:
    #   GECCO       unique=  0  non_unique= 14  total= 14
    #   antiSMASH   unique= 15  non_unique=  3  total= 18
    #   deepBGC JSON  unique= 82  non_unique= 10  total= 92
    #
    # Pairwise by tool (directional A against B):
    #   GECCO      vs antiSMASH   unique=  2  non_unique= 12
    #   GECCO      vs deepBGC JSON  unique=  1  non_unique= 13
    #   antiSMASH  vs GECCO       unique= 18  non_unique=  0
    #   antiSMASH  vs deepBGC JSON  unique= 15  non_unique=  3
    #   deepBGC JSON vs GECCO       unique= 89  non_unique=  3
    #   deepBGC JSON vs antiSMASH   unique= 82  non_unique= 10

    return results_uniques, meta












