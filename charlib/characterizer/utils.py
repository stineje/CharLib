"""Tools for building test circuits"""

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


def slew_pwl(v_0, v_1, t_slew, t_wait, low_threshold, high_threshold):
    """Return a list of 2-tuples describing the vertices of a piecewise linear slew waveform

    :param v_0: The initial voltage
    :param v_1: The voltage to slew to
    :param t_slew: The slew rate under test
    :param t_wait: The amount of time to hold the signal constant before slewing
    """
    # Determine the full time it takes to slew based on thresholds. See Figure 2-2 in  the Liberty
    # User Guide, Vol. 1 for details
    t_full_slew = t_slew / (high_threshold - low_threshold)
    return [
        (0,                         v_0),
        (t_wait,                    v_0),
        (t_wait + t_full_slew,      v_1) # simulator will hold this voltage until sim end
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

    return hi, phase1_candidates, phase2_candidates


def find_knee_point(boundary_points, arc_threshold=0.01):
    """Select a balanced (knee) setup/hold point from boundary samples.

    Algorithm:
      1. Normalize setup and hold axes to [0, 1] (min-max).
      2. Sort points by setup value; treat the first and last as chord endpoints.
      3. Knee = point with maximum perpendicular (orthogonal) distance to the chord.
      4. If max distance < arc_threshold the curve is effectively linear — fall back
         to the point closest to the chord midpoint in normalized space.
      5. Tie-break among near-tied candidates (within 5 % of max distance) by
         choosing the one closest to the chord midpoint in normalized space.

    Parameters
    ----------
    boundary_points : list of (setup_float, hold_float)
    arc_threshold   : minimum normalized perpendicular distance to treat the
                      boundary as curved; below this the midpoint fallback fires.

    Returns
    -------
    (setup_float, hold_float) in the same units as the input.
    """
    if not boundary_points:
        raise ValueError("boundary_points is empty")
    if len(boundary_points) == 1:
        return boundary_points[0]

    pts = np.array(boundary_points, dtype=float)   # (N, 2)

    # Normalize axes to [0, 1]
    s_min, s_max = pts[:, 0].min(), pts[:, 0].max()
    h_min, h_max = pts[:, 1].min(), pts[:, 1].max()
    s_range = s_max - s_min if s_max != s_min else 1.0
    h_range = h_max - h_min if h_max != h_min else 1.0

    norm = np.column_stack([
        (pts[:, 0] - s_min) / s_range,
        (pts[:, 1] - h_min) / h_range,
    ])

    # Sort by normalized setup so endpoints are the two extremes of the curve
    order = np.argsort(norm[:, 0])
    pts_s  = pts[order]
    norm_s = norm[order]

    p0, p1 = norm_s[0], norm_s[-1]
    chord     = p1 - p0
    chord_len = np.linalg.norm(chord)

    if chord_len < 1e-12:
        return tuple(pts_s[len(pts_s) // 2])

    # Perpendicular distance: 2-D cross-product magnitude / chord length
    diff  = norm_s - p0
    dists = np.abs(diff[:, 0] * chord[1] - diff[:, 1] * chord[0]) / chord_len

    max_dist = dists.max()
    mid_norm = (p0 + p1) / 2

    if max_dist < arc_threshold:
        best = int(np.argmin(np.linalg.norm(norm_s - mid_norm, axis=1)))
        return tuple(pts_s[best])

    # Near-tie candidates: within 5 % of max_dist
    candidates_mask = dists >= (max_dist * 0.95)
    candidates_norm = norm_s[candidates_mask]
    candidates_pts  = pts_s[candidates_mask]

    best = int(np.argmin(np.linalg.norm(candidates_norm - mid_norm, axis=1)))
    return tuple(candidates_pts[best])
