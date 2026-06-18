from unittest.mock import MagicMock

from charlib.characterizer.procedures.combinational.leakage_power import combinational_leakage, build_when_str
from charlib.liberty import liberty


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cell(input_names):
    """Return a minimal mock Cell with the given logic input names."""
    cell = MagicMock()
    cell.inputs = input_names
    return cell

# ---------------------------------------------------------------------------
# Generator tests
# ---------------------------------------------------------------------------

def test_generator_yields_two_jobs_for_one_input():
    """Single-input cell produces exactly 2 leakage states."""
    cell = _make_cell(['IN'])
    jobs = list(combinational_leakage(cell, None, None))
    assert len(jobs) == 2


def test_generator_yields_four_jobs_for_two_inputs():
    """Two-input cell produces exactly 4 leakage states (2^2)."""
    cell = _make_cell(['A', 'B'])
    jobs = list(combinational_leakage(cell, None, None))
    assert len(jobs) == 4


def test_generator_state_maps_cover_all_combinations():
    """All 2^N input combinations appear exactly once in the yielded state_maps."""
    cell = _make_cell(['A', 'B'])
    jobs = list(combinational_leakage(cell, None, None))
    state_maps = [job[4] for job in jobs]  # state_map is the 5th element of each tuple

    expected = [
        {'A': '0', 'B': '0'},
        {'A': '0', 'B': '1'},
        {'A': '1', 'B': '0'},
        {'A': '1', 'B': '1'},
    ]
    for expected_state in expected:
        assert expected_state in state_maps


def test_generator_first_element_is_procedure_function():
    """Each yielded tuple begins with the measure_leakage_for_state callable."""
    from charlib.characterizer.procedures.combinational.leakage_power import measure_leakage_for_state
    cell = _make_cell(['IN'])
    jobs = list(combinational_leakage(cell, None, None))
    for job in jobs:
        assert job[0] is measure_leakage_for_state


# ---------------------------------------------------------------------------
# when-string tests
# ---------------------------------------------------------------------------

def test_build_when_str_single_input_low():
    """Input held low produces '!IN'."""
    assert build_when_str({'IN': '0'}) == '!IN'


def test_build_when_str_single_input_high():
    """Input held high produces 'IN'."""
    assert build_when_str({'IN': '1'}) == 'IN'


def test_build_when_str_two_inputs_both_low():
    assert build_when_str({'A': '0', 'B': '0'}) == '!A & !B'


def test_build_when_str_two_inputs_mixed():
    assert build_when_str({'A': '0', 'B': '1'}) == '!A & B'


def test_build_when_str_two_inputs_both_high():
    assert build_when_str({'A': '1', 'B': '1'}) == 'A & B'


# ---------------------------------------------------------------------------
# Liberty output structure tests
# ---------------------------------------------------------------------------

def test_liberty_group_has_correct_type():
    """leakage_power group has the right Liberty group name."""
    when = '!IN'
    lp_group = liberty.Group('leakage_power', f'/* {when} */')
    lp_group.add_attribute('when', when)
    lp_group.add_attribute('value', 12.5)
    assert lp_group.name == 'leakage_power'


def test_liberty_group_when_attribute_is_quoted_in_output():
    """Liberty serialization wraps the when condition in double quotes."""
    when = '!A & B'
    lp_group = liberty.Group('leakage_power', f'/* {when} */')
    lp_group.add_attribute('when', when)
    lp_group.add_attribute('value', 5.0)
    output = lp_group.to_liberty()
    assert f'"{when}"' in output


def test_liberty_group_value_appears_in_output():
    """Liberty serialization includes the numeric power value."""
    lp_group = liberty.Group('leakage_power', '/* !IN */')
    lp_group.add_attribute('when', '!IN')
    lp_group.add_attribute('value', 7.3)
    output = lp_group.to_liberty()
    assert '7.3' in output


def test_two_leakage_groups_coexist_in_cell_liberty():
    """Adding two leakage_power groups with different when conditions does not overwrite either."""
    cell_group = liberty.Group('cell', 'inv')

    for when, val in [('!IN', 10.0), ('IN', 5.0)]:
        lp = liberty.Group('leakage_power', f'/* {when} */')
        lp.add_attribute('when', when)
        lp.add_attribute('value', val)
        cell_group.add_group(lp)

    output = cell_group.to_liberty()
    assert output.count('leakage_power (') == 2
    assert '"!IN"' in output
    assert 'when : IN' in output
