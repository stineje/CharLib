import matplotlib.pyplot as plt
import inspect

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
    t_simend = 100 * in_slew
    vdd = settings.vdd.voltage * settings.units.voltage
    vss = settings.vss.voltage * settings.units.voltage
    vpw = settings.pwell.voltage * settings.units.voltage
    vnw = settings.nwell.voltage * settings.units.voltage

    # Initialize circuit
    circuit = Circuit(trial_name)
    circuit.include(cell.model)
    circuit.include(cell.netlist)
    (v_start, v_end) = (vss, vdd) if harness.in_direction == 'rise' else (vdd, vss)
    pwl_values = [(0, v_start), (t_start, v_start), (t_end, v_end), (t_simend, v_end)]
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
    circuit.V('o_cap', 'vout', 'wout', 0)
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

    # Initialize simulator
    simulator = circuit.simulator(temperature=settings.temperature,
                                  nominal_temperature=settings.temperature,
                                  simulator=settings.simulator)
    simulator.options('nopage', 'nomod', 'autostop', post=1, ingold=2)

    # Measure delay
    if harness.in_direction == 'rise':
        v_prop_start = settings.logic_low_to_high_threshold_voltage()
    else:
        v_prop_start = settings.logic_high_to_low_threshold_voltage()
    if harness.out_direction == 'rise':
        v_prop_end = settings.logic_low_to_high_threshold_voltage()
        v_trans_start = settings.logic_threshold_low_voltage()
        v_trans_end = settings.logic_threshold_high_voltage()
    else:
        v_prop_end = settings.logic_low_to_high_threshold_voltage()
        v_trans_start = settings.logic_threshold_high_voltage()
        v_trans_end = settings.logic_threshold_low_voltage()
    simulator.measure('tran', 'prop_in_out',
                      f'trig v(Vin) val={v_prop_start} {harness.in_direction}=1',
                      f'targ v(Vout) val={v_prop_end} {harness.out_direction}=1')
    simulator.measure('tran', 'trans_out',
                      f'trig v(Vout) val={v_trans_start} {harness.out_direction}=1',
                      f'targ v(Vout) val={v_trans_end} {harness.out_direction}=1')

    # Measure energy
    if not energy:
        simulator.measure('tran', 'energy_start',
                          f"when v(Vin)='{str(settings.energy_meas_low_threshold_voltage())}' {harness.in_direction}=1")
        simulator.measure('tran', 'energy_end',
                          f"when v(Vout)='{str(settings.energy_meas_high_threshold_voltage())}' {harness.out_direction}=1")
    else:
        [energy_start, energy_end] = energy
        simulator.measure('tran', 'q_in_dyn',
                          f'integ i(Vin) from={energy_start} to={energy_end * settings.energy_meas_time_extent}')
        simulator.measure('tran', 'q_out_dyn',
                          f'integ i(Vo_cap) from={energy_start} to={energy_end * settings.energy_meas_time_extent}')
        simulator.measure('tran', 'q_vdd_dyn',
                          f'integ i(Vdd_dyn) from={energy_start} to={energy_end * settings.energy_meas_time_extent}')
        simulator.measure('tran', 'q_vss_dyn',
                          f'integ i(Vss_dyn), from={energy_start} to={energy_end * settings.energy_meas_time_extent}')
        simulator.measure('tran', 'i_vdd_leak',
                          f'avg i(Vdd_dyn) from={0.1 * t_start} to={t_start}')
        simulator.measure('tran', 'i_vss_leak',
                          f'avg i(Vss_dyn) from={0.1 * t_start} to={t_start}')
        simulator.measure('tran', 'i_in_leak',
                          f'avg i(Vin) from={0.1 * t_start} to={t_start}')

    print(str(simulator))

    # Run transient analysis and extract results
    analysis = simulator.transient(step_time=cell.sim_timestep, end_time=t_simend)

    walk_members(analysis)

    if 'io' in cell.plots:
        # Generate plots for Vin and Vout
        figure, (ax_i, ax_o) = plt.subplots(2, sharex=True)
        figure.suptitle('I/O Voltage vs. Time')
        
        # Set up Vin plot
        ax_i.grid()
        ax_i.set_ylabel(f'Vin (pin {harness.target_in_port}) [{str(settings.units.voltage.prefixed_unit)}]')
        ax_i.plot(analysis.time, analysis['vin'])

        # Set up Vout plot
        ax_o.grid()
        ax_o.set_ylabel(f'Vout (pin {harness.target_out_port}) [{str(settings.units.voltage.prefixed_unit)}]')
        ax_o.set_xlabel(f'Time [{str(settings.units.time.prefixed_unit)}]')
        ax_o.plot(analysis.time, analysis['vout'])

        # Add horizontal lines indicating logic levels and energy measurement bounds
        for ax in [ax_i, ax_o]:
            for level in [settings.logic_threshold_low_voltage(), settings.logic_threshold_high_voltage()]:
                ax.axhline(level, color='0.5', linestyle='--')
            for level in [settings.energy_meas_low_threshold_voltage(), settings.energy_meas_high_threshold_voltage()]:
                ax.axhline(level, color='g', linestyle=':')

        # Add vertical lines indicating timing
        for ax in [ax_i, ax_o]:
            for t in [t_start, t_end]:
                ax.axvline(float(t), color='r', linestyle=':')

        plt.show(block=False)

    return analysis

def walk_members(obj, indent=0):
    for k in inspect.getmembers(obj):
        if not k[0].startswith('_'):
            print(k)