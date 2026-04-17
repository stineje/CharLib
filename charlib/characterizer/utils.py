"""Tools for building test circuits"""

import csv
import math

import PySpice
import numpy as np


class PinStateMap:
    """Connect ports of a cell to the appropriate waveforms for a test.

    Maps cell ports to logic levels or transitions for a particular path through the cell.

    Keeps track of:
    - which inputs are changing
    - whether each of those inputs is rising or falling
    - which outputs are expected to change in response
    - whether each of those outputs is expected to rise or fall
    - the logic value required for each stable input
    - TODO: required level or transition for special pins, like enables, resets, and clocks
    """

    def __init__(self, inputs: list, outputs: list, pin_states: dict):
        self.target_inputs = {}
        self.stable_inputs = {}
        self.target_outputs = {}
        self.ignored_outputs = []

        # TODO: Make this more sophisticated, with list of Port objects as input instead of input
        # and output port names
        for name in inputs:
            state = pin_states[name]
            if len(state) == 2:
                self.target_inputs[name] = state
            elif len(state) == 1:
                self.stable_inputs[name] = state
            else:
                raise ValueError(f'Expected state to be a string of length 1 or 2, got "{state}" (length {len(state)})')
        for name in outputs:
            try:
                state = pin_states[name]
                self.target_outputs[name] = state
            except KeyError:
                self.ignored_outputs.append(name)
                continue


def slew_pwl(v_0, v_1, t_slew, t_wait, low_threshold, high_threshold, t_start=0):
    """Return a list of 2-tuples describing the vertices of a piecewise linear slew waveform

    :param v_0: The initial voltage
    :param v_1: The voltage to slew to
    :param t_slew: The duration for the signal to slew between the thresholds
    :param t_wait: The duration after t_start to hold the signal constant before slewing
    :param t_start: The start time for the waveform (useful for building multi-slew waves)
    """
    # Determine the full time it takes to slew based on thresholds. See Figure 2-2 in  the Liberty
    # User Guide, Vol. 1 for details
    t_full_slew = t_slew / (high_threshold - low_threshold)
    return [
        (t_start,                        v_0),
        (t_start + t_wait,               v_0),
        (t_start + t_wait + t_full_slew, v_1)
    ]

def init_circuit(title, cell_netlist, models, supplies, units):
    """Perform common circuit initialization tasks

    :param title: The title for the created circuit object
    :param cell_netlist: A path-like object pointing to a cell's SPICE netlist (from Cell.netlist)
    :param models: A list of path-likes or tuples to be imported (from CellTestConfig.models)
    :param supplies: Key voltage supplies to create (from CharacterizationSettings.named_nodes)
    :param units: An object describing which unit to use (from CharacterizationSettings.units)

    1. Sets up a new circuit with the given title
    2. Imports cell_netlist and models using the appropriate .lib or .include syntax
    3. Sets up voltage supplies in the circuit
    """
    circuit = PySpice.Circuit(title)
    circuit.include(cell_netlist)
    for model in models:
        if len (model) > 1:
            circuit.lib(*model)
        else:
            circuit.include(model[0])
            # TODO: if model.is_dir(), use SpiceLibrary
            #   To do this, we'll also need to know which subckts are used by the netlist
    for supply in supplies:
        if supply.name.upper() not in ['GND', '0']:
            circuit.V(supply.subscript, supply.name, circuit.gnd, supply.voltage*units.voltage)
    return circuit

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
    phase1_candidates = []
    phase2_candidates = []

    # Phase 1 — expand downward from start to find a lower bound (first failed latch)
    hi = start
    lo = None
    for exp in range(max_exp):
        candidate = start - step * (2 ** exp)
        phase1_candidates.append(candidate)
        result = probe_fn(candidate)
        if math.isnan(result):
            lo = candidate
            break
        hi = candidate

    if lo is None:
        return hi, phase1_candidates, phase2_candidates

    # Phase 2 — binary search between lo (NaN) and hi (valid)
    while (hi - lo) > tolerance:
        mid = (lo + hi) / 2
        phase2_candidates.append((lo, mid, hi))
        if math.isnan(probe_fn(mid)):
            lo = mid
        else:
            hi = mid

    # return hi because hi is always simulated and deemed valid
    return hi, phase1_candidates, phase2_candidates


def find_knee_point(boundary_points, chord_p0, chord_p1, arc_threshold=0.1):
    """Select a balanced (knee) setup/hold point from boundary samples.

    Algorithm:
      1. Normalize setup and hold axes to [0, 1] (min-max), anchored to chord_p0/p1.
      2. The reference chord is the line from chord_p0 (min setup, max hold) to
         chord_p1 (max setup, min hold) — the step1/step2 and step4/step3 results.
      3. Compute signed perpendicular distance to the chord (positive = concave side,
         i.e. bowing toward the origin, which is the only meaningful knee direction).
      4. If no points lie on the concave side, the boundary is linear or convex —
         fall back to the point closest to the chord midpoint in normalized space.
      5. If the maximum concave distance / chord_len < arc_threshold the arch is too
         shallow — fall back to the point closest to the chord midpoint.
      6. Otherwise knee = point with maximum concave perpendicular distance.
         Tie-break among near-tied candidates (within 5 % of max distance) by
         choosing the one closest to the chord midpoint in normalized space.

    Parameters
    ----------
    boundary_points : list of (setup_float, hold_float)
    chord_p0        : (setup_float, hold_float) — min-setup / max-hold anchor (step1/step2)
    chord_p1        : (setup_float, hold_float) — max-setup / min-hold anchor (step4/step3)
    arc_threshold   : dimensionless ratio; minimum (perpendicular deviation / chord length)
                      required to treat the boundary as curved. 0.2 means the peak
                      concave deviation must exceed 20 % of the chord length.

    Returns
    -------
    (setup_float, hold_float) in the same units as the input.
    """
    if not boundary_points:
        raise ValueError("boundary_points is empty")
    if len(boundary_points) == 1:
        return boundary_points[0], True

    pts = np.array(boundary_points, dtype=float)   # (N, 2)

    # Normalize axes to [0, 1] using chord endpoints as bounds.
    # chord_p0 = (min_setup, max_hold), chord_p1 = (max_setup, min_hold)
    chord_p0 = np.array(chord_p0, dtype=float)
    chord_p1 = np.array(chord_p1, dtype=float)
    s_min, s_max = chord_p0[0], chord_p1[0]
    h_min, h_max = chord_p1[1], chord_p0[1]
    s_range = s_max - s_min if s_max != s_min else 1.0
    h_range = h_max - h_min if h_max != h_min else 1.0

    norm = np.column_stack([
        (pts[:, 0] - s_min) / s_range,
        (pts[:, 1] - h_min) / h_range,
    ])

    p0 = np.array([(chord_p0[0] - s_min) / s_range, (chord_p0[1] - h_min) / h_range])
    p1 = np.array([(chord_p1[0] - s_min) / s_range, (chord_p1[1] - h_min) / h_range])
    chord     = p1 - p0
    chord_len = np.linalg.norm(chord)

    if chord_len < 1e-12:
        return tuple(pts[len(pts) // 2]), True

    # Signed perpendicular distance (positive = concave side, bowing toward origin).
    # Walking from p0 (min setup) to p1 (max setup), the concave/knee side is the
    # region where hold is lower than the chord predicts (points closer to origin).
    vecs_from_p0  = norm - p0  # vector from p0 to each boundary point
    # cross product: |vecs_from_p0| * |chord| * sin(θ), divided by chord_len gives |vecs_from_p0| * sin(θ) = perpendicular distance from each point to the chord line
    # sign: positive = concave side (below chord, toward origin), negative = convex side
    signed_dists  = (vecs_from_p0[:, 0] * chord[1] - vecs_from_p0[:, 1] * chord[0]) / chord_len

    # Projection of each point along the chord direction (0 = p0, chord_len = p1).
    # this is for the fallback if either max arc is too shallow or no points are on the convex side
    chord_unit   = chord / chord_len
    projections  = vecs_from_p0 @ chord_unit  # scalar projection of each point along the chord direction

    concave_mask     = signed_dists > 0
    max_concave_dist = signed_dists[concave_mask].max() if np.any(concave_mask) else 0.0
    # Fall back to midpoint if no concave points or arch is too shallow relative to chord length.
    # Find the boundary point whose along-chord projection is closest to the chord midpoint.
    if max_concave_dist / chord_len < arc_threshold:
        best = int(np.argmin(np.abs(projections - chord_len / 2)))
        return tuple(pts[best]), True # (point, is_fallback)

    # Significant concave arch: knee = max concave distance point.
    # Tie-break among near-tied candidates (within 5 % of max) by along-chord projection.
    candidates_mask = concave_mask & (signed_dists >= (max_concave_dist * 0.95))
    candidate_projs = projections[candidates_mask]
    candidates_pts  = pts[candidates_mask]
    best = int(np.argmin(np.abs(candidate_projs - chord_len / 2)))
    return tuple(candidates_pts[best]), False # (point, is_fallback)


def write_c2q_csv(debug_path, settings, c2q_a, c2q_b, setup_vals_s, hold_vals_s,
                  t_stabilizing, ref_c2q_steps, c2q_threshold):
    """Write the c2q sweep results to a CSV file for debugging

    The first data row is a reference point at (t_stabilizing, t_stabilizing) showing
    ref_c2q_steps and the c2q_threshold used for step-5 validity gating. Subsequent rows
    are the actual sweep points, each annotated with a 'valid' flag.
    """
    t_unit = settings.units.time.prefixed_unit
    c2q_merged = np.where(~np.isnan(c2q_a), c2q_a, c2q_b)

    debug_path.mkdir(parents=True, exist_ok=True)
    with open(debug_path / 'c2q_merged.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([f'setup_{t_unit.str_spice()}', f'hold_{t_unit.str_spice()}',
                         f'c2q_{t_unit.str_spice()}', 'valid', f'c2q_threshold_{t_unit.str_spice()}'])
        # Reference row: c2q at (t_stabilizing, t_stabilizing) and the degradation threshold
        t_stab_display = float(t_stabilizing.convert(t_unit).value)
        ref_display = float((ref_c2q_steps @ PySpice.Unit.u_s).convert(t_unit).value) if not math.isnan(ref_c2q_steps) else float('nan')
        thr_display = float((c2q_threshold @ PySpice.Unit.u_s).convert(t_unit).value) if not math.isinf(c2q_threshold) else float('inf')
        writer.writerow([f'{t_stab_display:.6g}', f'{t_stab_display:.6g}',
                         f'{ref_display:.6g}', True, f'{thr_display:.6g}'])
        for hi, h_s in enumerate(hold_vals_s):
            for si, s_s in enumerate(setup_vals_s):
                val = c2q_merged[hi, si]
                if math.isnan(val):
                    writer.writerow([f'{s_s:.6g}', f'{h_s:.6g}', 'nan', False, ''])
                else:
                    c2q_display = float((val @ PySpice.Unit.u_s).convert(t_unit).value)
                    writer.writerow([f'{s_s:.6g}', f'{h_s:.6g}', f'{c2q_display:.6g}', val < c2q_threshold, ''])
