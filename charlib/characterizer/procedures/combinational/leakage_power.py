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
    circuit = utils.init_circuit(
        'leakage', cell.netlist, config.models, settings.named_nodes, settings.units
    )

    connections = []
    for pin in cell.pins_in_netlist_order():
        match pin.role:
            case Port.Role.LOGIC:
                connections.append(f'v{pin.name}')
                if pin.name in cell.inputs:
                    v = settings.primary_power.voltage if state_map[pin.name] == '1' else 0
                    circuit.V(pin.name, f'v{pin.name}', circuit.gnd, v * settings.units.voltage)
                # outputs: node named v{pin.name}, driven to DC rail by the cell, no load
            case Port.Role.POWER:
                connections.append(settings.primary_power.name)
            case Port.Role.GROUND:
                connections.append(settings.primary_ground.name)
            case Port.Role.NWELL:
                connections.append(settings.nwell.name)
            case Port.Role.PWELL:
                connections.append(settings.pwell.name)
            case _:
                raise ValueError(f'Unable to connect unrecognized pin {pin.name} in cell {cell.name}')
    circuit.X('dut', cell.name, *connections)

    simulator = PySpice.Simulator.factory(simulator=settings.simulation.backend)
    simulation = simulator.simulation(
        circuit,
        temperature=settings.temperature,
        nominal_temperature=settings.temperature
    )
    simulation.options('nopage', 'nomod')
    simulation.operating_point()

    if settings.debug:
        debug_path = settings.debug_dir / cell.name / __name__.split('.')[-1]
        debug_path.mkdir(parents=True, exist_ok=True)
        with open(debug_path / f'state = {state_map}.sp', 'w', encoding='utf-8') as f:
            f.write(str(simulation))

    if settings.dry_run:
        # TODO: Display a message if not settings.quiet
        power_value = -1
    else:
        try:
            analysis = simulator.run(simulation)
        except Exception as e:
            msg = (f'Procedure measure_leakage_for_state failed for cell {cell.name} '
                   f'with state {state_map}')
            raise ProcedureFailedException(msg) from e

        # Branch current: ngspice names it <element_name>#branch, simplified to <element_name> (lower)
        i_vdd = float(analysis.branches[settings.primary_power.name.lower()][0])
        power_W = settings.primary_power.voltage * abs(i_vdd)
        power_value = (power_W @ PySpice.Unit.u_W).convert(
            settings.units.power.prefixed_unit
        ).value

    result = cell.liberty
    lp_group = liberty.Group('leakage_power')
    lp_group.add_attribute('when', build_when_str(state_map))
    lp_group.add_attribute('value', power_value)
    result.add_group(lp_group)
    return result
