import numpy as np
import PySpice
from PySpice.Unit import *

from charlib.characterizer import utils
from charlib.characterizer.procedures import register
from charlib.liberty import liberty

@register
def ac_sweep(cell, config, settings):
    """Measure input capacitance for each input pin using ac sweep and return a liberty cell group"""
    # Yield simulation tasks for measuring capacitance of each pin
    for target_pin in cell.filter_ports(directions=['input'],
                                        roles=['logic', 'clock', 'set', 'reset', 'enable']):
        yield (measure_pin_cap_by_ac_sweep, cell, settings, config, target_pin.name)

def measure_pin_cap_by_ac_sweep(cell, settings, config, target_pin):
    """Use an AC frequency sweep to measure the capacitance of target_pin

    Treat the cell as a grounded capacitor with fixed capacitance. Perform an ac sweep with fixed
    current amplitude, then evaluate capacitance as d/ds(i(s)/v(s))

    Returns a liberty cell group with the capacitance included on the appropriate pin.
    """
    result = cell.liberty

    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # TODO: Make these values configurable
    f_start = 10 @ u_Hz
    f_stop = 10 @ u_GHz
    r_in = 10 @ u_GOhm
    i_in = 1 @ u_uA
    r_out = 10 @ u_GOhm
    c_out = 1 @ u_pF

    # Initialize circuit
    circuit_name = f'cell-{cell.name}-pin-{target_pin}-cap'
    circuit = utils.init_circuit(circuit_name, cell.netlist, config.models)
    circuit.V('dd', 'vdd', circuit.gnd, vdd)
    circuit.V('ss', 'vss', circuit.gnd, vss)
    circuit.I('in', circuit.gnd, 'vin', f'DC 0 AC {PySpice.Spice.unit.str_spice(i_in)}')
    circuit.R('in', circuit.gnd, 'vin', r_in)

    # Initialize device under test and wire up ports
    connections = []
    for port in cell.ports:
        if port.name == target_pin:
            connections.append('vin')
        elif port.name == settings.primary_power.name:
            connections.append('vdd')
        elif port.name == settings.primary_ground.name:
            connections.append('vss')
        else:
            # Add a resistor and capacitor to each other port
            # TODO: Determine whether the capacitors are actually needed.
            # In general this method for cap measurement needs further investigation.
            circuit.C(port.name, f'v{port.name}', circuit.gnd, c_out)
            circuit.R(port.name, f'v{port.name}', circuit.gnd, r_out)
            connections.append(f'v{port.name}')
    circuit.X('dut', cell.name, *connections)

    simulator = PySpice.Simulator.factory(simulator=settings.simulation.backend)
    simulation = simulator.simulation(circuit, temperature=settings.temperature)
    simulation.ac('dec', 100, f_start, f_stop, run=False)

    if settings.debug:
        debug_path = settings.debug_dir / cell.name / __name__
        debug_path.mkdir(parents=True, exist_ok=True)
        with open(debug_path/f'{target_pin}.spice', 'w') as spice_file:
            spice_file.write(str(simulation))

    # Measure capacitance as the slope of the conductance with respect to frequency
    analysis = simulator.run(simulation)
    conductance = np.reciprocal(np.abs(analysis.vin)/i_in)
    [*_, capacitance] = np.polynomial.polynomial.polyfit(analysis.frequency, conductance, 1)

    # Add to the liberty group
    converted_cap = (capacitance @ u_F).convert(settings.units.capacitance.prefixed_unit).value
    result.group('pin', target_pin).add_attribute('capacitance', converted_cap)

    return result
