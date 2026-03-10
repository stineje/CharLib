from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.characterizer import utils, plots
from charlib.liberty.library import LookupTable

import PySpice
import numpy as np
import math
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
    STEP = 5 @ PySpice.Unit.u_ps # 5 ps initial bound-finding step for binary search
    T_STABILZING = 20 * max(cell_settings.parameters['clock_slews']) * charlib_settings.units.time # 20x worst case clock slew
    # C_LOAD = 4x the data pin's input capacitance from the prior ac_sweep, (fanout of 4)
    # C_LOAD = 4 * cell.liberty.group('pin', data_pin).attributes['capacitance'].value * settings.units.capacitance
    C_LOAD = 0.24 @ PySpice.Unit.u_pF # TODO: remove this line for actual characterization, default to 40 fF
    constants = (TOLERANCE, STEP, T_STABILZING, C_LOAD)

    for variation in cell_settings.variations('data_slews', 'clock_slews'):

        # write logs and results per-variantion
        ds = variation['data_slew'] * charlib_settings.units.time
        cs = variation['clock_slew'] * charlib_settings.units.time
        variation_debug_path = charlib_settings.debug_dir / cell.name / __name__.split('.')[-1] / f'variation_data_slew_{str(ds).replace(' ', '')}_clock_slew_{str(cs).replace(' ', '')}'
        variation_debug_path.mkdir(parents=True, exist_ok=True)

        for path in cell.paths():
            # cell.nonmasking_conditions_for_path filter out the impossible paths
            # ex. non-inverting FF with D, Q, and CLK. it'll never have D_01 -> Q_10
            state_maps = list(cell.nonmasking_conditions_for_path(*path))
            if state_maps == []:
                continue

            yield (find_setup_hold_simple_for_variation, cell, cell_settings, charlib_settings, variation, path, state_maps, constants, variation_debug_path)

def make_log_header(cell_name, ds, cs, path_str, constants):
    """Return a metadata header block common to all log files."""
    TOLERANCE, STEP, T_STABILZING, C_LOAD = constants
    return [
        f"Cell:      {cell_name}",
        f"Variation: data_slew={ds}, clock_slew={cs}",
        f"Path:      {path_str}",
        f"Constants: stabilizing={T_STABILZING}, tolerance={TOLERANCE}, step={STEP}, c_load={C_LOAD}",
        f"",
    ]

def write_log(debug_path, filename, lines):
    """Write a list of lines to a log file. No-ops if debug_path is None."""
    if debug_path is None:
        return
    debug_path.mkdir(parents=True, exist_ok=True)
    with open(debug_path / filename, 'w') as f:
        f.write('\n'.join(lines) + '\n')

def write_step_log(debug_path, step_label, cell_name, ds, cs, path_str, state_str, constants, description, result, phase1_candidates, phase2_candidates):
    """Write a debug log for a find_min_valid step. No-ops if debug_path is None."""
    write_log(debug_path, f'{step_label}_log.txt',
        make_log_header(cell_name, ds, cs, path_str, constants) + [
            f"State:     {state_str}",
            f"",
            f"{description}",
            f"{step_label} final result = {result}",
            f"{step_label}_phase1_candidates = \n" + "\n".join(f"  [{i}] {c}" for i, c in enumerate(phase1_candidates)),
            f"{step_label}_phase2_candidates = \n" + "\n".join(f"  [{i}] lo={lo}, mid={mid}, hi={hi}" for i, (lo, mid, hi) in enumerate(phase2_candidates)),
        ]
    )

def find_setup_hold_simple_for_variation(cell, config, settings, variation, path, state_maps, constants, variation_debug_path=None):
    """Find setup and hold time using an approach from https://ieeexplore.ieee.org/document/4167994, which is exploits
    the interdependence between setup time, hold time. 

    For each (data_slew × clock_slew) variation, the algorithm runs as follows:
      1. Find setup time with hold held at 'infinite'. Binary search finds absolute minimum setup where FF latches at all.
      2. Fix setup = result of step 1, then find hold time. Binary search finds absolute maximum hold where FF latches at all.
      ---- at this point we have absolute min setup and absolute max hold ----
      3. Find hold time with setup held at 'infinite'. Binary search finds absolute minimum hold where FF latches at all.
      4. Fix hold = result of step 3, then find setup time. Binary search finds absolute maximum setup where FF latches at all.
      ---- at this point we have absolute max setup and absolute min hold ----
      5. with the boundaries we obtained, simulate every (setup, hold) combination; use a c2q threshold (20% worse
         than c2q at the relaxed corner) to identify the valid-c2q contour within the full latching space
      6. pick the knee point on the valid-c2q contour as the final setup and hold result for the current variation

    Note: both setup time and hold time may be negative (data can arrive after the
    clock edge / change before the clock edge and the cell still latches).
    """
    TOLERANCE, STEP, T_STABILZING, C_LOAD = constants
    t_unit = settings.units.time.prefixed_unit
    to_t = lambda q: float(q.convert(t_unit).value)

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

        state_debug_path = path_debug_folder = None
        if settings.debug:
            state_folder = '__'.join(f"{k}_{v}" for k, v in state_map.items())
            path_debug_folder = variation_debug_path / path_str
            state_debug_path = path_debug_folder / state_folder

        # Step 0: measure reference c2q at (T_STABILZING, T_STABILZING) — guaranteed relaxed point.
        # Used to gate binary search steps 1–4: points with c2q > ref * 1.2 are treated
        # as invalid (metastable / degenerate operating region).
        step0_path = (state_debug_path / 'step0') if settings.debug else None
        ref_c2q_steps = get_c2q(cell, config, settings, cs, ds,
                                 T_STABILZING, T_STABILZING,
                                 C_LOAD, T_STABILZING, path, state_map, step0_path)
        step_threshold = ref_c2q_steps * 1.2 if not math.isnan(ref_c2q_steps) else math.inf
        ref_c2q_display = float((ref_c2q_steps @ PySpice.Unit.u_s).convert(t_unit).value) if not math.isnan(ref_c2q_steps) else float('nan')
        threshold_display = float((step_threshold @ PySpice.Unit.u_s).convert(t_unit).value) if not math.isinf(step_threshold) else float('inf')
        write_log(step0_path, 'step0_log.txt',
            make_log_header(cell.name, ds, cs, path_str, constants) + [
                f"State:     {state_str}",
                f"",
                f"step0 : measure ref c2q at setup=hold= {T_STABILZING}",
                f"  ref c2q   = {ref_c2q_display:.4g} {t_unit.str_spice()}",
                f"  threshold = {threshold_display:.4g} {t_unit.str_spice()} (ref c2q * 1.2)",
            ]
        )

        def _valid_c2q(c2q):
            """Return c2q if within threshold, else NaN (so find_min_valid treats it as invalid)."""
            return c2q if (not math.isnan(c2q) and c2q < step_threshold) else float('nan')

        # Step 1: setup time with hold fixed at T_STABILZING, this gives min setup
        step1_path = (state_debug_path / 'step1') if settings.debug else None
        step1_setup_result, step1_phase1_candidates, step1_phase2_candidates = utils.find_min_valid(
            lambda s: _valid_c2q(get_c2q(cell, config, settings, cs, ds, s, T_STABILZING, C_LOAD, T_STABILZING, path, state_map, step1_path)),
            start=T_STABILZING, step=STEP, tolerance=TOLERANCE)
        write_step_log(step1_path, 'step1', cell.name, ds, cs, path_str, state_str, constants,
                        f"step1 : find setup given hold= {T_STABILZING}",
                        step1_setup_result, step1_phase1_candidates, step1_phase2_candidates)

        # Step 2: hold time with setup fixed at min_setup, this gives max hold
        step2_path = (state_debug_path / 'step2') if settings.debug else None
        step2_hold_result, step2_phase1_candidates, step2_phase2_candidates = utils.find_min_valid(
            lambda h: _valid_c2q(get_c2q(cell, config, settings, cs, ds, step1_setup_result, h, C_LOAD, T_STABILZING, path, state_map, step2_path)),
            start=T_STABILZING, step=STEP, tolerance=TOLERANCE)
        write_step_log(step2_path, 'step2', cell.name, ds, cs, path_str, state_str, constants,
                        f"step2 : find hold given setup= {step1_setup_result}",
                        step2_hold_result, step2_phase1_candidates, step2_phase2_candidates)

        # Step 3: hold time with setup fixed T_STABILZING, this gives min hold
        step3_path = (state_debug_path / 'step3') if settings.debug else None
        step3_hold_result, step3_phase1_candidates, step3_phase2_candidates = utils.find_min_valid(
            lambda h: _valid_c2q(get_c2q(cell, config, settings, cs, ds, T_STABILZING, h, C_LOAD, T_STABILZING, path, state_map, step3_path)),
            start=T_STABILZING, step=STEP, tolerance=TOLERANCE)
        write_step_log(step3_path, 'step3', cell.name, ds, cs, path_str, state_str, constants,
                        f"step3 : find hold given setup= {T_STABILZING}",
                        step3_hold_result, step3_phase1_candidates, step3_phase2_candidates)

        # Step 4: find setup time with hold fixed at min hold, this gives max setup
        step4_path = (state_debug_path / 'step4') if settings.debug else None
        step4_setup_result, step4_phase1_candidates, step4_phase2_candidates = utils.find_min_valid(
            lambda s: _valid_c2q(get_c2q(cell, config, settings, cs, ds, s, step3_hold_result, C_LOAD, T_STABILZING, path, state_map, step4_path)),
            start=T_STABILZING, step=STEP, tolerance=TOLERANCE)
        write_step_log(step4_path, 'step4', cell.name, ds, cs, path_str, state_str, constants,
                        f"step4 : find setup given hold= {step3_hold_result}",
                        step4_setup_result, step4_phase1_candidates, step4_phase2_candidates)
        
        # Step 5: sweep the setup×hold boundary and plot the latched contour
        step5_debug_path = (state_debug_path / 'step5') if settings.debug else None
        ref_c2q = get_c2q(cell, config, settings, cs, ds,
                          step4_setup_result, step2_hold_result,
                          C_LOAD, T_STABILZING, path, state_map, step5_debug_path)
        c2q_threshold = ref_c2q * 1.2 if not math.isnan(ref_c2q) else math.inf

        # latch_x : 2D numpy array, indexed by hold(first index) and setup(second index), stores a boolean that indicates whether such setup & hold combination meets requirement
        # c2q_x : 2D numpy array, indexed by hold(first index) and setup(second index), stores a number that indicates the c2q time for such setup & hold combination
        # simulated_a : 2D numpy array, indexed by hold(first index) and setup(second index), stores a boolean that indicates whether such setup & hold combination has been simulated 
        (latched_a, c2q_a, simulated_a,
         latched_b, c2q_b, simulated_b,
         setup_vals_s, hold_vals_s) = sweep_2d_space_for_contour(
            lambda s, h: get_c2q(cell, config, settings, cs, ds,
                                 s * settings.units.time, h * settings.units.time,
                                 C_LOAD, T_STABILZING, path, state_map, step5_debug_path),
            setup_min=to_t(step1_setup_result), setup_max=to_t(step4_setup_result),
            hold_min=to_t(step3_hold_result),   hold_max=to_t(step2_hold_result),
            c2q_threshold=c2q_threshold,
        )

        # output some data into the debug folder
        if settings.debug:
            utils.write_c2q_csv(step5_debug_path, settings, c2q_a, c2q_b,
                                setup_vals_s, hold_vals_s, T_STABILZING,
                                ref_c2q_steps, c2q_threshold)

            _base_title = f'{cell.name}  |  {path_str}  |  {state_str}\ndata_slew={ds},  clk_slew={cs}'
            _contour_args = (step1_setup_result, step2_hold_result,
                            step4_setup_result, step3_hold_result,
                            step5_debug_path)

            points_a = [(s_s, h_s, 'green' if latched_a[hi, si] else 'red')
                        for hi, h_s in enumerate(hold_vals_s)
                        for si, s_s in enumerate(setup_vals_s)
                        if simulated_a[hi, si]]
            plots.plot_contour(settings, points_a, *_contour_args,
                            filename='contour_sweep_a_hold_as_outer_loop.png',
                            title=_base_title + '\nSweep A: hold outer, setup inner')

            points_b = [(s_s, h_s, 'green' if latched_b[hi, si] else 'red')
                        for hi, h_s in enumerate(hold_vals_s)
                        for si, s_s in enumerate(setup_vals_s)
                        if simulated_b[hi, si]]
            plots.plot_contour(settings, points_b, *_contour_args,
                            filename='contour_sweep_b_setup_as_outer_loop.png',
                            title=_base_title + '\nSweep B: setup outer, hold inner')

        # Step 6: pick the balanced knee point from the merged contour.
        boundary_pts = extract_2d_contour(latched_a, latched_b, setup_vals_s, hold_vals_s)
        (knee_setup_s, knee_hold_s), knee_is_fallback = utils.find_knee_point(
            boundary_pts,
            chord_p0=(to_t(step1_setup_result), to_t(step2_hold_result)),
            chord_p1=(to_t(step4_setup_result), to_t(step3_hold_result)),
        )
        setup = knee_setup_s * settings.units.time
        hold  = knee_hold_s  * settings.units.time
        knee_point = (knee_setup_s, knee_hold_s)
        merged = latched_a | latched_b
        points_merged = [(s_s, h_s, 'green')
                         for hi, h_s in enumerate(hold_vals_s)
                         for si, s_s in enumerate(setup_vals_s)
                         if merged[hi, si]]
        
        if settings.debug:
            plots.plot_contour(settings, points_merged, *_contour_args,
                               filename='contour.png',
                               title=_base_title + '\n2D setup vs hold contour and knee search result',
                               knee_point=knee_point,
                               knee_is_fallback=knee_is_fallback)

        # store a setup vs hold point per state
        result_per_state[state_str] = (setup, hold, knee_point)

    # find worst-case across all states for current path in current variation
    worst_setup = None
    worst_hold  = None
    worst_setup_state = None
    worst_hold_state  = None

    for state_str, (setup, hold, _) in result_per_state.items():
        if worst_setup is None or setup > worst_setup:
            worst_setup = setup
            worst_setup_state = state_str
        if worst_hold is None or hold > worst_hold:
            worst_hold = hold
            worst_hold_state = state_str

    # write path-level log
    if settings.debug:
        per_state_lines = []
        for state_str, (setup, hold, kp) in result_per_state.items():
            kp_str = f'({float(kp[0]):.4g} {t_unit.str_spice()}, {float(kp[1]):.4g} {t_unit.str_spice()})' if kp else 'fallback (no contour)'
            per_state_lines += [
                f"    state: {state_str}",
                f"        knee point = {kp_str}",
                f"        setup = {setup}",
                f"        hold  = {hold}",
            ]
        write_log(path_debug_folder, 'path_log.txt',
            make_log_header(cell.name, ds, cs, path_str, constants) + [
                f"States derived from this path:",
            ] + [f"    {s}" for s in result_per_state] + [
                f"",
                f"Per-state results:",
            ] + per_state_lines + [
                f"",
                f"Final selection (worst-case across states for current path):",
                f"    setup = {worst_setup}  (from state: {worst_setup_state})",
                f"    hold  = {worst_hold}  (from state: {worst_hold_state})",
            ]
        )

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


def sweep_2d_space_for_contour(probe_fn, setup_min, setup_max, hold_min, hold_max, c2q_threshold=math.inf):
    """Sweep every (setup, hold) combination inside the characterization boundary
    and record whether the flip-flop latches at each point.

    :param probe_fn: callable (setup_float, hold_float) -> c2q_float | NaN.
                     setup and hold are in the caller's display time units.
    :param setup_min: minimum setup value (display units), from step1 result.
    :param setup_max: maximum setup value (display units), from step4 result.
    :param hold_min:  minimum hold value  (display units), from step3 result.
    :param hold_max:  maximum hold value  (display units), from step2 result.
    :param c2q_threshold: c2q values above this are treated as failed latches.

    Returns
    -------
    latched_grid : np.ndarray[bool], shape (n_hold, n_setup)
        True where probe_fn returned a valid delay below c2q_threshold.
    c2q_grid : np.ndarray[float], shape (n_hold, n_setup)
        Raw c2q delay; NaN where the FF did not latch.
    setup_vals : np.ndarray[float]
        Setup-time axis values in display time units.
    hold_vals : np.ndarray[float]
        Hold-time axis values in display time units.
    """
    # Safety: ensure lo ≤ hi on both axes
    if setup_min > setup_max:
        setup_min, setup_max = setup_max, setup_min
    if hold_min > hold_max:
        hold_min, hold_max = hold_max, hold_min

    setup_vals = np.linspace(setup_min, setup_max, 40)
    hold_vals  = np.linspace(hold_min,  hold_max,  40)

    n_setup = len(setup_vals)
    n_hold  = len(hold_vals)

    _cache = {}  # (si, hi) -> c2q; reused by Sweep B to avoid duplicate SPICE jobs

    def _run_cached(si, hi, s_s, h_s):
        key = (si, hi)
        if key in _cache:
            return _cache[key], False  # (c2q, was_simulated)
        c2q = probe_fn(s_s, h_s)
        _cache[key] = c2q
        return c2q, True

    # --- Sweep A: hold outer, setup inner (left→right, break at first success) ---
    c2q_a       = np.full((n_hold, n_setup), np.nan)
    latched_a   = np.zeros((n_hold, n_setup), dtype=bool)
    simulated_a = np.zeros((n_hold, n_setup), dtype=bool)

    for hi, h_s in enumerate(hold_vals):
        for si, s_s in enumerate(setup_vals):
            c2q, ran = _run_cached(si, hi, s_s, h_s)
            c2q_a[hi, si]       = c2q
            simulated_a[hi, si] = ran
            latched_a[hi, si]   = not math.isnan(c2q) and c2q < c2q_threshold
            if latched_a[hi, si]:
                break

    # --- Sweep B: setup outer, hold inner (top→bottom, break at first success) ---
    c2q_b       = np.full((n_hold, n_setup), np.nan)
    latched_b   = np.zeros((n_hold, n_setup), dtype=bool)
    simulated_b = np.zeros((n_hold, n_setup), dtype=bool)

    for si, s_s in enumerate(setup_vals):
        for hi, h_s in enumerate(hold_vals):   # low hold → high hold, break at first success
            c2q, ran = _run_cached(si, hi, s_s, h_s)
            c2q_b[hi, si]       = c2q
            simulated_b[hi, si] = ran
            latched_b[hi, si]   = not math.isnan(c2q) and c2q < c2q_threshold
            if latched_b[hi, si]:
                break

    return (latched_a, c2q_a, simulated_a,
            latched_b, c2q_b, simulated_b,
            setup_vals, hold_vals)

def extract_2d_contour(latched_a, latched_b, setup_vals, hold_vals):
    """Extract the latch boundary as a list of (setup, hold) float pairs.
    The result is the 2D concaved contour we're using to pick the final setup / hold pair

    Sweep A contributes the minimum-setup point per hold row.
    Sweep B contributes the minimum-hold point per setup column.
    Points are de-duplicated by (si, hi) index before returning.
    """
    seen = set()
    pts = []

    # Sweep A: for each hold row, first latching setup column
    for hi in range(len(hold_vals)):
        for si in range(len(setup_vals)):
            if latched_a[hi, si]:
                if (si, hi) not in seen:
                    seen.add((si, hi))
                    pts.append((float(setup_vals[si]), float(hold_vals[hi])))
                break

    # Sweep B: for each setup column, first latching hold row
    for si in range(len(setup_vals)):
        for hi in range(len(hold_vals)):
            if latched_b[hi, si]:
                if (si, hi) not in seen:
                    seen.add((si, hi))
                    pts.append((float(setup_vals[si]), float(hold_vals[hi])))
                break

    return pts

def get_c2q(cell, config, settings, t_clk_slew, t_data_slew, t_setup_skew, t_hold_skew, c_load, t_stabilizing, path, state_map, debug_path=None):
    """Build a SPICE testbench and run a transient simulation to get the clock-to-q delay
    for a given setup skew / hold skew, load capacitance, and stabilizing time."""

    data_pin, data_transition, output_pin, output_transition = path

    if debug_path is not None:
        debug_path.mkdir(parents=True, exist_ok=True)

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
    circuit = utils.init_circuit("sequential_setup_hold", cell.netlist, config.models,
                                    settings.named_nodes, settings.units)
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