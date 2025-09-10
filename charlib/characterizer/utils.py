"""Tools for building test circuits"""

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
    :param t_wait: The amount of time to hold the signal constant before and after slewing
    """
    # Determine the full time it takes to slew based on thresholds. See Figure 2-2 in  the Liberty
    # User Guide, Vol. 1 for details
    t_full_slew = t_slew / (high_threshold - low_threshold)
    return [
        (0,                         v_0),
        (t_wait,                    v_0),
        (t_wait + t_full_slew,      v_1),
        (2 * t_wait + t_full_slew,  v_1)
    ]
