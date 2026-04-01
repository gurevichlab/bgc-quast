from pathlib import Path

import pytest
from src.compare_to_ref_data import Intersection, RecoveryContiguity, ReferenceBgc, Status
from src.genome_mining_result import Bgc, GenomeMiningResult
from src.reporting.metrics import GROUPING_REGISTRY
from src.reporting.metrics_calculators import CompareToRefMetricsCalculator
from src.reporting.report_config import (
    GroupingDimensionConfig,
    MetricConfig,
    ReportConfig,
)


def create_bgc(
    bgc_id,
    product_types,
    completeness="Complete",
    sequence_id="contig_1",
    start=100,
    end=500,
    gene_count=5,
):
    return Bgc(
        bgc_id=bgc_id,
        sequence_id=sequence_id,
        start=start,
        end=end,
        completeness=completeness,
        product_types=product_types,
        metadata={},
        gene_count=gene_count,
    )


def create_reference_bgc(
    bgc_id,
    product_types,
    completeness="Complete",
    status=Status.MISSED,
    contiguity=None,
    recovered_product_types=None,
    sequence_id="ref_1",
    start=100,
    end=500,
):
    ref_bgc = ReferenceBgc.from_bgc(
        create_bgc(
            bgc_id=bgc_id,
            product_types=product_types,
            completeness=completeness,
            sequence_id=sequence_id,
            start=start,
            end=end,
        )
    )
    ref_bgc.status = status
    ref_bgc.recovery_contiguity = contiguity
    ref_bgc.recovered_product_types = recovered_product_types or []
    return ref_bgc


def attach_intersection(
    ref_bgc,
    assembly_bgc,
    start_in_ref=100,
    end_in_ref=500,
    reversed=False,
):
    ref_bgc.intersecting_assembly_bgcs.append(
        Intersection(
            assembly_bgc=assembly_bgc,
            start_in_ref=start_in_ref,
            end_in_ref=end_in_ref,
            reversed=reversed,
        )
    )


def create_config(metric_names, grouping_dims=None):
    grouping_dims = grouping_dims or []
    return ReportConfig(
        metrics=[MetricConfig(name=name, display_name=name) for name in metric_names],
        grouping_dimensions={dim: GroupingDimensionConfig() for dim in grouping_dims},
        grouping_combinations=[grouping_dims] if len(grouping_dims) > 1 else [],
    )


def calculate_metrics(assembly_bgcs, reference_bgcs, metric_names, grouping_dims=None):
    result = GenomeMiningResult(
        input_file=Path("assembly.gbk"),
        input_file_label="assembly",
        mining_tool="test_tool",
        bgcs=assembly_bgcs,
    )
    calculator = CompareToRefMetricsCalculator(
        [(result, reference_bgcs)],
        create_config(metric_names, grouping_dims),
    )
    return calculator.calculate_metrics()


def metric_map(metric_values, metric_name):
    result = {}
    for metric_value in metric_values:
        if metric_value.metric_name != metric_name:
            continue
        key = tuple(sorted(metric_value.grouping.items()))
        result[key] = metric_value.value
    return result


def _group_label(bgc, dim):
    return GROUPING_REGISTRY.get(dim)(bgc)


def _mapped_assembly_bgcs(reference_bgcs):
    mapped = {}
    for ref in reference_bgcs:
        for intr in ref.intersecting_assembly_bgcs:
            asm = intr.assembly_bgc
            asm_id = id(asm)
            if asm_id not in mapped:
                mapped[asm_id] = (asm, [ref])
            else:
                mapped[asm_id][1].append(ref)
    return mapped


def _is_misclassified(assembly_bgc, mapped_refs):
    return not any(
        set(assembly_bgc.product_types).issubset(set(ref.product_types))
        for ref in mapped_refs
    )


def _recovery_bucket(ref_bgc):
    if ref_bgc.status == Status.MISSED:
        return "missed"
    if ref_bgc.status == Status.PARTIALLY_RECOVERED:
        return "partial"
    if ref_bgc.status == Status.FULLY_RECOVERED:
        if ref_bgc.recovery_contiguity == RecoveryContiguity.MULTI_CONTIG:
            return "full_multi_contig"
        return "full_single_contig"
    return ref_bgc.status.name.lower()


def print_report_debug(reference_bgcs, assembly_bgcs, metric_values, title=None):
    if title:
        print(f"\n=== {title} ===")

    metric_names = sorted({m.metric_name for m in metric_values})
    metric_lookup = {}
    for metric_value in metric_values:
        grouping_key = tuple(sorted(metric_value.grouping.items()))
        metric_lookup[(metric_value.metric_name, grouping_key)] = metric_value.value

    mapped = _mapped_assembly_bgcs(reference_bgcs)
    mapped_ids = set(mapped.keys())

    print("\n--- REF / ASSEMBLY MAPPING TABLE ---")
    header = [
        "REF_ID",
        "REF_PRODUCTS",
        "REF_GROUP",
        "REF_COMPLETENESS",
        "REF_STATUS_BUCKET",
        "ASSEMBLY_ID",
        "ASM_PRODUCTS",
        "ASM_GROUP",
        "ASM_COMPLETENESS",
        "ASM_MISCLASSIFIED",
    ]
    print("\t".join(header))

    seen_pairs = set()
    for ref in reference_bgcs:
        ref_group = _group_label(ref, "product_type")
        ref_status_bucket = _recovery_bucket(ref)
        if ref.intersecting_assembly_bgcs:
            for intr in ref.intersecting_assembly_bgcs:
                asm = intr.assembly_bgc
                pair_key = (ref.bgc_id, asm.bgc_id, intr.start_in_ref, intr.end_in_ref)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                asm_group = _group_label(asm, "product_type")
                asm_misclassified = _is_misclassified(asm, mapped[id(asm)][1])
                row = [
                    ref.bgc_id,
                    ",".join(ref.product_types),
                    ref_group,
                    ref.completeness,
                    ref_status_bucket,
                    asm.bgc_id,
                    ",".join(asm.product_types),
                    asm_group,
                    asm.completeness,
                    str(asm_misclassified),
                ]
                print("\t".join(row))
        else:
            row = [
                ref.bgc_id,
                ",".join(ref.product_types),
                ref_group,
                ref.completeness,
                ref_status_bucket,
                "-",
                "-",
                "-",
                "-",
                "-",
            ]
            print("\t".join(row))

    for asm in assembly_bgcs:
        if id(asm) in mapped_ids:
            continue
        asm_group = _group_label(asm, "product_type")
        row = [
            "-",
            "-",
            "-",
            "-",
            "-",
            asm.bgc_id,
            ",".join(asm.product_types),
            asm_group,
            asm.completeness,
            "UNMAPPED",
        ]
        print("\t".join(row))

    print("\n--- METRIC TABLE ---")
    metric_header = ["GROUPING"] + metric_names
    print("\t".join(metric_header))

    grouping_keys = sorted(
        {tuple(sorted(m.grouping.items())) for m in metric_values},
        key=lambda x: (len(x), x),
    )

    for grouping_key in grouping_keys:
        grouping_label = "(Total)" if not grouping_key else ", ".join(
            f"{k}={v}" for k, v in grouping_key
        )
        row = [grouping_label]
        for metric_name in metric_names:
            value = metric_lookup.get((metric_name, grouping_key), "")
            row.append(str(value))
        print("\t".join(row))


def debug_calculate_metrics(
    assembly_bgcs,
    reference_bgcs,
    metric_names,
    grouping_dims=None,
    title=None,
):
    result = calculate_metrics(
        assembly_bgcs,
        reference_bgcs,
        metric_names,
        grouping_dims=grouping_dims,
    )
    print_report_debug(
        reference_bgcs=reference_bgcs,
        assembly_bgcs=assembly_bgcs,
        metric_values=result,
        title=title,
    )
    return result


@pytest.mark.parametrize(
    "ref_products_per_ref, asm_products, expected_misclassified",
    [
        ([["NRP"]], ["NRP"], 0),
        ([["NRP", "PKS"]], ["NRP"], 0),
        ([["NRP"]], ["NRP", "PKS"], 1),
        ([["PKS"]], ["NRP"], 1),
        ([["NRP"], ["NRP", "PKS"]], ["NRP", "PKS"], 0),
        ([["NRP"], ["PKS"]], ["NRP", "PKS"], 1),
        ([["NRP"], ["NRP"]], ["NRP"], 0),
        ([["NRP"], ["RiPP"]], ["NRP"], 0),
    ],
)
def test_misclassified_total_for_single_assembly_cases(
    ref_products_per_ref,
    asm_products,
    expected_misclassified,
):
    assembly_bgc = create_bgc("asm", asm_products)
    reference_bgcs = []

    for i, ref_products in enumerate(ref_products_per_ref, start=1):
        ref_bgc = create_reference_bgc(
            f"ref_{i}",
            ref_products,
            status=Status.FULLY_RECOVERED,
            contiguity=RecoveryContiguity.SINGLE_CONTIG,
            recovered_product_types=asm_products,
            start=100 * i,
            end=100 * i + 400,
        )
        attach_intersection(
            ref_bgc,
            assembly_bgc,
            start_in_ref=ref_bgc.start,
            end_in_ref=ref_bgc.end,
        )
        reference_bgcs.append(ref_bgc)

    metrics = debug_calculate_metrics(
        [assembly_bgc],
        reference_bgcs,
        ["misclassified_product_type_count"],
        title="single assembly cases",
    )

    assert metric_map(metrics, "misclassified_product_type_count") == {
        (): expected_misclassified
    }


def test_two_assemblies_to_one_reference_can_be_counted_separately():
    ref_bgc = create_reference_bgc(
        "ref_hybrid",
        ["NRP", "PKS"],
        status=Status.FULLY_RECOVERED,
        contiguity=RecoveryContiguity.MULTI_CONTIG,
        recovered_product_types=["NRP", "PKS"],
    )
    asm1 = create_bgc("asm1", ["NRP"], start=100, end=250)
    asm2 = create_bgc("asm2", ["PKS"], start=260, end=500)
    attach_intersection(ref_bgc, asm1, start_in_ref=100, end_in_ref=250)
    attach_intersection(ref_bgc, asm2, start_in_ref=260, end_in_ref=500)

    metrics = debug_calculate_metrics(
        [asm1, asm2],
        [ref_bgc],
        ["misclassified_product_type_count"],
        title="two assemblies to one reference",
    )

    assert metric_map(metrics, "misclassified_product_type_count") == {(): 0}


def test_two_assemblies_to_one_reference_one_can_be_misclassified():
    ref_bgc = create_reference_bgc(
        "ref_nrp",
        ["NRP"],
        status=Status.FULLY_RECOVERED,
        contiguity=RecoveryContiguity.MULTI_CONTIG,
        recovered_product_types=["NRP"],
    )
    asm_ok = create_bgc("asm_ok", ["NRP"], start=100, end=250)
    asm_bad = create_bgc("asm_bad", ["NRP", "PKS"], start=260, end=500)
    attach_intersection(ref_bgc, asm_ok, start_in_ref=100, end_in_ref=250)
    attach_intersection(ref_bgc, asm_bad, start_in_ref=260, end_in_ref=500)

    metrics = debug_calculate_metrics(
        [asm_ok, asm_bad],
        [ref_bgc],
        ["misclassified_product_type_count"],
        title="one assembly misclassified",
    )

    assert metric_map(metrics, "misclassified_product_type_count") == {(): 1}


def test_unmapped_assembly_count_only_counts_non_overlapping_assemblies():
    ref_bgc = create_reference_bgc(
        "ref1",
        ["NRP"],
        status=Status.FULLY_RECOVERED,
        contiguity=RecoveryContiguity.SINGLE_CONTIG,
        recovered_product_types=["NRP"],
    )
    asm_mapped = create_bgc("asm_mapped", ["NRP"], start=100, end=500)
    asm_unmapped = create_bgc("asm_unmapped", ["PKS"], start=600, end=900)
    attach_intersection(ref_bgc, asm_mapped)

    metrics = debug_calculate_metrics(
        [asm_mapped, asm_unmapped],
        [ref_bgc],
        ["unmapped_assembly_bgcs_count", "misclassified_product_type_count"],
        title="unmapped assembly count",
    )

    assert metric_map(metrics, "unmapped_assembly_bgcs_count") == {(): 1}
    assert metric_map(metrics, "misclassified_product_type_count") == {(): 0}


def test_deduplication_same_assembly_multiple_intersections_counts_once():
    ref_bgc = create_reference_bgc(
        "ref1",
        ["NRP"],
        status=Status.PARTIALLY_RECOVERED,
        contiguity=RecoveryContiguity.MULTI_CONTIG,
        recovered_product_types=["NRP", "PKS"],
    )
    asm = create_bgc("asm1", ["NRP", "PKS"])
    attach_intersection(ref_bgc, asm, start_in_ref=100, end_in_ref=180)
    attach_intersection(ref_bgc, asm, start_in_ref=300, end_in_ref=420)

    metrics = debug_calculate_metrics(
        [asm],
        [ref_bgc],
        ["misclassified_product_type_count"],
        title="deduplication multiple intersections",
    )

    assert metric_map(metrics, "misclassified_product_type_count") == {(): 1}


def test_recovery_rate_is_independent_of_product_type():
    ref_recovered = create_reference_bgc(
        "ref_recovered",
        ["NRP"],
        status=Status.FULLY_RECOVERED,
        contiguity=RecoveryContiguity.SINGLE_CONTIG,
        recovered_product_types=["PKS"],
    )
    ref_missed = create_reference_bgc(
        "ref_missed",
        ["PKS"],
        status=Status.MISSED,
        recovered_product_types=[],
    )

    metrics = debug_calculate_metrics(
        [],
        [ref_recovered, ref_missed],
        ["recovery_rate"],
        title="recovery rate independent of product type",
    )

    assert metric_map(metrics, "recovery_rate") == {(): 0.5}


def test_reference_side_product_grouping_uses_reference_label_for_hybrid():
    ref_bgc = create_reference_bgc(
        "ref_hybrid",
        ["NRP", "PKS"],
        status=Status.FULLY_RECOVERED,
        contiguity=RecoveryContiguity.MULTI_CONTIG,
        recovered_product_types=["NRP", "PKS"],
    )
    asm1 = create_bgc("asm1", ["NRP"], start=100, end=250)
    asm2 = create_bgc("asm2", ["PKS"], start=260, end=500)
    attach_intersection(ref_bgc, asm1, start_in_ref=100, end_in_ref=250)
    attach_intersection(ref_bgc, asm2, start_in_ref=260, end_in_ref=500)

    metrics = debug_calculate_metrics(
        [asm1, asm2],
        [ref_bgc],
        ["fully_recovered_bgcs_count"],
        grouping_dims=["product_type"],
        title="reference-side grouping for hybrid",
    )

    assert metric_map(metrics, "fully_recovered_bgcs_count") == {
        (): 1,
        (("product_type", "Hybrid"),): 1,
    }


def test_mismatch_grouping_by_assembly_product_type_sums_to_total():
    ref_nrp = create_reference_bgc("ref_nrp", ["NRP"], status=Status.FULLY_RECOVERED)
    ref_pks = create_reference_bgc("ref_pks", ["PKS"], status=Status.FULLY_RECOVERED)
    ref_unknown = create_reference_bgc(
        "ref_unknown", ["Unknown product"], status=Status.FULLY_RECOVERED
    )
    ref_hybrid = create_reference_bgc(
        "ref_hybrid", ["NRP", "PKS"], status=Status.FULLY_RECOVERED
    )

    asm_nrp = create_bgc("asm_nrp", ["NRP", "RiPP"], completeness="Complete")
    asm_pks = create_bgc("asm_pks", ["PKS", "RiPP"], completeness="Incomplete")
    asm_hybrid = create_bgc(
        "asm_hybrid", ["NRP", "PKS", "RiPP"], completeness="Complete"
    )
    asm_unknown = create_bgc(
        "asm_unknown", ["Unknown product", "RiPP"], completeness="Unknown completeness"
    )

    attach_intersection(ref_nrp, asm_nrp)
    attach_intersection(ref_pks, asm_pks)
    attach_intersection(ref_hybrid, asm_hybrid)
    attach_intersection(ref_unknown, asm_unknown)

    metrics = debug_calculate_metrics(
        [asm_nrp, asm_pks, asm_hybrid, asm_unknown],
        [ref_nrp, ref_pks, ref_unknown, ref_hybrid],
        ["misclassified_product_type_count"],
        grouping_dims=["product_type"],
        title="mismatch grouped by assembly product type",
    )

    observed = metric_map(metrics, "misclassified_product_type_count")
    assert observed[()] == 4
    assert observed[(("product_type", "Hybrid"),)] == 4
    assert sum(value for key, value in observed.items() if len(key) == 1) == observed[()]


def test_mismatch_grouping_by_assembly_completeness_sums_to_total():
    ref_nrp = create_reference_bgc("ref_nrp", ["NRP"], status=Status.FULLY_RECOVERED)
    ref_pks = create_reference_bgc("ref_pks", ["PKS"], status=Status.FULLY_RECOVERED)
    ref_ripp = create_reference_bgc("ref_ripp", ["RiPP"], status=Status.FULLY_RECOVERED)

    asm_complete = create_bgc("asm_complete", ["NRP", "PKS"], completeness="Complete")
    asm_incomplete = create_bgc(
        "asm_incomplete", ["PKS", "NRP"], completeness="Incomplete"
    )
    asm_unknown = create_bgc(
        "asm_unknown", ["RiPP", "NRP"], completeness="Unknown completeness"
    )

    attach_intersection(ref_nrp, asm_complete)
    attach_intersection(ref_pks, asm_incomplete)
    attach_intersection(ref_ripp, asm_unknown)

    metrics = debug_calculate_metrics(
        [asm_complete, asm_incomplete, asm_unknown],
        [ref_nrp, ref_pks, ref_ripp],
        ["misclassified_product_type_count"],
        grouping_dims=["completeness"],
        title="mismatch grouped by assembly completeness",
    )

    observed = metric_map(metrics, "misclassified_product_type_count")
    assert observed[()] == 3
    assert observed[(("completeness", "Complete"),)] == 1
    assert observed[(("completeness", "Incomplete"),)] == 1
    assert observed[(("completeness", "Unknown completeness"),)] == 1
    assert sum(value for key, value in observed.items() if len(key) == 1) == observed[()]


def test_mismatch_grouping_by_product_type_and_completeness_sums_to_total():
    ref_a = create_reference_bgc("ref_a", ["NRP"], status=Status.FULLY_RECOVERED)
    ref_b = create_reference_bgc("ref_b", ["PKS"], status=Status.FULLY_RECOVERED)
    ref_c = create_reference_bgc("ref_c", ["RiPP"], status=Status.FULLY_RECOVERED)
    ref_d = create_reference_bgc(
        "ref_d", ["Unknown product"], status=Status.FULLY_RECOVERED
    )

    asm1 = create_bgc("asm1", ["NRP", "PKS"], completeness="Complete")
    asm2 = create_bgc("asm2", ["PKS", "RiPP"], completeness="Incomplete")
    asm3 = create_bgc(
        "asm3", ["Unknown product", "RiPP"], completeness="Unknown completeness"
    )

    attach_intersection(ref_a, asm1)
    attach_intersection(ref_b, asm2)
    attach_intersection(ref_d, asm3)

    metrics = debug_calculate_metrics(
        [asm1, asm2, asm3],
        [ref_a, ref_b, ref_c, ref_d],
        ["misclassified_product_type_count"],
        grouping_dims=["product_type", "completeness"],
        title="mismatch grouped by assembly product type and completeness",
    )

    observed = metric_map(metrics, "misclassified_product_type_count")
    assert observed[()] == 3
    assert observed[(("completeness", "Complete"), ("product_type", "Hybrid"))] == 1
    assert observed[(("completeness", "Incomplete"), ("product_type", "Hybrid"))] == 1
    assert observed[
        (("completeness", "Unknown completeness"), ("product_type", "Hybrid"))
    ] == 1
    assert (
        sum(value for key, value in observed.items() if len(key) == 2)
        == observed[()]
    )