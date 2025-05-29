import pytest
from src.genome_mining_result import Bgc
from src.metrics import MetricsEngine

# filepath: bgc-quast/src/test_metrics.py


def test_compute_group_by_completeness():
    """Test grouping by completeness."""
    bgcs = [
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Complete",
            product_types=["PKS"],
            start=0,
            end=100,
        ),
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Incomplete",
            product_types=["NRPS"],
            start=50,
            end=150,
        ),
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Complete",
            product_types=["PKS"],
            start=200,
            end=300,
        ),
    ]
    engine = MetricsEngine(bgcs)
    result = engine.compute(group_by=["completeness"])

    assert len(result) == 2
    assert result[("Complete",)]["total_bgc_count"] == 2
    assert result[("Incomplete",)]["total_bgc_count"] == 1
    assert result[("Complete",)]["mean_bgc_length"] == 100
    assert result[("Incomplete",)]["mean_bgc_length"] == 100


def test_compute_group_by_product_type():
    """Test grouping by product type."""
    bgcs = [
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Complete",
            product_types=["PKS"],
            start=0,
            end=100,
        ),
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Incomplete",
            product_types=["NRPS"],
            start=50,
            end=150,
        ),
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Complete",
            product_types=["PKS", "NRPS"],
            start=200,
            end=300,
        ),
    ]
    engine = MetricsEngine(bgcs)
    result = engine.compute(group_by=["product_type"])

    assert len(result) == 3
    assert result[("PKS",)]["total_bgc_count"] == 1
    assert result[("NRPS",)]["total_bgc_count"] == 1
    assert result[("Hybrid",)]["total_bgc_count"] == 1


def test_compute_group_by_multiple_keys():
    """Test grouping by multiple keys."""
    bgcs = [
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Complete",
            product_types=["PKS"],
            start=0,
            end=100,
        ),
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Incomplete",
            product_types=["NRPS"],
            start=50,
            end=150,
        ),
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Complete",
            product_types=["PKS", "NRPS"],
            start=200,
            end=300,
        ),
    ]
    engine = MetricsEngine(bgcs)
    result = engine.compute(group_by=["completeness", "product_type"])

    assert len(result) == 3
    assert result[("Complete", "PKS")]["total_bgc_count"] == 1
    assert result[("Incomplete", "NRPS")]["total_bgc_count"] == 1
    assert result[("Complete", "Hybrid")]["total_bgc_count"] == 1


def test_compute_empty_bgcs():
    """Test compute with no BGCs."""
    engine = MetricsEngine([])
    result = engine.compute(group_by=["completeness"])

    assert result == {}


def test_compute_invalid_grouping_key():
    """Test compute with an invalid grouping key."""
    bgcs = [
        Bgc(
            bgc_id="id",
            sequence_id="_",
            completeness="Complete",
            product_types=["PKS"],
            start=0,
            end=100,
        ),
    ]
    engine = MetricsEngine(bgcs)

    with pytest.raises(ValueError, match="Invalid grouping keys: invalid_key"):
        engine.compute(group_by=["invalid_key"])
