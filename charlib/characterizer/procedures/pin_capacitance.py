import numpy as np
import PySpice
from PySpice.Unit import *

def measure_input_capacitance(cell, settings, config):
    """Measure input capacitance for each input pin and return a liberty.Cell object"""
    pass # TODO

def ac_sweep(cell, settings, config, target_pin):
    """Use an AC frequency sweep to measure the capacitance of target_pin

    Treat the cell as a grounded capacitor with fixed capacitance. Perform an ac sweep with fixed
    current amplitude, then evaluate capacitance as d/ds(i(s)/v(s))"""

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
    circuit_name = f'cell{cell.name}-pin{target_pin}-cap'
    circuit = PySpice.Circuit(circuit_name)
    circuit.V('dd', 'vdd', circuit.gnd, vdd)
    circuit.V('ss', 'vss', circuit.gnd, vss)
    circuit.I('in', circuit.gnd, 'vin', f'DC 0 AC {PySpice.Unit.str_spice(i_in)}')
    circuit.R('in', circuit.gnd, 'vin', r_in)

    # Include relevant circuits
    for (model, libname) in config.models:
        if libname is not None:
            circuit.lib(model, libname)
        else:
            circuit.include(model)
            # TODO: if model.is_dir(), use SpiceLibrary
            # We'll also need to know what subckts are used by the netlist
    circuit.include(cell.netlist)

    # Initialize device under test and wire up ports
    for port in self.ports:
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
            circuit.C(port, f'v{port.name}', circuit.gnd, c_out)
            circuit.R(port, f'v{port.name}', circuit.gnd, r_out)
            connections.append(f'v{port}')
    circuit.X('dut', cell.name, *connections)

    simulator = PySpice.Simulator.factory(simulator=settings.simulator)
    simulation = simulator.simulation(circuit, temperature= settings.temperature)
    simulation.ac('dec', 100, f_start, f_stop, run=False)

    # TODO: Log for debugging

    # Measure capacitance as the slope of the conductance with respect to frequency
    analysis = simulator.run(simulation)
    conductance = i_in*np.reciprocal(np.abs(analysis.vin))
    [capacitance, _] = np.polynomial.polynomial.polyfit(analysis.frequency, conductance, 1)

    return capacitance
