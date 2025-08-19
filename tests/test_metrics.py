import pytest
from src.genome_mining_result import Bgc
from src.reporting.metrics import GROUPING_REGISTRY, METRIC_REGISTRY


@pytest.fixture
def sample_bgcs():
    return [
        Bgc(
            bgc_id="bgc1",
            sequence_id="seq1",
            start=0,
            end=100,
            completeness="Complete",
            product_types=["NRP"],
        ),
        Bgc(
            bgc_id="bgc2",
            sequence_id="seq2",
            start=100,
            end=200,
            completeness="Incomplete",
            product_types=["PKS"],
        ),
        Bgc(
            bgc_id="bgc3",
            sequence_id="seq3",
            start=200,
            end=300,
            completeness="Complete",
            product_types=["NRP", "PKS"],
        ),
        Bgc(
            bgc_id="bgc4",
            sequence_id="seq4",
            start=300,
            end=400,
            completeness="Unknown",
            product_types=[],
        ),
    ]


def test_total_bgc_count(sample_bgcs):
    metric_func = METRIC_REGISTRY.get("total_bgc_count")
    assert metric_func(sample_bgcs) == 4


def test_mean_bgc_length(sample_bgcs):
    metric_func = METRIC_REGISTRY.get("mean_bgc_length")
    assert metric_func(sample_bgcs) == 100.0


def test_grouping_by_completeness(sample_bgcs):
    grouping_func = GROUPING_REGISTRY.get("completeness")
    assert grouping_func(sample_bgcs[0]) == "Complete"
    assert grouping_func(sample_bgcs[1]) == "Incomplete"
    assert grouping_func(sample_bgcs[2]) == "Complete"
    assert grouping_func(sample_bgcs[3]) == "Unknown"


def test_grouping_by_product_type(sample_bgcs):
    grouping_func = GROUPING_REGISTRY.get("product_type")
    assert grouping_func(sample_bgcs[0]) == "NRP"
    assert grouping_func(sample_bgcs[1]) == "PKS"
    assert grouping_func(sample_bgcs[2]) == "Hybrid"
    assert grouping_func(sample_bgcs[3]) == "Unknown"


def test_invalid_grouping_key():
    with pytest.raises(ValueError, match="Unknown grouping key: invalid_key"):
        GROUPING_REGISTRY.get("invalid_key")


def test_invalid_metric_name():
    with pytest.raises(ValueError, match="Unknown metric: invalid_metric"):
        METRIC_REGISTRY.get("invalid_metric")
