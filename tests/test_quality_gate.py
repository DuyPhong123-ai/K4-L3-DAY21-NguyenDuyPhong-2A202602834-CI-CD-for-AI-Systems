import pytest
from src.quality_gate import check_quality


@pytest.mark.parametrize("f1", [0.0, 0.6499, float("nan"), float("inf"), 1.01])
def test_rejects_low_or_invalid_f1(f1):
    with pytest.raises(ValueError):
        check_quality(f1)


@pytest.mark.parametrize("f1", [0.65, 0.75, 1.0])
def test_accepts_quality_threshold(f1):
    check_quality(f1)
