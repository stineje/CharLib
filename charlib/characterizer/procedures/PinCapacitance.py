import numpy as np

from PySpice import Circuit, Simulator
from PySpice.Spice.unit import str_spice
from PySpice.Unit import *

def ac_sweep(cell_settings, charlib_settings, target_pin) -> float:
    """Measure the input capacitance of target_pin using an AC frequency sweep.

    Treat the cell as a grounded capacitor with fixed capacitance. With a fixed current amplitude,
    perform an AC frequency sweep on the circuit and evaluate the capacitance as
    d/ds(i(s)/v(s))."""
    vdd = charlib_settings.vdd.voltage * charlib_settings.units.voltage
    vss = charlib_settings.vss.voltage * charlib_settings.units.voltage
    # TODO: Make these values configurable
    f_start = 10 @ u_Hz
    f_stop = 10 @ u_GHz
    r_in = 10 @ u_GOhm
    i_in = 1 @ u_uA
    r_out = 10 @ u_GOhm
    c_out = 1 @ u_pF

    # Initialize circuit
    circuit_name = f'{cell_settings.cell.name}_pin_{target_pin}_cap'
    circuit = Circuit(circuit_name)
    circuit.V('dd', 'vdd', circuit.gnd, vdd)
    circuit.V('ss', 'vss', circuit.gnd, vss)
    circuit.I('in', circuit.gnd, 'vin', f'DC 0 AC {str_spice(i_in)}')
    circuit.R('in', circuit.gnd, 'vin', r_in)

    # Initialize device under test and wire up ports
    cell_settings.include_models(circuit)
    circuit.include(cell_settings.netlist)
    ports = cell_settings.definition().lower().split()[1:]
    subcircuit_name = ports.pop(0)
    connections = []
    for port in ports:
        if port == target_pin:
            connections.append('vin')
        elif port == charlib_settings.vdd.name.lower():
            connections.append('vdd')
        elif port == charlib_settings.vss.name.lower():
            connections.append('vss')
        else:
            # Add a resistor and capacitor to each other port
            # TODO: Determine whether the capacitors are actually needed.
            # In general this method for cap measurement needs further investigation.
            circuit.C(port, f'v{port}', circuit.gnd, c_out)
            circuit.R(port, f'v{port}', circuit.gnd, r_out)
            connections.append(f'v{port}')
    circuit.X('dut', subcircuit_name, *connections)

    simulator = Simulator.factory(simulator=charlib_settings.simulator)
    simulation = simulator.simulation(
        circuit,
        temperature=charlib_settings.temperature,
        nominal_temperature=charlib_settings.temperature
    )

    # Log simulation files if debugging
    if charlib_settings.debug:
        debug_path = charlib_settings.debug_dir / cell_settings.cell.name / 'in_cap_ac_sweep'
        debug_path.mkdir(parents=True, exist_ok=True)
        with open(debug_path/f'{circuit_name}.spice', 'w') as spice_file:
            spice_file.write(str(simulation))

    # Measure capacitance as the slope of the conductance with respect to frequency
    analysis = simulation.ac('dec', 100, f_start, f_stop)
    impedance = np.abs(analysis.vin)/i_in
    [capacitance, _] = np.polyfit(analysis.frequency, np.reciprocal(impedance)/(2*np.pi), 1)

    return capacitance
