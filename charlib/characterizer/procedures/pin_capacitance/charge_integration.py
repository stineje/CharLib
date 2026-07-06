import math

import PySpice
from PySpice.Unit import *

from charlib.characterizer import utils
from charlib.characterizer.cell import Port
from charlib.characterizer.procedures import register, ProcedureFailedException


@register
def charge_integration(cell, config, settings):
    """Measure input capacitance for each input pin using charge integration and return a liberty cell group"""
    roles = ['logic', 'clock', 'set', 'reset', 'enable']
    for target_pin in cell.filter_pins(direction=['input'], role=roles):
        yield (measure_pin_cap_by_charge_integration, cell, settings, config, target_pin.name)


def measure_pin_cap_by_charge_integration(cell, settings, config, target_pin):
    """Use a PWL stimulus to ramp the input through a full VDD swing and integrate i(vstim).

    Applies a VSS→VDD→VSS waveform to the target pin. The charge drawn on the rising
    and falling edges is integrated separately; C_in = (|Q_rise| + |Q_fall|) / 2 / VDD.
    All other pins are isolated with a large R and small C to ground, matching the AC
    sweep topology.

    Returns a liberty cell group with the capacitance set on the appropriate pin.
    """
    result = cell.liberty

    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # TODO: Make these values configurable
    t_slew = 0.5 @ u_ns    # ramp duration VSS→VDD (or VDD→VSS)
    t_wait = 5 * t_slew    # settling time before and between edges
    r_out  = 10 @ u_GOhm
    c_out  = 1  @ u_pF

    # Convert to SI seconds for the .meas from=/to= strings
    t_slew_s = float(t_slew.value) * float(t_slew.scale)
    t_wait_s = float(t_wait.value) * float(t_wait.scale)

    t_rise_start = t_wait_s
    t_rise_end   = t_wait_s + t_slew_s
    t_fall_start = 2 * t_wait_s + t_slew_s
    t_fall_end   = 2 * t_wait_s + 2 * t_slew_s
    t_sim_end    = 3 * t_wait + 2 * t_slew

    # Initialize circuit
    circuit_name = f'cell-{cell.name}-pin-{target_pin}-cap'
    circuit = utils.init_circuit(circuit_name, cell.netlist, config.models,
                                 settings.named_nodes, settings.units)

    # PWL stimulus: flat at VSS, ramp to VDD, flat at VDD, ramp back to VSS
    circuit.PieceWiseLinearVoltageSource('stim', 'vin', circuit.gnd, values=[
        (0 @ u_ns,                              vss),
        (t_wait,                                vss),
        (t_wait + t_slew,                       vdd),
        (t_wait + t_slew + t_wait,              vdd),
        (t_wait + t_slew + t_wait + t_slew,     vss),
    ])

    # Wire up device under test
    connections = []
    for pin in cell.pins_in_netlist_order():
        match pin.role:
            case Port.Role.POWER:
                connections.append(settings.primary_power.name)
            case Port.Role.GROUND:
                connections.append(settings.primary_ground.name)
            case Port.Role.NWELL:
                connections.append(settings.nwell.name)
            case Port.Role.PWELL:
                connections.append(settings.pwell.name)
            case _:
                if pin.name == target_pin:
                    connections.append('vin')
                else:
                    # TODO: Determine whether the capacitors are actually needed.
                    circuit.C(pin.name, f'v{pin.name}', circuit.gnd, c_out)
                    circuit.R(pin.name, f'v{pin.name}', circuit.gnd, r_out)
                    connections.append(f'v{pin.name}')
    circuit.X('dut', cell.name, *connections)

    # Set up simulation
    simulator = PySpice.Simulator.factory(simulator=settings.simulation.backend)
    simulation = simulator.simulation(
        circuit,
        temperature=settings.temperature,
        nominal_temperature=settings.temperature
    )
    simulation.options('nopage', 'nomod', post=1, ingold=2)

    # Integrate i(vstim) over each edge; i(vstim) is negative when sourcing current
    simulation.measure('tran', 'q_rise',
                       'integ i(vstim)',
                       f'from={t_rise_start:.6g}',
                       f'to={t_rise_end:.6g}',
                       run=False)
    simulation.measure('tran', 'q_fall',
                       'integ i(vstim)',
                       f'from={t_fall_start:.6g}',
                       f'to={t_fall_end:.6g}',
                       run=False)
    simulation.transient(step_time=t_slew / 10, end_time=t_sim_end, run=False)

    if settings.debug:
        debug_path = settings.debug_dir / cell.name / __name__.split('.')[-1]
        debug_path.mkdir(parents=True, exist_ok=True)
        with open(debug_path / f'{target_pin}.spice', 'w', encoding='utf-8') as spice_file:
            spice_file.write(str(simulation))

    try:
        analysis = simulator.run(simulation)
    except Exception as e:
        msg = (f'Procedure measure_pin_cap_by_charge_integration failed for cell {cell.name}, '
               f'pin {target_pin}')
        raise ProcedureFailedException(msg) from e

    q_rise = analysis.measurements.get('q_rise', float('nan'))
    q_fall = analysis.measurements.get('q_fall', float('nan'))
    if math.isnan(q_rise) or math.isnan(q_fall):
        return result

    # C = |Q| / VDD, averaged over both edges
    capacitance_F = (abs(q_rise) + abs(q_fall)) / 2 / settings.primary_power.voltage

    converted_cap = (capacitance_F @ u_F).convert(settings.units.capacitance.prefixed_unit).value
    result.group('pin', target_pin).add_attribute('capacitance', converted_cap)

    return result
