from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.characterizer import utils
from charlib.liberty.library import LookupTable

import PySpice
import numpy as np
import csv
import math
import matplotlib.pyplot as plt
from collections import defaultdict

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
def sequential_setup_hold_simple(cell, cell_settings, charlib_settings):
    """Find setup and hold time using an iterative 3-step binary search.

    For each (data_slew × clock_slew) variation, the algorithm runs as follows:
      1. Find minimum setup time with hold held at 'infinite' (data never de-asserts
         during the simulation window).  Binary search starts from setup_skew = 0.
      2. Fix setup = result of step 1, then find minimum hold time.
         Binary search starts from hold_skew = stabilizing time.
      3. Fix hold = result of step 2, then find minimum setup time again.
         Binary search starts from setup_time found in step 1.

    Results from steps 2 and 3 are the final hold and setup times.  The worst-case
    (largest) setup and hold across all paths and nonmasking conditions is used for
    the liberty output.

    Note: both setup time and hold time may be negative (data can arrive after the
    clock edge / change before the clock edge and the cell still latches).
    """
    for variation in cell_settings.variations('data_slews', 'clock_slews'):
        yield (find_setup_hold_simple_for_variation, cell, cell_settings, charlib_settings, variation)

def find_setup_hold_simple_for_variation(cell, config, settings, variation):
    """Worker: find worst-case setup & hold across all paths for one slew variation."""
    clock_pin = cell.clock
    if clock_pin is None:
        raise ProcedureFailedException(
            f"Cell {cell.name} has no clock pin; cannot measure setup/hold time")

    # binary search stops when iternation n - (n-1) < TOLERANCE
    TOLERANCE   = 1e-12   

    # 10 ps initial bound-finding step
    INIT_STEP   = 10e-12  

    ds = variation['data_slew']
    cs = variation['clock_slew']
    # t_stabilizing is 10x clock slew in seconds. It serves two purposes:
    #   1. Passed to get_c2q to set the waveform padding time.
    #   2. Used as the guaranteed-valid starting point for all searches (setup and hold
    #      times can be negative, so we search downward from a known-valid value).
    t_stabilizing = 10 * (cs * settings.units.time).value
    log_lines = [
        f"Cell:      {cell.name}",
        f"Variation: data_slew={ds}, clock_slew={cs}  (in configured time unit)",
        f"Constants: stabilizing=10x clk_slew ({t_stabilizing:.3e} s), tolerance={TOLERANCE:.3e} s",
        "",
    ]

    # worst[(data_pin, data_transition)] = {'setup': float_s, 'hold': float_s}
    worst = {}

    for path in cell.paths():

        data_pin, data_transition, output_pin, output_transition = path

        # filter out the impossible paths
        # ex. non-inverting FF with D, Q, and CLK. it'll never have D_01 -> Q_10
        state_maps = list(cell.nonmasking_conditions_for_path(*path))
        if not state_maps:
            continue

        # c_load = 4x the data pin's input capacitance from the prior ac_sweep, (fanout of 4)
        # c_load = 4 * cell.liberty.group('pin', data_pin).attributes['capacitance'].value * settings.units.capacitance
        c_load = 40e-12 # TODO: remove this line for actual characterization, default to 40 pF

        for state_map in state_maps:
            state_str = ', '.join(f"{k}={v}" for k, v in state_map.items())
            path_str  = (f"{data_pin}_{data_transition}_to_{output_pin}_{output_transition}_")

            log_lines.append(f"\nPath: {path_str} State: [{state_str}]")

            # Step 1: setup time with hold fixed at t_stabilizing 
            log_lines.append(
                f"  Step 1: hold={t_stabilizing:.3e} s, "
                f"setup search starts at {t_stabilizing:.3e} s")
            setup_1 = find_min_valid(
                lambda s: get_c2q(cell, config, settings, cs, ds, s, t_stabilizing, c_load, t_stabilizing, state_map),
                start=t_stabilizing, step=INIT_STEP, tolerance=TOLERANCE)
            log_lines.append(f"  Step 1 result: setup_1 = {setup_1:.3e} s")

            if math.isnan(setup_1):
                log_lines.append(f"  -> Step 1 failed (no valid setup found), skipping state {state_str}")
                continue

            # Step 2: hold time with setup fixed at setup_1 
            log_lines.append(
                f"  Step 2: setup={setup_1:.3e} s, hold search starts at {t_stabilizing:.3e} s")
            hold = find_min_valid(
                lambda h: get_c2q(cell, config, settings, cs, ds, setup_1, h, c_load, t_stabilizing, state_map),
                start=t_stabilizing, step=INIT_STEP, tolerance=TOLERANCE)
            log_lines.append(f"  Step 2 result: hold = {hold:.3e} s")

            if math.isnan(hold):
                log_lines.append(f"  -> Step 2 failed (no valid hold found), skipping state {state_str}\n")
                continue

            # Step 3: setup time again with hold fixed at found hold 
            log_lines.append(
                f"  Step 3: hold={hold:.3e} s, "
                f"setup search starts at {t_stabilizing:.3e} s")
            setup = find_min_valid(
                lambda s: get_c2q(cell, config, settings, cs, ds, s, hold, c_load, t_stabilizing, state_map),
                start=t_stabilizing, step=INIT_STEP, tolerance=TOLERANCE)
            log_lines.append(f"  Step 3 result: setup = {setup:.3e} s")

            if math.isnan(setup):
                log_lines.append(
                    f"  -> Step 3 failed for state {state_str}, keeping setup_1={setup_1:.3e} s")
                setup = setup_1

            log_lines.append(
                f"  => state {state_str} final: setup={setup:.3e} s, hold={hold:.3e} s\n")

            # Track worst case per (data_pin, data_transition)
            key = (data_pin, data_transition)
            if key not in worst:
                worst[key] = {'setup': setup, 'hold': hold}
            else:
                worst[key]['setup'] = max(worst[key]['setup'], setup)
                worst[key]['hold']  = max(worst[key]['hold'],  hold)

    # Write log 
    log_path = settings.debug_dir / cell.name / __name__.split('.')[-1]
    log_path.mkdir(parents=True, exist_ok=True)
    with open(log_path / f'setup_hold_simple_ds{ds}_cs{cs}.log', 'w') as f:
        f.write('\n'.join(log_lines))

    # Build liberty output
    result = cell.liberty
    if not worst:
        return result

    clock_name = clock_pin.name
    n_data = len(config.parameters['data_slews'])
    n_clk  = len(config.parameters['clock_slews'])
    template_name = f'constraint_template_{n_data}x{n_clk}'

    # variation slew values are already in the library's configured time unit
    data_slew_lib = ds
    clk_slew_lib  = cs

    by_pin = defaultdict(dict)
    for (data_pin, data_transition), vals in worst.items():
        by_pin[data_pin][data_transition] = vals

    for data_pin, transitions in by_pin.items():
        setup_tid = f'/* {clock_name}_setup */'
        hold_tid  = f'/* {clock_name}_hold */'

        # Setup timing group
        result.group('pin', data_pin).add_group('timing', setup_tid)
        stg = result.group('pin', data_pin).group('timing', setup_tid)
        stg.add_attribute('related_pin', clock_name)
        stg.add_attribute('timing_type', 'setup_falling' if clock_pin.is_inverted() else 'setup_rising')

        # Hold timing group
        result.group('pin', data_pin).add_group('timing', hold_tid)
        htg = result.group('pin', data_pin).group('timing', hold_tid)
        htg.add_attribute('related_pin', clock_name)
        htg.add_attribute('timing_type', 'hold_falling' if clock_pin.is_inverted() else 'hold_rising')

        for data_transition, vals in transitions.items():
            # rise_constraint when D rises (01), fall_constraint when D falls (10)
            cname = 'rise_constraint' if data_transition == '01' else 'fall_constraint'

            setup_lut = LookupTable(cname, template_name,
                                    input_net_transition=[data_slew_lib],
                                    related_pin_transition=[clk_slew_lib])
            setup_lut.values[0, 0] = utils.to_lib_time(vals['setup'], settings)
            stg.add_group(setup_lut)

            hold_lut = LookupTable(cname, template_name,
                                   input_net_transition=[data_slew_lib],
                                   related_pin_transition=[clk_slew_lib])
            hold_lut.values[0, 0] = utils.to_lib_time(vals['hold'],  settings)
            htg.add_group(hold_lut)

    return result


def find_min_valid(probe_fn, start, step, tolerance, max_exp=1000):
    """Find the minimum x such that probe_fn(x) is not NaN. 
    When flipflop fails to latch the correct value, get_c2q returns NaN.

    Setup and hold times may be negative, so start must be a guaranteed-valid point
    (large enough that the cell always latches). The search expands downward from
    start to bracket the threshold, then binary searches upward to the minimum.

    :param probe_fn:  A callable (float) -> float | NaN.
    :param start:     A guaranteed-valid starting point (probe_fn(start) is not NaN).
    :param step:      Initial step size for downward expansion.
    :param tolerance: Convergence threshold; binary search stops when hi-lo < tolerance.
    :param max_exp:   Maximum number of exponential expansions before giving up.
    :returns:         Minimum valid x, or float('nan') if no invalid region is found below start.
    """
    # Phase 1 — expand downward from start to find an lower bound (first failed transition from the ff).
    hi = start
    lo = None
    for exp in range(max_exp):
        # this candidate variable can be setup or hold time
        # in phase one every step increase by power of 2
        candidate = start - step * (2 ** exp)
        if math.isnan(probe_fn(candidate)):
            lo = candidate
            break
        hi = candidate  # tighter valid lower bound

    if lo is None:
        return hi  # never found invalid; hi is the lowest valid point tried

    # Phase 2 — binary search between lo (NaN) and hi (valid)
    while (hi - lo) > tolerance:
        mid = (lo + hi) / 2
        if math.isnan(probe_fn(mid)):
            lo = mid
        else:
            hi = mid

    return hi

@register
def sequential_setup_hold_complex(cell, cell_settings, charlib_settings):
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

    setup_skews = np.arange(t_setup_skew_range[0], t_setup_skew_range[1], t_setup_skew_step)
    hold_skews = np.arange(t_hold_skew_range[0], t_hold_skew_range[1], t_hold_skew_step)

    t_stabilizing = 10 * (variation['clock_slew'] * settings.units.time).value
    for state_map in cell.nonmasking_conditions_for_path(*path):
        c2q_values = []
        for t_setup_skew in setup_skews:
            c2q_hold_skew_values = []
            for t_hold_skew in hold_skews:
                t_c2q = get_c2q(cell, config, settings, variation['clock_slew'], variation['data_slew'], t_setup_skew, t_hold_skew, 40e-15, t_stabilizing, state_map)
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

def get_c2q(cell, config, settings, clk_slew, data_slew, t_setup_skew, t_hold_skew, c_load, t_stabilizing, state_map):
    """Build a SPICE testbench and run a transient simulation to get the clock-to-q delay
    for a given setup skew / hold skew, load capacitance, and stabilizing time."""

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
    t['sim_end'] = t['data_edge_2_end'] + t_stabilizing

    # check for invalid timing conditions (all PWL timepoints must be non-decreasing)
    if t['data_edge_1_end'] >= t['data_edge_2_start']:
        return float('nan')

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
    (v0, v1) = (vss, vdd) if state_map['D'] == '01' else (vdd, vss)
    circuit.PieceWiseLinearVoltageSource('data', 'vdata', circuit.gnd, values=[
        (0, v0),
        (t['data_edge_1_start'], v0),
        (t['data_edge_1_end'], v1),
        (t['data_edge_2_start'], v1),
        (t['data_edge_2_end'], v0),
        (t['sim_end'], v0),
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
    if state_map['Q'] == '01':
        q_crossings = np.where(np.diff(np.sign(vout_after - v_half)) > 0)[0]
    else:
        q_crossings = np.where(np.diff(np.sign(vout_after - v_half)) < 0)[0]
    if len(q_crossings) < 1:
        return float('nan')

    # Interpolate the exact 50% crossing time on Q
    idx = q_crossings[0]
    if state_map['Q'] == '01':
        t_q_edge = np.interp(v_half, [vout_after[idx], vout_after[idx + 1]],
                                      [time_after[idx], time_after[idx + 1]])
    else:
        t_q_edge = np.interp(v_half, [vout_after[idx + 1], vout_after[idx]],
                                      [time_after[idx + 1], time_after[idx]])

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
