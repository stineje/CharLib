from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.characterizer import utils

import PySpice
import numpy as np
import csv
import matplotlib.pyplot as plt

def measure_recovery_constraint(cell_settings, charlib_settings, control_pin, trigger_pin, state_pin):
    """Find the minimum time a control pin must be active before the trigger.

    This is analagous to setup time for an asynchronous control pin.

    For example, for a rising-edge DFF with an asynchronous reset, recovery time is the minimum
    time the reset signal must be active before the rising clock edge in order to reset the device
    state."""
    pass # TODO

def measure_removal_constraint(cell_settings, charlib_settings, control_pin, trigger_pin, state_pin):
    """Find the mimimum time a control pin must remain active after the trigger.

    This is analagous to hold time for an asynchronous control pin.

    For example, for a rising-edge DFF with an asynchronous reset, removal time is the minimum time
    that the reset signal must remain active after the rising clock edge in order to reset the
    device state."""
    pass # TODO

@register
def sequential_delay(cell_settings, charlib_settings, data_pin, trigger_pin, state_pin):
    """Measure the delay between trigger activation and state change.

    For clock-edge-triggered devices, this is commonly called the clock-to-Q or C2Q delay. This
    value depends on the transition time of both the data pin and the trigger pin."""
    pass # TODO

@register
def sequential_min_pulse_width(cell_settings, charlib_settings, data_pin, trigger_pin, state_pin):
    """Find the minimum pulse width required for the trigger to activate the device.

    This is analagous to the min_pulse_width property of a set, reset, enable, or clock pin.

    For example, for a rising-edge DFF with an asynchronous reset, the minimum pulse width is the
    minimum time the clock signal must be active before the rising edge in order to reset the
    device state."""
    pass # TODO

@register
def sequential_setup_hold(cell, cell_settings, charlib_settings):
    """procedure for measuring setup and hold time
    This function returns (yield) jobs to be submitted to the PoolExecutor"""
    for variation in cell_settings.variations('data_slews', 'clock_slews'):
        for path in cell.paths():
            yield (sweep_setup_hold_skew_for_c2q, cell, cell_settings, charlib_settings, variation, path)

def sweep_setup_hold_skew_for_c2q(cell, config, settings, variation, path):
    """This function takes a range of setup skew and a range of hold skew,
    and runs every single combination of the two to find the C2Q delay.
    Giving us the 3D C2Q vs setup time (ts) vs hold time (th) surface.
    """
    t_setup_skew_range = (0e-12, 700e-12)
    t_setup_skew_step = 10e-12
    t_hold_skew_range = (-500e-12, 200e-12)
    t_hold_skew_step = 10e-12

    # index 1 is setup skew, index 2 is hold skew
    c2q_values = []

    setup_skews = np.arange(t_setup_skew_range[0], t_setup_skew_range[1], t_setup_skew_step)
    hold_skews = np.arange(t_hold_skew_range[0], t_hold_skew_range[1], t_hold_skew_step)

    for t_setup_skew in setup_skews:
        c2q_hold_skew_values = []
        for t_hold_skew in hold_skews:
            t_c2q = get_c2q(cell, config, settings, variation['clock_slew'], variation['data_slew'], t_setup_skew, t_hold_skew, 40e-15, 2e-9)
            c2q_hold_skew_values.append(float(t_c2q))
        c2q_values.append(c2q_hold_skew_values)

    if settings.debug:
        debug_path = settings.debug_dir / cell.name / __name__.split('.')[-1] / f'{path[0]}_{path[1]}_to_{path[2]}_{path[3]}'
        debug_path.mkdir(parents=True, exist_ok=True)
        plot_c2q_surface(setup_skews, hold_skews, np.array(c2q_values), cell.name, debug_path)
        write_c2q_csv(setup_skews, hold_skews, c2q_values, cell.name, debug_path)

    return cell.liberty

def plot_c2q_surface(setup_skews, hold_skews, c2q_values, cell_name, debug_path):
    """Plot C2Q delay as a 3D surface over setup_skew and hold_skew."""
    setup_grid, hold_grid = np.meshgrid(setup_skews * 1e9, hold_skews * 1e9, indexing='ij')
    c2q_ns = c2q_values * 1e9

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(hold_grid, setup_grid, c2q_ns, cmap='viridis', edgecolor='none', alpha=0.9)

    # Plot red dots where C2Q failed to converge (NaN)
    nan_mask = np.isnan(c2q_ns)
    if np.any(nan_mask):
        z_min = np.nanmin(c2q_ns) if not np.all(nan_mask) else 0
        ax.scatter(hold_grid[nan_mask], setup_grid[nan_mask],
                   np.full(np.sum(nan_mask), z_min), color='red', s=20, label='did not converge')
        ax.legend()

    ax.set_xlabel('Hold Skew (ns)')
    ax.set_ylabel('Setup Skew (ns)')
    ax.invert_yaxis()
    ax.set_zlabel('C2Q Delay (ns)')
    ax.set_title(f'{cell_name} — C2Q vs Setup Skew vs Hold Skew')
    fig.colorbar(surf, ax=ax, shrink=0.5, label='C2Q (ns)')

    plt.tight_layout()
    plt.savefig(debug_path / f'{cell_name}_c2q_surface.png', dpi=150)
    plt.close(fig)

def write_c2q_csv(setup_skews, hold_skews, c2q_values, cell_name, debug_path):
    """Write C2Q delay data to a CSV file with columns: setup_skew, hold_skew, c2q."""
    with open(debug_path / f'{cell_name}_c2q.csv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter=' ')
        writer.writerow(['setup_skew', 'hold_skew', 'c2q'])
        for i, t_setup in enumerate(setup_skews):
            for j, t_hold in enumerate(hold_skews):
                writer.writerow([t_setup, t_hold, c2q_values[i][j]])

def get_c2q(cell, config, settings, clk_slew, data_slew, t_setup_skew, t_hold_skew, c_load, t_stabilizing):
    """Build a SPICE testbench and run a transient simulation to get the clock-to-q delay
    for a given setup skew / hold skew, load capacitance and stabilizing time."""

    # Set up parameters
    t_clk_slew = clk_slew * settings.units.time
    t_data_slew = data_slew * settings.units.time
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # building waveform for data
    t = {}
    t['clk_edge_1_start'] = t_stabilizing
    t['clk_edge_1_end'] = t['clk_edge_1_start'] + t_clk_slew
    t['clk_edge_2_start'] = t['clk_edge_1_end'] + t_stabilizing
    t['clk_edge_2_end'] = t['clk_edge_2_start'] + t_clk_slew
    t['clk_edge_3_start'] = t['clk_edge_2_end'] + 2 * t_stabilizing - t_clk_slew / 2
    t['clk_edge_3_end'] = t['clk_edge_3_start'] + t_clk_slew

    t['data_edge_1_start'] = ( t['clk_edge_3_start'] + t_clk_slew / 2 ) - t_setup_skew - t_clk_slew / 2
    t['data_edge_1_end'] = t['data_edge_1_start'] + t_data_slew
    t['data_edge_2_start'] = ( t['clk_edge_3_start'] + t_clk_slew / 2 ) + t_hold_skew 
    t['data_edge_2_end'] = t['data_edge_2_start'] + t_data_slew

    t['sim_end'] = t['data_edge_2_end'] + t_stabilizing # wait for the system to stabilize

    # check for invalid timing conditions (all PWL timepoints must be non-decreasing)
    if t['data_edge_1_end'] >= t['data_edge_2_start']:
        print(f'Invalid point setup_skew = {t_setup_skew*1e12:.3g}ps, hold_skew = {t_hold_skew*1e12:.3g}ps: data rise overlaps with data fall')
        return float('nan')
    print(f'Running simulation for setup_skew = {t_setup_skew*1e12:.3g}ps, hold_skew = {t_hold_skew*1e12:.3g}ps')

    # Initialize circuit
    circuit = utils.init_circuit("sequential_setup_hold", cell.netlist, config.models)
    circuit.V('dd', 'vdd', circuit.gnd, vdd) # for input pins
    circuit.V('ss', 'vss', circuit.gnd, vss) # for input pins
    circuit.V('dd_dyn', 'vdd_dyn', circuit.gnd, vdd) # separate voltage sources for VDD / VSS pins of DUT for measuring dynamic power 
    circuit.V('ss_dyn', 'vss_dyn', circuit.gnd, vss) # separate voltage sources for VDD / VSS pins of DUT for measuring dynamic power 
    circuit.V('o_cap', 'vout', 'wout', 0) # 0 volt source in series with c_load is a trick to measure current through the load capacitor.
    circuit.C('c_load', 'wout', circuit.gnd, c_load)

    # Set up clock input
    (v0, v1) = (vdd, vss) if False else (vss, vdd)
    circuit.PieceWiseLinearVoltageSource('clk', 'vclk', circuit.gnd, values=[
        (0, v0),
        (t['clk_edge_1_start'], v0),
        (t['clk_edge_1_end'], v1),
        (t['clk_edge_2_start'], v1),
        (t['clk_edge_2_end'], v0),
        (t['clk_edge_3_start'], v0),
        (t['clk_edge_3_end'], v1),
        (t['sim_end'], v1)
    ])

    # Set up data input node
    (v0, v1) = (vss, vdd) if True else (vdd, vss)
    circuit.PieceWiseLinearVoltageSource('data', 'vdata', circuit.gnd, values=[
        (0, v0),
        (t['data_edge_1_start'], v0),
        (t['data_edge_1_end'], v1),
        (t['data_edge_2_start'], v1),
        (t['data_edge_2_end'], v0),
        (t['sim_end'], v0)
    ])

    # Initialize device under test subcircuit and wire up ports
    connections = []
    for port in cell.ports:
      if port.role == 'clock':
          connections.append('vclk')
      elif port.name == 'D':
          connections.append('vdata')         
      elif port.name == 'Q':
          connections.append('vout')          
      elif port.role == 'primary_power':
          connections.append('vdd')
      elif port.role == 'primary_ground':
          connections.append('vss')
      else:
          connections.append('wfloat0')       # float unrecognized
    circuit.X('dut', cell.name, *connections)

    # Build the simulation
    simulator = PySpice.Simulator.factory(simulator=settings.simulation.backend)
    simulation = simulator.simulation(
        circuit,
        temperature=settings.temperature,
        nominal_temperature=settings.temperature
    )
    simulation.options('nopage', 'nomod', post=1, ingold=2, trtol=1)

    # hardcode the simulation step and time for now, to be reviewed
    simulation.transient(step_time=t_data_slew/16, end_time=t['sim_end'], run=False)
    if settings.debug:
        debug_path = settings.debug_dir / cell.name / __name__.split('.')[-1]
        debug_path.mkdir(parents=True, exist_ok=True)
        with open(debug_path / f'{cell.name}_ts_{t_setup_skew*1e12:.3g}ps_th_{t_hold_skew*1e12:.3g}ps_cl_{c_load*1e15:.3g}fF.spice', 'w') as f:
            f.write(str(simulation))

    # run the simulation
    try:
        analysis = simulator.run(simulation)

    except Exception as e:
        msg = f'Procedure get_c2q failed for cell {cell.name}, setup_skew = {t_setup_skew}, hold_skew = {t_hold_skew}'
        raise ProcedureFailedException(msg) from e

    # Check whether Q latched the D value by looking at vout after the 3rd clock edge
    time = np.array(analysis.time)
    vout = np.array(analysis['vout'])
    vclk = np.array(analysis['vclk'])
    v_half = float(vdd / 2)

    # Find the 50% crossing of the 3rd clock rising edge (RISE=2 in 0-indexed terms)
    clk_crossings = np.where(np.diff(np.sign(vclk - v_half)) > 0)[0]
    if len(clk_crossings) < 2:
        return float('nan')
    t_clk_edge = np.interp(v_half, [vclk[clk_crossings[1]], vclk[clk_crossings[1] + 1]],
                                    [time[clk_crossings[1]], time[clk_crossings[1] + 1]])

    # Check if vout crosses 50% after the clock edge (i.e. Q latched)
    after_clk = time >= t_clk_edge
    vout_after = vout[after_clk]
    time_after = time[after_clk]
    q_crossings = np.where(np.diff(np.sign(vout_after - v_half)) > 0)[0]
    if len(q_crossings) < 1:
        return float('nan')

    # Interpolate the exact 50% crossing time on Q
    t_q_edge = np.interp(v_half, [vout_after[q_crossings[0]], vout_after[q_crossings[0] + 1]],
                                  [time_after[q_crossings[0]], time_after[q_crossings[0] + 1]])

    return t_q_edge - t_clk_edge

def sequential_setup_hold_search(cell, config, settings, variation, path):
    """The goal of this fucntion is to find the minimum setup and hold time of a sequential cell,
    give an input transition and output load.

    Terminology used here :
    - clock-to-q delay = C2Q = c2q
    - setup skew = the amount of D2C set in simulation, usually becomes setup time
    - hold skew = the amount of C2D set in simulation, usually becomes hold time

    The following few terminologies are used in this very important paper : https://ieeexplore.ieee.org/document/4167994
    - minimum hold pair = MHP 
    - minimum setup pair = MSP
    - minimum setup & hold pair = MSHP = the pair of setup and hold time where the sum of the two
                                         is the smallest out of the sum from all other pairs on the same contour   
                                         on the same contour (i.e. same C2Q)
    
    The big picture steps taken here, which does not completely reflect what the paper define is :
    1. Find the 3D C2Q vs setup time (ts) vs hold time (th) surface.
    2. Find a setup skew vs hold skew contour by selecting C2Q based on boundry conditions.
    3. Find one point on the contour (MSHP) for our LIBERTY library

    =======================
    = The steps in detail =
    =======================
    * assumption : smallest setup time always cooresponds to the largest hold time, vice versa
    * terminology : to the rigth means increase in time, to the left means decrease in time

    1. find min setup skew : infinite hold skew, binary search to the right for min setup time
    2. find max hold skew to run the cell : min setup skew, binary search to the left for max hold time 
    3. save pulse width (setup skew + hold skew) from the last run, keep moving the window to the left by 
       a binary search.
       During the binary search, if there is no transition on Q, double the setup skew (which also increase the pulse width).
       Algorithm stops when setup skew has been increased 5 times and there is still no transition on Q. 
       This means we have hit the smallest hold possible, the smallest hold time is hold skew from the second last run.
    4. take minimum min hold skew and increase setup skew to the left until the C2Q curve flattens out. 
       Check that the C2Q curve flattens out by checking the slope of the C2Q curve.
       
    After these few steps, we should have the boundries for 3D C2Q vs setup time (ts) vs hold time (th) surface.
    """
    pass
