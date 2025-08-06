from PySpice import Circuit, Simulator
from PySpice.Unit import *

from charlib.characterizer.combinational.Harness import CombinationalHarness
from charlib.liberty.cell import TimingData

def measure_tran_prop(cell_settings, charlib_settings, target_pin, test_arc):
    """Measure combinational transient and propagation delays for a particular timing arc.

    This procedure constructs harnesses and makes delay measurements for all combinations of slew
    rate and capacitive load values with the given test arc. Results are returned in
    CombinationalHarness objects."""
    harness = CombinationalHarness(
        cell_settings,
        dict(zip([*(target_pin.function.operands), target_pin.name], test_arc))
    )

    # Set up parameters
    vdd = charlib_settings.vdd.voltage * charlib_settings.units.voltage
    vss = charlib_settings.vss.voltage * charlib_settings.units.voltage
    (v_start, v_end) = (vss, vdd) if harness.in_direction == 'rise' else (vdd, vss)
    slew_pwl = lambda t_slew: [(0, v_start), (t_slew, v_start), (2*t_slew, v_end), (1000*t_slew, v_end)]

    # Initialize circuit netlist
    circuit_name = f'delay_{cell_settings.cell.name}_{harness.short_str().replace(" ", "_")}'
    circuit = Circuit(circuit_name)
    cell_settings.include_models(circuit)
    circuit.include(cell_settings.netlist)
    circuit.PieceWiseLinearVoltageSource(
        'in',
        'vin',
        circuit.gnd,
        values=slew_pwl(cell_settings.in_slews[0] * charlib_settings.units.time)
    )
    circuit.V('high', 'vhigh', circuit.gnd, vdd)
    circuit.V('low', 'vlow', circuit.gnd, vss)
    circuit.V('dd_dyn', 'vdd_dyn', circuit.gnd, vdd)
    circuit.V('ss_dyn', 'vss_dyn', circuit.gnd, vss)
    circuit.V('o_cap', 'vout', 'wout', circuit.gnd)
    circuit.C('0', 'wout', 'vss_dyn', cell_settings.out_loads[0] * charlib_settings.units.capacitance)

    # Initiialize device under test and wire up ports
    ports = cell_settings.definition().upper().split()[1:]
    subcircuit_name = ports.pop(0)
    connections = []
    for port in ports:
        if port == harness.target_in_port.pin.name:
            connections.append('vin')
        elif port == harness.target_out_port.pin.name:
            connections.append('vout')
        elif port == charlib_settings.vdd.name.upper():
            connections.append('vdd_dyn')
        elif port == charlib_settings.vss.name.upper():
            connections.append('vss_dyn')
        elif port in [pin.pin.name for pin in harness.stable_in_ports]:
            for stable_port in harness.stable_in_ports:
                if port == stable_port.pin.name:
                    match stable_port.state:
                        case '0':
                            connections.append('vhigh')
                        case '1':
                            connections.append('vlow')
                        case s:
                            raise ValueError(f'Invalid state identified during simulation setup for port {port}: {s}')
        else:
            raise ValueError(f'Unable to connect unrecognized port {port}')
    if len(connections) is not len(ports):
        raise ValueError(f'Failed to conect all ports in definition "{cell_settings.definition()}"')
    circuit.X('dut', subcircuit_name, *connections)

    simulator = Simulator.factory(simulator='ngspice-shared')
    simulation = simulator.simulation(
        circuit,
        temperature=charlib_settings.temperature,
        nominal_temperature=charlib_settings.temperature
    )
    simulation.options('autostop', 'nopage', post=1, ingold=2, trtol=1)

    # Measure delay
    pct_vdd = lambda x : x * charlib_settings.vdd.voltage
    match harness.in_direction:
        case 'rise':
            v_prop_start = charlib_settings.logic_threshold_low_to_high
        case 'fall':
            v_prop_start = charlib_settings.logic_threshold_high_to_low
    match harness.out_direction:
        case 'rise':
            v_prop_end = charlib_settings.logic_threshold_low_to_high
            v_trans_start = charlib_settings.logic_threshold_low
            v_trans_end = charlib_settings.logic_threshold_high
        case 'fall':
            v_prop_end = charlib_settings.logic_threshold_high_to_low
            v_trans_start = charlib_settings.logic_threshold_high
            v_trans_end = charlib_settings.logic_threshold_low
    simulation.measure(
        'tran', 'prop_in_out',
        f'trig v(vin) val={pct_vdd(v_prop_start)} {harness.in_direction}=1',
        f'targ v(vout) val={pct_vdd(v_prop_end)} {harness.out_direction}=1',
        run=False
    )
    simulation.measure(
        'tran', 'trans_out',
        f'trig v(vout) val={pct_vdd(v_trans_start)} {harness.out_direction}=1',
        f'targ v(vout) val={pct_vdd(v_trans_end)} {harness.out_direction}=1',
        run=False
    )

    # Log simulation files if debugging
    if charlib_settings.debug:
        debug_path = charlib_settings.debug_dir / cell_settings.cell.name / 'delay' / harness.debug_path
        debug_path.mkdir(parents=True, exist_ok=True)
        with open(debug_path/f'{circuit_name}.spice', 'w') as spice_file:
            spice_file.write(str(simulation))

    # Run simulation & alter for each combination of slew & load
    # TODO: Figure out if alter_device actually works
    for slew in cell_settings.in_slews:
        simulator.ngspice.alter_device(f'@vin[pwl]={slew_pwl(slew * charlib_settings.units.time)}')
        for load in cell_settings.out_loads:
            simulator.ngspice.alter_device(f'C0={load * charlib_settings.units.capacitance}')
            print(f'running {circuit_name} with slew={slew}, load={load}')
            harness.results[str(slew)][str(load)] = simulation.transient(
                step_time=cell_settings.sim_timestep * charlib_settings.units.time,
                end_time=1000*slew * charlib_settings.units.time
            )

    return harness
