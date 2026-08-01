import itertools
import PySpice

from charlib.characterizer import utils
from charlib.characterizer.cell import Port
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

    # Total static power = sum of signed V*I across every pin/rail that has its own
    # source in the DC testbench built by operating_point_analysis
    total_power_W = 0.0
    for pin in cell.pins_in_netlist_order():
        match pin.role:
            case Port.Role.LOGIC if pin.name in cell.inputs:
                voltage = settings.primary_power.voltage if state_map[pin.name] == '1' else 0.0
                elem = pin.name
            case Port.Role.POWER:
                voltage, elem = settings.primary_power.voltage, settings.primary_power.subscript
            case Port.Role.GROUND:
                voltage, elem = settings.primary_ground.voltage, settings.primary_ground.subscript
            case Port.Role.NWELL:
                voltage, elem = settings.nwell.voltage, settings.nwell.subscript
            case Port.Role.PWELL:
                voltage, elem = settings.pwell.voltage, settings.pwell.subscript
            case _:
                continue
        branch = f'v{elem}'.lower()
        if branch not in analysis.branches:
            continue
        i_branch = float(analysis.branches[branch][0])
        # By SPICE convention a voltage source's branch current is defined flowing INTO its
        # positive terminal from the external circuit
        total_power_W += voltage * (-i_branch)

    power_value = (total_power_W @ PySpice.Unit.u_W).convert(
        settings.units.power.prefixed_unit
    ).value

    result = cell.liberty
    lp_group = liberty.Group('leakage_power')
    lp_group.add_attribute('when', build_when_str(state_map))
    lp_group.add_attribute('value', power_value)
    result.add_group(lp_group)
    return result
