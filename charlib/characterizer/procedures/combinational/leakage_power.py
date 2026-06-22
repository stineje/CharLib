import itertools
import PySpice

from charlib.characterizer import utils
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty import liberty


@register
def combinational_leakage(cell, config, settings):
    """Measure static leakage power for all 2^N input state combinations"""
    for state_bits in itertools.product('01', repeat=len(cell.inputs)):
        state_map = dict(zip(cell.inputs, state_bits))
        yield (measure_leakage_for_state, cell, config, settings, state_map)


def build_when_str(state_map):
    """Return a Liberty boolean expression for the given input state.
    Extracted to a standalone method so it can be tested in test/logic/test_combinational_leakage.py

    e.g. {'A': '0', 'B': '1'} -> '!A & B'
    """
    parts = [f'!{name}' if val == '0' else name for name, val in state_map.items()]
    return ' & '.join(parts)


def measure_leakage_for_state(cell, config, settings, state_map):
    """Run one DC operating point and write one leakage_power group to cell.liberty.

    :param cell: Cell object under test.
    :param config: CellTestConfig with model paths and cell-specific config.
    :param settings: CharacterizationSettings with library-wide config.
    :param state_map: dict mapping each logic input name to '0' or '1'.
    """
    debug_path = (settings.debug_dir / cell.name / __name__.split('.')[-1]) if settings.debug else None
    try:
        analysis = utils.operating_point_analysis(cell, config, settings, state_map, debug_path=debug_path)
    except Exception as e:
        msg = (f'Procedure measure_leakage_for_state failed for cell {cell.name} '
               f'with state {state_map}')
        raise ProcedureFailedException(msg) from e

    i_vdd = float(analysis.branches[settings.primary_power.name.lower()][0])
    power_W = settings.primary_power.voltage * abs(i_vdd)
    power_value = (power_W @ PySpice.Unit.u_W).convert(
        settings.units.power.prefixed_unit
    ).value

    when_str = build_when_str(state_map)

    # Use when_str as identifier so multiple leakage_power groups in the same cell don't collide
    result = cell.liberty
    lp_group = liberty.Group('leakage_power', f'/* {when_str} */')
    lp_group.add_attribute('when', when_str)
    lp_group.add_attribute('value', power_value)
    result.add_group(lp_group)
    return result
