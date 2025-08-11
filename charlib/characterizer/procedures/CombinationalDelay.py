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
    slew_pwl = lambda t_slew: [(0, v_start), (t_slew, v_start), (2*t_slew, v_end)]

    # Initialize circuit netlist
    circuit_name = f'delay_{cell_settings.cell.name}_{harness.short_str().replace(" ", "_")}'
    print('Running', circuit_name)
    circuit = Circuit(circuit_name)
    cell_settings.include_models(circuit)
    circuit.include(cell_settings.netlist)
    circuit.PieceWiseLinearVoltageSource(
        'test',
        'vin',
        circuit.gnd,
        values=slew_pwl(cell_settings.in_slews[0] * charlib_settings.units.time)
    )
    circuit.V('high', 'vhigh', circuit.gnd, vdd)
    circuit.V('low', 'vlow', circuit.gnd, vss)
    circuit.V('dd', 'vdd', circuit.gnd, vdd)
    circuit.V('ss', 'vss', circuit.gnd, vss)
    circuit.C('load', 'vout', 'vss', cell_settings.out_loads[0] * charlib_settings.units.capacitance)

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
            connections.append('vdd')
        elif port == charlib_settings.vss.name.upper():
            connections.append('vss')
        elif port in [pin.pin.name for pin in harness.stable_in_ports]:
            for stable_port in harness.stable_in_ports:
                if port == stable_port.pin.name:
                    match stable_port.state:
                        case '0':
                            connections.append('vlow')
                        case '1':
                            connections.append('vhigh')
                        case s:
                            raise ValueError(f'Invalid state identified during simulation setup for port {port}: {s}')
        elif port in [pin.pin.name for pin in harness.nontarget_ports]:
            for nontarget_port in harness.nontarget_ports:
                if port == nontarget_port.pin.name:
                    connections.append(f'wfloat{nontarget_port.state}')
        else:
            raise ValueError(f'Unable to connect unrecognized port {port}')
    if len(connections) is not len(ports):
        raise ValueError(f'Failed to conect all ports in definition "{cell_settings.definition()}"')
    circuit.X('dut', subcircuit_name, *connections)

    # Set up delay measurement thresholds
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

    # Create the simulation
    simulator = Simulator.factory(simulator=charlib_settings.simulator)
    simulation = simulator.simulation(
        circuit,
        temperature=charlib_settings.temperature,
        nominal_temperature=charlib_settings.temperature
    )
    simulation.options('autostop', 'nopage', 'nomod', post=1, ingold=2, trtol=1)
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

    # Test each combination of slew & load
    for slew in cell_settings.in_slews:
        # Assign new test slew
        circuit['Vtest'].detach()
        circuit.PieceWiseLinearVoltageSource(
            'test',
            'vin',
            circuit.gnd,
            values=slew_pwl(slew * charlib_settings.units.time)
        )

        # Use slew/8 for sim timestep unless user has set a custom timestep
        # TODO: Consider allowing sim_timestep be set to a multiplied factor
        t_step = cell_settings.sim_timestep if cell_settings.sim_timestep else slew/8
        simulation.reset_analysis()
        simulation.transient(
            step_time=t_step * charlib_settings.units.time,
            end_time=10000 * t_step * charlib_settings.units.time,
            run=False
        )

        for load in cell_settings.out_loads:
            # Assign new test load
            circuit['Cload'].capacitance = load * charlib_settings.units.capacitance

            # Log simulation files if debugging
            if charlib_settings.debug:
                debug_path = charlib_settings.debug_dir / cell_settings.cell.name / 'delay' / harness.debug_path
                debug_path.mkdir(parents=True, exist_ok=True)
                with open(debug_path/f'{circuit_name}_slew{slew}_load{load}.spice', 'w') as spice_file:
                    spice_file.write(str(circuit))

            # Run the simulation
            # print(f'running {circuit_name} with slew={slew}, load={load}')
            harness.results[str(slew)][str(load)] = simulator.run(simulation)

    return harness
