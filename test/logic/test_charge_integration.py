from types import SimpleNamespace

import pytest

from charlib.characterizer.procedures.pin_capacitance.charge_integration import (
    _combine_capacitances,
    charge_integration,
)


@pytest.mark.parametrize(
    ('criterion', 'expected'),
    [
        ('average', 3.0),
        ('min', 2.0),
        ('max', 4.0),
    ],
)
def test_combine_capacitances_with_named_criterion(criterion, expected):
    assert _combine_capacitances(2.0, 4.0, criterion) == expected


def test_combine_capacitances_defaults_to_average():
    assert _combine_capacitances(2.0, 4.0) == 3.0


def test_combine_capacitances_accepts_callable():
    weighted = lambda values: 0.25 * values[0] + 0.75 * values[1]
    assert _combine_capacitances(2.0, 4.0, weighted) == 3.5


def test_combine_capacitances_rejects_unknown_criterion():
    with pytest.raises(ValueError, match='Unknown charge integration criterion'):
        _combine_capacitances(2.0, 4.0, 'median')


def test_charge_integration_passes_configured_criterion_to_measurement():
    pin = SimpleNamespace(name='A')
    cell = SimpleNamespace(filter_pins=lambda **kwargs: [pin])
    config = SimpleNamespace(parameters={'charge_integration_criterion': 'max'})

    task, = charge_integration(cell, config, settings=None)

    assert task[-1] == 'max'
