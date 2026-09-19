import math

import pytest

from charlib.characterizer.characterizer import Characterizer
from charlib.characterizer.procedures.sequential.constraint.metastability.c2q_contour import (
    c2q_delay_limit,
    measure_setup_hold_from_contour,
)


class StubCell:
    def paths(self):
        return [('D', '01', 'Q', '01')]

    def nonmasking_conditions_for_path(self, *_):
        return [{'CLK': 1}]


class StubConfig:
    def __init__(self, delay_growth_threshold=None):
        self.parameters = {
            'delay_growth_threshold': (
                0.2 if delay_growth_threshold is None else delay_growth_threshold
            )
        }

    def variations(self, *keys):
        values = {
            'data_slews': 0.1,
            'clock_slews': 0.2,
            'metastability_constraint_search_tolerance': 0.01,
            'metastability_constraint_search_timestep': 0.005,
            'metastability_constraint_load': 0.1,
            'metastability_constraint_sweep_samples': 40,
            'delay_growth_threshold': self.parameters['delay_growth_threshold'],
        }
        yield {key: values[key] for key in keys}


def test_c2q_delay_limit_uses_fractional_growth():
    assert c2q_delay_limit(2.0, 0.2) == pytest.approx(2.4)
    assert c2q_delay_limit(2.0, 0.35) == pytest.approx(2.7)


def test_c2q_delay_limit_preserves_failed_reference():
    assert math.isinf(c2q_delay_limit(math.nan, 0.2))


@pytest.mark.parametrize(
    ('configured_threshold', 'expected_threshold'),
    [(None, 0.2), (0.35, 0.35)],
)
def test_setup_hold_tasks_use_default_or_configured_threshold(
        configured_threshold, expected_threshold):
    config = StubConfig(configured_threshold)

    tasks = list(measure_setup_hold_from_contour(StubCell(), config, object()))

    assert len(tasks) == 1
    assert tasks[0][4]['delay_growth_threshold'] == expected_threshold


@pytest.mark.parametrize('configured_threshold', [None, 0.35])
def test_programmatic_cell_uses_schema_threshold_default(monkeypatch, configured_threshold):
    monkeypatch.setattr('charlib.characterizer.characterizer.Cell', lambda *args, **kwargs: object())
    characterizer = Characterizer(lib_name='test')
    properties = {
        'netlist': 'dff.sp',
        'models': [],
        'functions': ['Q <= D'],
        'data_slews': [0.1],
    }
    if configured_threshold is not None:
        properties['delay_growth_threshold'] = configured_threshold

    characterizer.add_cell('DFF', properties)

    expected = 0.2 if configured_threshold is None else configured_threshold
    assert characterizer.cells[0][1].parameters['delay_growth_threshold'] == expected
