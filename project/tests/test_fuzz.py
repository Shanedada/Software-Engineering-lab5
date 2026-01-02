from hypothesis import given, strategies as st
import pytest

from project.models import Payment


@given(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
def test_payment_charge_no_crash(amount):
    """Fuzz test: Payment.charge should not crash for valid amounts (we'll detect crash if it does)."""
    p = Payment(user=None, amount=amount)
    # We expect this to not raise; if it raises, Hypothesis will shrink and report counterexample
    p.charge()


@given(st.floats(min_value=9.0, max_value=9.999999, allow_nan=False, allow_infinity=False))
def test_payment_charge_small_range_finds_bug(amount):
    """Targeted fuzzing over the range [9.0, 10.0) which we suspect will trigger the bug."""
    p = Payment(user=None, amount=amount)
    p.charge()


def test_reproduce_known_bad_amount():
    # regression test: ensure amount == 9.0 does not crash and returns a boolean
    p = Payment(user=None, amount=9.0)
    res = p.charge()
    assert isinstance(res, bool)
