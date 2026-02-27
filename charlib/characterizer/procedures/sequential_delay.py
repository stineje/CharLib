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
    """find setup and hold time using the approach described in https://ieeexplore.ieee.org/document/4167994"""

    TOLERANCE = 10 @ PySpice.Unit.u_ps # binary search stops when iternation n - (n-1) < TOLERANCE
    STEP = 5 @ PySpice.Unit.u_ps # 10 ps initial bound-finding step
    T_STABILZING = 20 * max(cell_settings.parameters['clock_slews']) * charlib_settings.units.time # 20x worst case clock slew
    # C_LOAD = 4x the data pin's input capacitance from the prior ac_sweep, (fanout of 4)
    # C_LOAD = 4 * cell.liberty.group('pin', data_pin).attributes['capacitance'].value * settings.units.capacitance
    C_LOAD = 0.004 @ PySpice.Unit.u_pF # TODO: remove this line for actual characterization, default to 40 fF
    constants = (TOLERANCE, STEP, T_STABILZING, C_LOAD)

    for variation in cell_settings.variations('data_slews', 'clock_slews'):

        # write logs and results per-variantion
        ds = variation['data_slew'] * charlib_settings.units.time
        cs = variation['clock_slew'] * charlib_settings.units.time
        variation_debug_path = charlib_settings.debug_dir / cell.name / __name__.split('.')[-1] / f'variation_data_slew_{str(ds).replace(' ', '')}_clock_slew_{str(cs).replace(' ', '')}'
        variation_debug_path.mkdir(parents=True, exist_ok=True)

        variation_log = [
            f"Cell: {cell.name}",
            f"Variation: data_slew={ds}, clock_slew={cs}",
            f"Constants: stabilizing={T_STABILZING}, tolerance={TOLERANCE}, step={STEP}, c_load={C_LOAD}",
        ]
        for path in cell.paths():
            # cell.nonmasking_conditions_for_path filter out the impossible paths
            # ex. non-inverting FF with D, Q, and CLK. it'll never have D_01 -> Q_10
            state_maps = list(cell.nonmasking_conditions_for_path(*path))
            if state_maps == []:
                continue

            yield (find_setup_hold_simple_for_variation, cell, cell_settings, charlib_settings, variation, path, state_maps, constants, variation_debug_path)

        with open(variation_debug_path / f'variation_log.txt', 'w') as f:
            f.write('\n'.join(variation_log))


def find_setup_hold_simple_for_variation(cell, config, settings, variation, path, state_maps, constants, variation_debug_path=None):
    """Find setup and hold time using an approach from https://ieeexplore.ieee.org/document/4167994, which is exploits
    the interdependence between setup time, hold time. 

    For each (data_slew × clock_slew) variation, the algorithm runs as follows:
      1. Find setup time with hold held at 'infinite'. Binary search starts from setup_skew = T_STABILZING.
      2. Fix setup = result of step 1, then find hold time.Binary search starts from hold_skew = T_STABILZING.
      ---- at this point we have min setup and max hold ----
      3. Find hold time with setup held at 'infinite'. Binary search starts from hold_skew = T_STABILZING.
      4. Fix hold = result of step 3, then find setup time.Binary search starts from setup_skew = T_STABILZING.
      ---- at this point we have max setup and min hold ----
      5. with the boundries we obtained, simulate every single setup vs hold combination and get a 3D surface of c2q time
      6. set a c2q threshold (20% worst than c2q obtains from max setup & max hold), and get a 2D contour 
      7. pick the knee point on the contour as the final setup and hold result for the current variation

    Note: both setup time and hold time may be negative (data can arrive after the
    clock edge / change before the clock edge and the cell still latches).
    """
    TOLERANCE, STEP, T_STABILZING, C_LOAD = constants

    ds = variation['data_slew'] * settings.units.time
    cs = variation['clock_slew'] * settings.units.time
    data_pin, data_transition, output_pin, output_transition = path
    path_str = f'{data_pin}_{data_transition}__{output_pin}_{output_transition}'

    result_per_state = {}

    # there could be multiple state maps for a given path
    # ex. in a scan dff with pins D, Q, CLK, SE (scan enable) and SD (scan data)
    # for path D, 01 -> Q, 01, SD can be either 0 or 1, that will affect setup / hold time
    for state_map in state_maps:
        state_str = ', '.join(f"{k}={v}" for k, v in state_map.items())

        # Per-state debug subfolder
        if settings.debug:
            step1_debug_path = step2_debug_path = step3_debug_path = None
            if variation_debug_path is not None:
                state_folder = '__'.join(f"{k}_{v}" for k, v in state_map.items())
                path_debug_folder = variation_debug_path / path_str 
                state_debug_path = path_debug_folder / state_folder
                step1_debug_path = state_debug_path / 'step1'
                step2_debug_path = state_debug_path / 'step2'
                step3_debug_path = state_debug_path / 'step3'
                for p in (step1_debug_path, step2_debug_path, step3_debug_path):
                    p.mkdir(parents=True, exist_ok=True)

        # Step 1: setup time with hold fixed at T_STABILZING
        step1_setup_result, step1_phase1_candidates, step1_phase2_candidates = find_min_valid(
            lambda s: get_c2q(cell, config, settings, cs, ds, s, T_STABILZING, C_LOAD, T_STABILZING, path, state_map, step1_debug_path),
            start=T_STABILZING, step=STEP, tolerance=TOLERANCE)
        
        # write step1 log
        if settings.debug:
            step1_log = [
                f"Cell: {cell.name}",
                f"Variation: data_slew={ds}, clock_slew={cs}",
                f"path_str: {path_str}",
                f"state_str: {state_str}",
                f"step1 : find setup given hold= {T_STABILZING}",
                f"\nstep1 final setup result = {step1_setup_result}",
                f"step1_phase1_candidates = \n{"\n".join(f"  [{i}] {c}" for i, c in enumerate(step1_phase1_candidates))}",
                f"step1_phase2_candidates = \n{"\n".join(f"  [{i}] lo={lo}, mid={mid}, hi={hi}"
                                                for i, (lo, mid, hi) in enumerate(step1_phase2_candidates))}",
            ]
            with open(step1_debug_path / f'step1_log.txt', 'w') as f:
                f.write('\n'.join(step1_log))

        # Step 2: hold time with setup fixed at setup_1
        step2_hold_result, step2_phase1_candidates, step2_phase2_candidates = find_min_valid(
            lambda h: get_c2q(cell, config, settings, cs, ds, step1_setup_result, h, C_LOAD, T_STABILZING, path, state_map, step2_debug_path),
            start=T_STABILZING, step=STEP, tolerance=TOLERANCE)

        # write step2 log
        if settings.debug:
            step2_log = [
                f"Cell: {cell.name}",
                f"Variation: data_slew={ds}, clock_slew={cs}",
                f"path_str: {path_str}",
                f"state_str: {state_str}",
                f"step2 : find hold given setup= {step1_setup_result}",
                f"\nstep2 final hold result = {step2_hold_result}",
                f"step2_phase1_candidates = \n{"\n".join(f"  [{i}] {c}" for i, c in enumerate(step2_phase1_candidates))}",
                f"step2_phase2_candidates = \n{"\n".join(f"  [{i}] lo={lo}, mid={mid}, hi={hi}"
                                                for i, (lo, mid, hi) in enumerate(step2_phase2_candidates))}",
            ]
            with open(step2_debug_path / f'step2_log.txt', 'w') as f:
                f.write('\n'.join(step2_log))

        # Step 3: setup time again with hold fixed at found hold
        step3_setup_result, step3_phase1_candidates, step3_phase2_candidates = find_min_valid(
            lambda s: get_c2q(cell, config, settings, cs, ds, s, step2_hold_result, C_LOAD, T_STABILZING, path, state_map, step3_debug_path),
            start=T_STABILZING, step=STEP, tolerance=TOLERANCE)

        # write step3 log
        if settings.debug:
            step3_log = [
                f"Cell: {cell.name}",
                f"Variation: data_slew={ds}, clock_slew={cs}",
                f"path_str: {path_str}",
                f"state_str: {state_str}",
                f"step3 : find final setup given hold= {step2_hold_result}",
                f"\nstep3 final setup result = {step3_setup_result}",
                f"step3_phase1_candidates = \n{"\n".join(f"  [{i}] {c}" for i, c in enumerate(step3_phase1_candidates))}",
                f"step3_phase2_candidates = \n{"\n".join(f"  [{i}] lo={lo}, mid={mid}, hi={hi}"
                                                for i, (lo, mid, hi) in enumerate(step3_phase2_candidates))}",
            ]
            with open(step3_debug_path / f'step3_log.txt', 'w') as f:
                f.write('\n'.join(step3_log))

        # setup hold result selection
        setup = step3_setup_result
        hold  = step2_hold_result

        # store results per state and per path for later analysis
        result_per_state[state_str] = (setup, hold)

    # find worst-case across all states for this variation + path
    worst_setup = None
    worst_hold  = None
    worst_setup_state = None
    worst_hold_state  = None

    for state_str, (setup, hold) in result_per_state.items():
        if worst_setup is None or setup > worst_setup:
            worst_setup = setup
            worst_setup_state = state_str
        if worst_hold is None or hold > worst_hold:
            worst_hold = hold
            worst_hold_state = state_str

    if settings.debug:
        path_log = [
            f"Cell: {cell.name}",
            f"Variation: data_slew={ds}, clock_slew={cs}",
            f"",
            f"path_str: {path_str}",
            f"Worst-case setup time = {worst_setup} in state {worst_setup_state}",
            f"Worst-case hold time = {worst_hold} in state {worst_hold_state}",
        ]
        tree_lines = ['', 'result_per_state:']
        for state_str, (setup, hold) in result_per_state.items():
            tree_lines.append(f'    state: {state_str}')
            tree_lines.append(f'        setup = {setup}')
            tree_lines.append(f'        hold  = {hold}')
        path_log.extend(tree_lines)
        with open(path_debug_folder / f'path_log.txt', 'w') as f:
             f.write('\n'.join(path_log))

    # Build liberty output
    result = cell.liberty
    clock_pin = cell.clock
    n_ds = len(config.parameters['data_slews'])
    n_cs  = len(config.parameters['clock_slews'])
    lut_template_size = f'{len(config.parameters["clock_slews"])}x{len(config.parameters["data_slews"])}'

    # Setup timing group
    result.group('pin', data_pin).add_group('timing', "/* setup */")
    stg = result.group('pin', data_pin).group('timing', "/* setup */")
    stg.add_attribute('related_pin', clock_pin.name)
    stg.add_attribute('timing_type', 'setup_falling' if clock_pin.is_inverted() else 'setup_rising')

    # Hold timing group
    result.group('pin', data_pin).add_group('timing', "/* hold */")
    htg = result.group('pin', data_pin).group('timing', "/* hold */")
    htg.add_attribute('related_pin', clock_pin.name)
    htg.add_attribute('timing_type', 'hold_falling' if clock_pin.is_inverted() else 'hold_rising')

    # add lut to timing group
    # rise_constraint when D rises (01), fall_constraint when D falls (10)
    cname = 'rise_constraint' if data_transition == '01' else 'fall_constraint'

    setup_lut = LookupTable(cname, f'setup_template_{n_cs}x{n_ds}',
                            related_pin_transition=[cs.convert(settings.units.time.prefixed_unit).value],
                            constraint_pin_transition=[ds.convert(settings.units.time.prefixed_unit).value])
    setup_lut.values[0, 0] = worst_setup.convert(settings.units.time.prefixed_unit).value
    stg.add_group(setup_lut)

    hold_lut = LookupTable(cname, f'hold_template_{n_cs}x{n_ds}',
                           related_pin_transition=[cs.convert(settings.units.time.prefixed_unit).value],
                           constraint_pin_transition=[ds.convert(settings.units.time.prefixed_unit).value])
    hold_lut.values[0, 0] = worst_hold.convert(settings.units.time.prefixed_unit).value
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

    # these two lists keeps track of all the setup / hold time sent for experiment
    phase1_candidates = []
    phase2_candidates = [] # this is an array of tuples(3 items, binary search bounds for each step)

    # Phase 1 — expand downward from start to find an lower bound (first failed transition from the ff).
    hi = start
    lo = None
    for exp in range(max_exp):
        # this candidate variable can be setup or hold time
        # in phase one every step increase by power of 2
        candidate = start - step * (2 ** exp)
        phase1_candidates.append(candidate)
        result = probe_fn(candidate)
        if math.isnan(result):
            lo = candidate
            break
        hi = candidate  # tighter valid lower bound

    if lo is None:
        return hi  # never found invalid; hi is the lowest valid point tried

    # Phase 2 — binary search between lo (NaN) and hi (valid)
    # Continue until the interval is within tolerance AND the last probe was valid (non-NaN)
    while (hi - lo) > tolerance:
        mid = (lo + hi) / 2
        phase2_candidates.append((lo, mid, hi))
        if math.isnan(probe_fn(mid)):
            lo = mid
        else:
            hi = mid

    # return hi as the final result because such result will be used in subsquent steps
    # in other words, the setup time returned here must be able to successfully latch the ff, otherwise in step 2
    # no matter how big the hold time is the start condition for the ff to latch might not be statisfied
    return hi, phase1_candidates, phase2_candidates

def get_c2q(cell, config, settings, t_clk_slew, t_data_slew, t_setup_skew, t_hold_skew, c_load, t_stabilizing, path, state_map, debug_path=None):
    """Build a SPICE testbench and run a transient simulation to get the clock-to-q delay
    for a given setup skew / hold skew, load capacitance, and stabilizing time."""

    data_pin, data_transition, output_pin, output_transition = path

    # Set up parameters
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # building waveform for data
    t = {}
    t['clk_edge_1_start'] = t_stabilizing
    t['clk_edge_1_end'] = t['clk_edge_1_start'] + t_clk_slew
    t['clk_edge_2_start'] = t['clk_edge_1_end'] + t_stabilizing
    t['clk_edge_2_end'] = t['clk_edge_2_start'] + t_clk_slew
    t['clk_edge_3_start'] = t['clk_edge_2_end'] + 2 * t_stabilizing
    t['clk_edge_3_end'] = t['clk_edge_3_start'] + t_clk_slew

    t['data_edge_1_start'] = (t['clk_edge_3_start'] + t_clk_slew/2) - t_setup_skew - t_data_slew/2 # 50% clk edge to 50% data edge
    t['data_edge_1_end'] = t['data_edge_1_start'] + t_data_slew
    t['data_edge_2_start'] = (t['clk_edge_3_start'] + t_clk_slew/2) + t_hold_skew - t_data_slew/2 # 50% clk edge to 50% data edge
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
    (v0, v1) = (vdd, vss) if cell.clock.is_inverted() else (vss, vdd)
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
    (v0, v1) = (vss, vdd) if data_transition == '01' else (vdd, vss)
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
      elif port.name == data_pin:
          connections.append('vdata')
      elif port.name == output_pin:
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
    simulation.transient(step_time=min(t_data_slew, t_clk_slew)/4, end_time=t['sim_end'], run=False)
    if settings.debug:
        with open(debug_path / f'{cell.name}_ts_{str(t_setup_skew).replace(" ", "")}_th_{str(t_hold_skew).replace(" ", "")}_cl_{str(c_load).replace(" ", "")}.spice', 'w') as f:
            f.write(str(simulation))

    # run the simulation
    try:
        analysis = simulator.run(simulation)

    except Exception as e:
        if settings.debug:
            with open(debug_path / f'{cell.name}_ts_{str(t_setup_skew).replace(" ", "")}_th_{str(t_hold_skew).replace(" ", "")}_cl_{str(c_load).replace(" ", "")}_failure.spice', 'w') as f:
                f.write(str(simulation))
        msg = f'Procedure get_c2q failed for cell {cell.name}, data_slew = {t_data_slew}, clk_slew = {t_clk_slew}, setup_skew = {t_setup_skew}, hold_skew = {t_hold_skew}'
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