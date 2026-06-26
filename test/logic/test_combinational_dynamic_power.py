import itertools
from unittest.mock import MagicMock

from charlib.characterizer.procedures.combinational.dynamic_power import (
    combinational_dynamic_power, measure_dynamic_power_for_path
)
from charlib.liberty import liberty
from charlib.liberty.library import LookupTable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cell(input_names, output_names=None):
    """Return a minimal mock Cell with the given logic input and output names."""
    if output_names is None:
        output_names = ['OUT']
    cell = MagicMock()
    cell.inputs = input_names
    cell.outputs = output_names
    paths = list(itertools.product(input_names, ['01', '10'], output_names, ['01', '10']))
    cell.paths.return_value = paths
    return cell


def _make_config(slews=None, loads=None):
    """Return a minimal mock CellTestConfig."""
    slews = slews or [0.1]
    loads = loads or [1.0]
    config = MagicMock()
    config.variations.return_value = [
        {'data_slews': s, 'loads': l, 'transient_sim_end_time': 0}
        for s, l in itertools.product(slews, loads)
    ]
    return config


# ---------------------------------------------------------------------------
# Generator tests
# ---------------------------------------------------------------------------

def test_generator_yields_four_jobs_for_one_input_one_output():
    """1-input/1-output cell with 1 variation yields 4 jobs (2 input x 2 output transitions)."""
    cell = _make_cell(['IN'], ['OUT'])
    config = _make_config()
    jobs = list(combinational_dynamic_power(cell, config, None))
    assert len(jobs) == 4


def test_generator_yields_eight_jobs_for_two_inputs_one_output():
    """2-input/1-output cell with 1 variation yields 8 jobs (2 inputs x 2 x 2 transitions)."""
    cell = _make_cell(['A', 'B'], ['OUT'])
    config = _make_config()
    jobs = list(combinational_dynamic_power(cell, config, None))
    assert len(jobs) == 8


def test_generator_scales_with_variations():
    """2 slews x 3 loads = 6 variations --> 24 jobs for a 1-input/1-output cell."""
    cell = _make_cell(['IN'], ['OUT'])
    config = _make_config(slews=[0.1, 0.2], loads=[1.0, 2.0, 3.0])
    jobs = list(combinational_dynamic_power(cell, config, None))
    assert len(jobs) == 24 


def test_generator_first_element_is_procedure_function():
    """Each yielded tuple begins with the measure_dynamic_power_for_path callable."""
    cell = _make_cell(['IN'], ['OUT'])
    config = _make_config()
    jobs = list(combinational_dynamic_power(cell, config, None))
    for job in jobs:
        assert job[0] is measure_dynamic_power_for_path


def test_generator_passes_path_as_last_element():
    """Each yielded tuple ends with one of the paths from cell.paths()."""
    cell = _make_cell(['IN'], ['OUT'])
    config = _make_config()
    jobs = list(combinational_dynamic_power(cell, config, None))
    expected_paths = cell.paths.return_value
    job_paths = [job[-1] for job in jobs]
    for path in expected_paths:
        assert path in job_paths


# ---------------------------------------------------------------------------
# Liberty structure tests
# ---------------------------------------------------------------------------

def test_internal_power_group_nested_under_pin():
    """internal_power group is nested under the output pin group."""
    pin_group = liberty.Group('pin', 'OUT')
    ip_group = liberty.Group('internal_power', '/* IN */')
    ip_group.add_attribute('related_pin', 'IN')
    pin_group.add_group(ip_group)
    assert any(g.name == 'internal_power' for g in pin_group.groups.values())


def test_rise_power_lut_in_internal_power():
    """rise_power LUT is present inside internal_power group."""
    ip_group = liberty.Group('internal_power', '/* IN */')
    lut = LookupTable('rise_power', 'energy_template_1x1',
                      total_output_net_capacitance=[1.0],
                      input_net_transition=[0.1])
    lut.values[0, 0] = 5.0
    ip_group.add_group(lut)
    assert 'rise_power' in ip_group.to_liberty()


def test_fall_power_lut_in_internal_power():
    """fall_power LUT is present inside internal_power group."""
    ip_group = liberty.Group('internal_power', '/* IN */')
    lut = LookupTable('fall_power', 'energy_template_1x1',
                      total_output_net_capacitance=[1.0],
                      input_net_transition=[0.1])
    lut.values[0, 0] = 4.5
    ip_group.add_group(lut)
    assert 'fall_power' in ip_group.to_liberty()


def test_related_pin_attribute_in_output():
    """related_pin attribute is present in the internal_power liberty output."""
    ip_group = liberty.Group('internal_power', '/* IN */')
    ip_group.add_attribute('related_pin', 'IN')
    output = ip_group.to_liberty()
    assert 'related_pin' in output
    assert 'IN' in output


def test_energy_value_appears_in_output():
    """The numeric energy value is present in the liberty output."""
    ip_group = liberty.Group('internal_power', '/* IN */')
    lut = LookupTable('rise_power', 'energy_template_1x1',
                      total_output_net_capacitance=[1.0],
                      input_net_transition=[0.1])
    lut.values[0, 0] = 7.3
    ip_group.add_group(lut)
    assert '7.3' in ip_group.to_liberty()


def test_rise_and_fall_power_coexist_in_internal_power():
    """rise_power and fall_power can both exist inside the same internal_power group."""
    ip_group = liberty.Group('internal_power', '/* IN */')
    ip_group.add_attribute('related_pin', 'IN')
    for lut_name, val in [('rise_power', 5.0), ('fall_power', 4.0)]:
        lut = LookupTable(lut_name, 'energy_template_1x1',
                          total_output_net_capacitance=[1.0],
                          input_net_transition=[0.1])
        lut.values[0, 0] = val
        ip_group.add_group(lut)
    output = ip_group.to_liberty()
    assert 'rise_power' in output
    assert 'fall_power' in output


def test_two_internal_power_groups_coexist_for_two_inputs():
    """Two internal_power groups with different related_pins coexist under the same output pin."""
    pin_group = liberty.Group('pin', 'OUT')
    for in_pin in ('A', 'B'):
        ip = liberty.Group('internal_power', f'/* {in_pin} */')
        ip.add_attribute('related_pin', in_pin)
        pin_group.add_group(ip)
    output = pin_group.to_liberty()
    assert output.count('internal_power (') == 2
    assert 'related_pin : A' in output or '"A"' in output
    assert 'related_pin : B' in output or '"B"' in output
