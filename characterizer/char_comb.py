import matplotlib.pyplot as plt

from PySpice.Spice.Netlist import Circuit
from PySpice import Unit

def runCombinationalDelay(settings, cell, harness, spice_filename, in_slew, out_load):
    spice_results_filename = str(spice_filename)+"_"+str(out_load)+"_"+str(in_slew)

    ## 1st trial, extract energy_start and energy_end
    trial_results = runCombinationalTrial(settings, cell, harness, in_slew, out_load, spice_results_filename)
    energy_start = trial_results['energy_start']
    energy_end = trial_results['energy_end']

    ## 2nd trial
    trial_results = runCombinationalTrial(settings, cell, harness, in_slew, out_load, spice_results_filename, energy_start, energy_end)
    trial_results['energy_start'] = energy_start
    trial_results['energy_end'] = energy_end

    if not harness.results.get(str(in_slew)):
        harness.results[str(in_slew)] = {}
    harness.results[str(in_slew)][str(out_load)] = trial_results

def runCombinationalTrial(settings, cell, harness, in_slew, out_load, trial_name: str, *energy):
    """Run delay measurement for a single trial"""
    print(f'Running {trial_name}')

    # Set up parameters
    t_start = in_slew
    t_end = t_start + in_slew
    t_simend = 10000 * in_slew
    vdd = settings.vdd.voltage * settings.units.voltage
    vss = settings.vss.voltage * settings.units.voltage
    vpw = settings.pwell.voltage * settings.units.voltage
    vnw = settings.nwell.voltage * settings.units.voltage

    # Initialize circuit
    circuit = Circuit(trial_name)
    circuit.include(cell.model)
    circuit.include(cell.netlist)
    (v_start, v_end) = (vss, vdd) if harness.in_direction == 'rise' else (vdd, vss)
    pwl_values = [(1@Unit.u_ps, v_start), (t_start, v_start), (t_end, v_end), (t_simend, v_end)]
    circuit.PieceWiseLinearVoltageSource('in', 'vin', circuit.gnd, values=pwl_values)
    circuit.V('high', 'vhigh', circuit.gnd, vdd)
    circuit.V('low', 'vlow', circuit.gnd, vss)
    circuit.V('dd_dyn', 'vdd_dyn', circuit.gnd, vdd)
    circuit.V('ss_dyn', 'vss_dyn', circuit.gnd, vss)
    circuit.V('nw_dyn', 'vnw_dyn', circuit.gnd, vnw)
    circuit.V('pw_dyn', 'vpw_dyn', circuit.gnd, vpw)
    circuit.V('dd_leak', 'vdd_leak', circuit.gnd, vdd)
    circuit.V('ss_leak', 'vss_leak', circuit.gnd, vss)
    circuit.V('nw_leak', 'vnw_leak', circuit.gnd, vnw)
    circuit.V('pw_leak', 'vpw_leak', circuit.gnd, vpw)
    circuit.C('0', 'wout', 'vss_dyn', out_load)

    # Initialize device under test subcircuit and wire up ports
    ports = cell.definition.split()[1:]
    subcircuit_name = ports.pop(0)
    connections = []
    for port in ports:
        if port.lower() == harness.target_in_port:
            connections.append('vin')
        elif port.lower() == harness.target_out_port:
            connections.append('vout')
        elif port.lower() == settings.vdd.name.lower():
            connections.append('vdd_dyn')
        elif port.lower() == settings.vss.name.lower():
            connections.append('vss_dyn')
        elif port.lower() == settings.nwell.name.lower():
            connections.append('vnw_dyn')
        elif port.lower() == settings.pwell.name.lower():
            connections.append('vpw_dyn')
        elif port.lower() in harness.stable_in_ports:
            for stable_port, state in zip(harness.stable_in_ports, harness.stable_in_port_states):
                if port.lower() == stable_port:
                    if state == '1':
                        connections.append('vhigh')
                    elif state == '0':
                        connections.append('vlow')
                    else:
                        raise ValueError(f'Invalid state identified during simulation setup for port {port}: {state}')
        elif port.lower() in harness.nontarget_out_ports:
            for nontarget_port, state in zip(harness.nontarget_out_ports, harness.nontarget_out_port_states):
                if port.lower() == nontarget_port:
                    connections.append(f'wfloat{str(state)}')
    if len(connections) is not len(ports):
        raise ValueError(f'Failed to match all ports identified in definition "{cell.definition.strip()}"')
    circuit.X('dut', subcircuit_name, *connections)

    print(str(circuit))

    # Perform spice simulation
    simulator = circuit.simulator(temperature=settings.temperature, nominal_temperature=settings.temperature, simulator=settings.simulator)
    analysis = simulator.transient(step_time=cell.sim_timestep, end_time=t_simend)

    # Take a first attempt at plotting
    figure, ax = plt.subplots(figsize=(20, 10))
    ax.plot(analysis['vout'])
    ax.plot(analysis['vin'])
    ax.grid()
    ax.set_xlabel('Time')
    ax.set_ylabel('Voltage')
    plt.show()

    # TODO:
    # - Set up prop and trans delay probes
    # - Set up energy probes