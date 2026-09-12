import math

import pytest

from charlib.characterizer.procedures.sequential.constraint.metastability.c2q_contour import (
    c2q_delay_limit,
)


def test_c2q_delay_limit_uses_fractional_growth():
    assert c2q_delay_limit(2.0, 0.2) == pytest.approx(2.4)
    assert c2q_delay_limit(2.0, 0.35) == pytest.approx(2.7)


def test_c2q_delay_limit_preserves_failed_reference():
    assert math.isinf(c2q_delay_limit(math.nan, 0.2))
