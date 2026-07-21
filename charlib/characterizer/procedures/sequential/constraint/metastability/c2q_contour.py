import PySpice
import numpy as np
import math

from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.characterizer import utils, plots
from charlib.liberty import liberty
from charlib.liberty.library import LookupTable

@register(
    'data_slews',
    'clock_slews',
    'metastability_constraint_search_tolerance',
    'metastability_constraint_search_timestep',
    'metastability_constraint_load',
    'metastability_constraint_sweep_samples'
)
def measure_setup_hold_from_contour(cell, config, settings):
    """find setup and hold time using the approach described in https://ieeexplore.ieee.org/document/4167994"""
    for variation in config.variations(
            'data_slews',
            'clock_slews',
            'metastability_constraint_search_tolerance',
            'metastability_constraint_search_timestep',
            'metastability_constraint_load',
            'metastability_constraint_sweep_samples'):
        for path in cell.paths():
            # cell.nonmasking_conditions_for_path filter out the impossible paths
            # ex. non-inverting FF with D, Q, and CLK. it'll never have D_01 -> Q_10
            state_maps = list(cell.nonmasking_conditions_for_path(*path))
            if not state_maps:
                continue
            yield (find_setup_hold_for_path, cell, config, settings, variation, path, state_maps)

def make_log_header(cell_name, ds, cs, path_str, constants):
    """Return a metadata header block common to all log files."""
    TOLERANCE, STEP, C_LOAD, N_SWEEP_SAMPLES = constants
    return [
        f"Cell:      {cell_name}",
        f"Variation: data_slew={ds}, clock_slew={cs}",
        f"Path:      {path_str}",
        f"Constants: tolerance={TOLERANCE}, step={STEP}, c_load={C_LOAD}, n_sweep_samples={N_SWEEP_SAMPLES}",
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

def find_setup_hold_for_path(cell, config, settings, variation, path, state_maps):
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
    TOLERANCE = variation['metastability_constraint_search_tolerance'] * settings.units.time
    STEP = variation['metastability_constraint_search_timestep'] * settings.units.time
    C_LOAD = variation['metastability_constraint_load'] * settings.units.capacitance
    N_SWEEP_SAMPLES = variation['metastability_constraint_sweep_samples']
    constants = (TOLERANCE, STEP, C_LOAD, N_SWEEP_SAMPLES)

    ds = variation['data_slews'] * settings.units.time
    cs = variation['clock_slews'] * settings.units.time
    variation_debug_path = settings.debug_dir / cell.name / __name__.split('.')[-1] / f'variation_data_slew_{str(ds).replace(' ', '')}_clock_slew_{str(cs).replace(' ', '')}'
    t_unit = settings.units.time.prefixed_unit
    to_t = lambda q: float(q.convert(t_unit).value)

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

        # Step -1: measure stabilizing time to minimize total runtime
        k = 2 # FIXME: safety factor k should be configurable
        t_stabilizing = get_t_stabilizing(cell, config, settings, path, state_map, k=k,
                                          clock_slew_rate=cs,
                                          data_slew_rate=ds, capacitive_load=C_LOAD,
                                          debug_dir=state_debug_path)

        step_c2q = lambda t_s, t_h, debug_dir: get_c2q(cell, config, settings, path, state_map,
                                                       clock_slew_rate=cs, data_slew_rate=ds,
                                                       setup_skew=t_s, hold_skew=t_h,
                                                       stabilizing_time=t_stabilizing,
                                                       capacitive_load=C_LOAD, debug_dir=debug_dir)

        # Step 0: measure reference c2q at (t_stabilizing, t_stabilizing) — relaxed point.
        # Used to gate binary search steps 1–4: points with c2q > ref * 1.2 are treated
        # as invalid (metastable / degenerate operating region).
        step0_path = (state_debug_path / 'step0') if settings.debug else None
        ref_c2q_steps = step_c2q(t_stabilizing, t_stabilizing, step0_path)
        step_threshold = ref_c2q_steps * 1.2 if not math.isnan(ref_c2q_steps) else math.inf
        ref_c2q_display = to_t(ref_c2q_steps @ PySpice.Unit.u_s) if not math.isnan(ref_c2q_steps) else float('nan')
        threshold_display = to_t(step_threshold @ PySpice.Unit.u_s) if not math.isinf(step_threshold) else float('inf')
        write_log(step0_path, 'step0_log.txt',
            make_log_header(cell.name, ds, cs, path_str, constants) + [
                f"State:     {state_str}",
                f"",
                f"step0 : measure ref c2q at setup=hold= {t_stabilizing}",
                f"  ref c2q   = {ref_c2q_display:.4g} {t_unit.str_spice()}",
                f"  threshold = {threshold_display:.4g} {t_unit.str_spice()} (ref c2q * 1.2)",
            ]
        )

        # Return c2q if within threshold, else NaN (so find_min_valid treats it as invalid).
        _valid_c2q = lambda c2q: c2q if (not math.isnan(c2q) and c2q < step_threshold) else float('nan')

        # Step 1: setup time with hold fixed at t_stabilizing, this gives min setup
        step1_path = (state_debug_path / 'step1') if settings.debug else None
        step1_setup_result, step1_phase1_candidates, step1_phase2_candidates = utils.find_min_valid(
            lambda s: _valid_c2q(step_c2q(s, t_stabilizing, step1_path)),
            start=t_stabilizing, step=STEP, tolerance=TOLERANCE)
        write_step_log(step1_path, 'step1', cell.name, ds, cs, path_str, state_str, constants,
                        f"step1 : find setup given hold= {t_stabilizing}",
                        step1_setup_result, step1_phase1_candidates, step1_phase2_candidates)

        # Step 2: hold time with setup fixed at min_setup, this gives max hold
        step2_path = (state_debug_path / 'step2') if settings.debug else None
        step2_hold_result, step2_phase1_candidates, step2_phase2_candidates = utils.find_min_valid(
            lambda h: _valid_c2q(step_c2q(step1_setup_result, h, step2_path)),
            start=t_stabilizing, step=STEP, tolerance=TOLERANCE)
        write_step_log(step2_path, 'step2', cell.name, ds, cs, path_str, state_str, constants,
                        f"step2 : find hold given setup= {step1_setup_result}",
                        step2_hold_result, step2_phase1_candidates, step2_phase2_candidates)

        # Step 3: hold time with setup fixed t_stabilizing, this gives min hold
        step3_path = (state_debug_path / 'step3') if settings.debug else None
        step3_hold_result, step3_phase1_candidates, step3_phase2_candidates = utils.find_min_valid(
            lambda h: _valid_c2q(step_c2q(t_stabilizing, h, step3_path)),
            start=t_stabilizing, step=STEP, tolerance=TOLERANCE)
        write_step_log(step3_path, 'step3', cell.name, ds, cs, path_str, state_str, constants,
                        f"step3 : find hold given setup= {t_stabilizing}",
                        step3_hold_result, step3_phase1_candidates, step3_phase2_candidates)

        # Step 4: find setup time with hold fixed at min hold, this gives max setup
        step4_path = (state_debug_path / 'step4') if settings.debug else None
        step4_setup_result, step4_phase1_candidates, step4_phase2_candidates = utils.find_min_valid(
            lambda s: _valid_c2q(step_c2q(s, step3_hold_result, step4_path)),
            start=t_stabilizing, step=STEP, tolerance=TOLERANCE)
        write_step_log(step4_path, 'step4', cell.name, ds, cs, path_str, state_str, constants,
                        f"step4 : find setup given hold= {step3_hold_result}",
                        step4_setup_result, step4_phase1_candidates, step4_phase2_candidates)

        # Step 5: sweep the setup×hold boundary and plot the latched contour
        step5_debug_path = (state_debug_path / 'step5') if settings.debug else None
        ref_c2q = step_c2q(step4_setup_result, step2_hold_result, step5_debug_path)
        c2q_threshold = ref_c2q * 1.2 if not math.isnan(ref_c2q) else math.inf

        # latch_x : 2D numpy array, indexed by hold(first index) and setup(second index), stores a boolean that indicates whether such setup & hold combination meets requirement
        # c2q_x : 2D numpy array, indexed by hold(first index) and setup(second index), stores a number that indicates the c2q time for such setup & hold combination
        # simulated_a : 2D numpy array, indexed by hold(first index) and setup(second index), stores a boolean that indicates whether such setup & hold combination has been simulated
        (latched_a, c2q_a, simulated_a,
         latched_b, c2q_b, simulated_b,
         setup_vals_s, hold_vals_s) = sweep_2d_space_for_contour(
            lambda s, h: step_c2q(s * settings.units.time, h * settings.units.time, step5_debug_path),
            setup_min=to_t(step1_setup_result), setup_max=to_t(step4_setup_result),
            hold_min=to_t(step3_hold_result),   hold_max=to_t(step2_hold_result),
            c2q_threshold=c2q_threshold,
            n_samples=N_SWEEP_SAMPLES,
        )

        # output some data into the debug folder
        if settings.debug:
            utils.write_c2q_csv(step5_debug_path, settings, c2q_a, c2q_b,
                                setup_vals_s, hold_vals_s, t_stabilizing,
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

        # If this is a dry-run, we can't proceed past this point because the next step relies on
        # previously measured data
        if settings.dry_run:
            # TODO: Display a message if not settings.quiet
            result_per_state[state_str] = (-1 @ PySpice.Unit.u_s, -1 @ PySpice.Unit.u_s, None)
            continue

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
    lut_size = f'{len(config.parameters["clock_slews"])}x{len(config.parameters["data_slews"])}'
    constraint_name = 'rise_constraint' if data_transition == '01' else 'fall_constraint'

    # Setup timing group
    stg = liberty.Group('timing')
    stg.add_attribute('related_pin', cell.clock.name)
    stg.add_attribute('timing_type', 'setup_falling' if cell.clock.is_inverted() else 'setup_rising')
    setup_lut = LookupTable(constraint_name, f'setup_template_{lut_size}',
                            related_pin_transition=[cs.convert(settings.units.time.prefixed_unit).value],
                            constrained_pin_transition=[ds.convert(settings.units.time.prefixed_unit).value])
    setup_lut.values[0, 0] = worst_setup.convert(settings.units.time.prefixed_unit).value
    stg.add_group(setup_lut)
    result.group('pin', data_pin).add_group(stg)

    # Hold timing group
    htg = liberty.Group('timing')
    htg.add_attribute('related_pin', cell.clock.name)
    htg.add_attribute('timing_type', 'hold_falling' if cell.clock.is_inverted() else 'hold_rising')
    hold_lut = LookupTable(constraint_name, f'hold_template_{lut_size}',
                           related_pin_transition=[cs.convert(settings.units.time.prefixed_unit).value],
                           constrained_pin_transition=[ds.convert(settings.units.time.prefixed_unit).value])
    hold_lut.values[0, 0] = worst_hold.convert(settings.units.time.prefixed_unit).value
    htg.add_group(hold_lut)
    result.group('pin', data_pin).add_group(htg)

    return result


def sweep_2d_space_for_contour(probe_fn, setup_min, setup_max, hold_min, hold_max, c2q_threshold=math.inf, n_samples=40):
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

    setup_vals = np.linspace(setup_min, setup_max, n_samples)
    hold_vals  = np.linspace(hold_min,  hold_max,  n_samples)

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

def sim_latch(cell, config, settings, path, state_map, capacitive_load=None,
              clock_slew_rate=None, data_slew_rate=None, setup_skew=None, hold_skew=None,
              stabilizing_time=None, circuit_title='sim_latch', debug_dir=None
    ):
    """Build a SPICE test bench and run transient simulation. Return an analysis object."""

    # Set up parameters, using reasonable defaults where possible
    data_pin, data_transition, output_pin, output_transition = path
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage
    th_low = settings.logic_thresholds.low
    th_high = settings.logic_thresholds.high
    th_rise = settings.logic_thresholds.rising
    th_fall = settings.logic_thresholds.falling
    t_clk_slew = clock_slew_rate if clock_slew_rate else \
                 max(config.parameters['clock_slews']) * settings.units.time
    t_data_slew = data_slew_rate if data_slew_rate else \
                  max(config.parameters['data_slews']) * settings.units.time
    t_setup = setup_skew if setup_skew else \
              10*max(config.parameters['data_slews']) * settings.units.time
    t_hold = hold_skew if hold_skew else \
             10*max(config.parameters['data_slews']) * settings.units.time
    t_stabilizing = stabilizing_time if stabilizing_time else \
                    20*max([t_clk_slew, t_data_slew, t_setup, t_hold])
    c_load = capacitive_load if capacitive_load else \
             max(config.parameters['loads']) * settings.units.capacitance

    if t_setup + t_hold <= 0:
        raise ValueError(f'setup_skew ({t_setup}) + hold_skew ({t_hold}) < 0!')

    # Build clock waveform (lockdown pulse, stabilizing, clock activation)
    clk_is_rising = state_map[cell.clock.name] == '1'
    (v0, v1) = (vss, vdd) if clk_is_rising else (vdd, vss)
    clk_pwl = utils.slew_pwl(v0, v1, t_clk_slew, t_stabilizing, th_low, th_high)
    clk_pwl += utils.slew_pwl(v1, v0, t_clk_slew, t_stabilizing, th_low, th_high, t_start=clk_pwl[-1][0])[1:]
    clk_pwl += utils.slew_pwl(v0, v1, t_clk_slew, 2*t_stabilizing, th_low, th_high, t_start=clk_pwl[-1][0])[1:]

    # Find the precise time that the clock activation (rise/fall) threshold is reached
    th_clk_active = th_rise if clk_is_rising else th_fall
    t_clk_active = clk_pwl[-2][0] + (clk_pwl[-1][0] - clk_pwl[-2][0])*th_clk_active

    # Based on the time that the clock activates, find the time we want the data to start slewing
    # Data should activate t_setup before the clock activates, plus a bit more to account for
    # the time data takes to slew.
    t_data_full_slew = t_data_slew / (th_high - th_low)
    data_is_rising = data_transition == '01'
    *_, data_port = cell.filter_pins(name=data_pin)
    if data_port.trigger: # edge triggered
        (th_data_start, th_data_end) = (th_rise, th_fall) if data_transition == '01' else (th_fall, th_rise)
    else:
        (th_data_start, th_data_end) = (th_high, th_low) if data_is_rising else (th_low, th_high)
    t_data_start = t_clk_active - t_setup - th_data_start * t_data_full_slew

    # Find the pulse width of the data signal, then build the data waveform
    data_pulse_width = (1-th_data_start)*t_data_slew + t_setup + t_hold + (1-th_data_end)*t_data_slew
    (v0, v1) = (vss, vdd) if data_is_rising else (vdd, vss)
    data_pwl = utils.slew_pwl(v0, v1, t_data_slew, t_data_start, th_low, th_high)
    data_pwl += utils.slew_pwl(v1, v0, t_data_slew, data_pulse_width, th_low, th_high, data_pwl[-1][0])[1:]

    # Initialize circuit
    circuit = utils.init_circuit(circuit_title, cell.netlist, config.models, settings.named_nodes, settings.units)
    circuit.V('o_cap', 'vout', 'wout', 0) # 0 volt source in series with c_load is a trick to measure current through the load capacitor.
    circuit.C('c_load', 'wout', circuit.gnd, c_load)
    circuit.PieceWiseLinearVoltageSource('clk', 'vclk', circuit.gnd, values=clk_pwl)
    circuit.PieceWiseLinearVoltageSource('data', 'vdata', circuit.gnd, values=data_pwl)

    # Initialize device under test subcircuit and wire up pins
    connections = []
    for pin in cell.pins_in_netlist_order():
        if pin.role == 'clock':
            connections.append('vclk')
        elif pin.name == data_pin:
            connections.append('vdata')
        elif pin.name == output_pin:
            connections.append('vout')
        elif pin.role == 'primary_power':
            connections.append('vdd')
        elif pin.role == 'primary_ground':
            connections.append('vss')
        elif pin.name in state_map.keys() and len(state_map[pin.name]) == 1:
            connections.append('vdd' if state_map[pin.name] == '1' else 'vss')
        else:
            connections.append('wfloat0') # float unrecognized
    circuit.X('dut', cell.name, *connections)

    # Build the simulation
    simulator = PySpice.Simulator.factory(simulator=settings.simulation.backend)
    simulation = simulator.simulation(
        circuit,
        temperature=settings.temperature,
        nominal_temperature=settings.temperature
    )
    simulation.options('nopage', 'nomod', rshunt=1e9, trtol=1)
    simulation.transient(
        step_time=min(t_data_slew, t_clk_slew)/4,
        end_time=t_data_start + data_pulse_width + t_stabilizing,
        run=False
    )

    if settings.debug and debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        with open(debug_dir / f'{cell.name}_ts_{t_setup}_th_{t_hold}_cl_{c_load}.spice'.replace(" ", ""), 'w') as f:
            f.write(str(simulation))

    return (simulator, simulation)


def get_t_stabilizing(cell, config, settings, path, state_map, k=2, th_low=0.03, th_high=0.99, **sim_kwargs):
    """Find a reasonable estimate of the stabilizing time for the current configuration.

    The stabilizing time is the delay between lockdown (when any existing state is cleared) and c2q
    measurement. It is important to minimize stabilizing time as it has a major effect on total
    simulation runtime. This procedure measures the transient time of the output signal, then
    multiplies that by a 'safety factor' k to determine a reasonable stabilizing time."""

    simulator, simulation = sim_latch(cell, config, settings, path, state_map, **sim_kwargs)

    if settings.dry_run:
        # TODO: Display a message if not settings.quiet
        return -1. @ PySpice.Unit.u_s

    try:
        analysis = simulator.run(simulation)
    except Exception as e:
        raise ProcedureFailedException('get_t_stabilizing failed') from e

    # Set up post-processing parameters
    *_, output_transition = path
    output_is_rising = output_transition == '01'
    vdd = settings.primary_power.voltage * settings.units.voltage
    v_start = vdd * (th_low if output_is_rising else th_high)
    v_end = vdd - v_start
    time = np.array(analysis.time)
    vout = np.array(analysis['vout'])

    # Measure transient time
    start_crossings = np.where(np.diff(((np.sign(vout - v_start)) > 0) if output_is_rising else \
                                       ((np.sign(vout - v_start)) < 0)))
    end_crossings = np.where(np.diff(((np.sign(vout - v_end)) > 0) if output_is_rising else \
                                     ((np.sign(vout - v_end)) < 0)))
    transient_time = abs(time[end_crossings[-1]][0] - time[start_crossings[-1]][0])
    return (k*transient_time @ PySpice.Unit.u_s).convert(settings.units.time.prefixed_unit)


def get_c2q(cell, config, settings, path, state_map, debug_dir=None, **sim_kwargs):
    """Build a SPICE testbench and run a transient simulation to get the clock-to-q delay
    for a given setup skew / hold skew, load capacitance, and stabilizing time."""

    # Build latch simulation
    try:
        simulator, simulation = sim_latch(cell, config, settings, path, state_map,
                                          circuit_title='get_c2q', debug_dir=debug_dir,
                                          **sim_kwargs)
    except ValueError:
        # If t_setup + t_hold < 0 fail immediately
        return float('nan')

    if settings.dry_run:
        # TODO: Display a message if not settings.quiet
        return -1. @ PySpice.Unit.u_s

    # Run simulation
    try:
        analysis = simulator.run(simulation)
    except Exception as e:
        kwarg_str = ", ".join([f"{k}={v}" for k, v in sim_kwargs.items()])
        msg = f'Procedure get_c2q failed for cell {cell.name} with kwargs {kwarg_str}'
        raise ProcedureFailedException(msg) from e

    # Set up post-processing parameters
    data_pin, data_transition, output_pin, output_transition = path
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage
    th_low = settings.logic_thresholds.low
    th_high = settings.logic_thresholds.high
    th_rise = settings.logic_thresholds.rising
    th_fall = settings.logic_thresholds.falling

    # Check whether Q latched the D value by looking at vout after the 3rd clock edge
    time = np.array(analysis.time)
    vout = np.array(analysis['vout'])
    vclk = np.array(analysis['vclk'])

    # Find the time where the 3rd clock edge crosses the activation threshold
    clk_is_rising = state_map[cell.clock.name] == '1'
    th_clk_active = th_rise if clk_is_rising else th_fall
    v_clk_active = vdd*th_clk_active
    clk_crossings = np.where(np.diff(np.sign(vclk - v_clk_active)) > 0)[0] if clk_is_rising else \
                    np.where(np.diff(np.sign(vclk - v_clk_active)) < 0)[0]
    if len(clk_crossings) < 2:
        # TODO: Log why the procedure failed (not enough clock edges; error in clk wave gen)
        return float('nan')
    t_clk_edge = np.interp(v_clk_active, [vclk[clk_crossings[-1]], vclk[clk_crossings[-1] + 1]],
                                         [time[clk_crossings[-1]], time[clk_crossings[-1] + 1]])

    # Find when the output pin activates (i.e. Q latches) relative to the clock edge
    output_is_rising = output_transition == '01'
    v_q_active = vdd * (th_rise if output_is_rising else th_fall)
    q_crossings = np.where(np.diff(np.sign(vout - v_q_active)) > 0)[0] if output_is_rising else \
                  np.where(np.diff(np.sign(vout - v_q_active)) < 0)[0]
    if len(q_crossings) < 1:
        # TODO: Log why the procedure failed (Q never latches; overconstrained setup/hold window)
        return float('nan')
    t_q_edge = np.interp(v_q_active, [vout[q_crossings[-1]], vout[q_crossings[-1] + 1]],
                                     [time[q_crossings[-1]], time[q_crossings[-1] + 1]])

    return t_q_edge - t_clk_edge
