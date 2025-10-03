"""Tools for building test circuits"""

import PySpice
from matplotlib import pyplot as plt

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

def init_circuit(title, cell_netlist, models):
    """Perform common circuit initialization tasks"""
    circuit = PySpice.Circuit(title)
    circuit.include(cell_netlist)
    for model in models:
        if len (model) > 1:
            circuit.lib(*model)
        else:
            circuit.include(model[0])
            # TODO: if model.is_dir(), use SpiceLibrary
            #   To do this, we'll also need to know which subckts are used by the netlist
    return circuit

def plot_io_voltages(analyses, input_signals, output_signals, legend_labels,
                     indicate_voltages=[], indicate_times=[], fig_label='', title='I/O Voltages'):
    """Plot input and output voltages from simulation results.

    Given a list of analysis objects and signals to plot, construct a series of plots showing the
    voltage signals over time. Indicate key voltage and time values if desired.

    :param analyses: A list of analysis results from simulation.
    :param input_signals: A list of signal names in the analyses which should be displayed in the
                          upper half of the plot.
    :param output_signals: A list of signal names in the analyses which should be displayed in the
                           lower half of the plot.
    :param legend_labels: Labels corresponding to each analysis. results
    :param indicate_voltages: Key voltage values to be indicated as horizontal lines on each ax.
    :param indicate_times: Key time values to be indicated as vertical lines on each ax.
    """
    signals = input_signals + output_signals
    ratios = [1]*len(input_signals) + [len(input_signals)]*len(output_signals)
    figure, axes = plt.subplots(len(signals), sharex=True, height_ratios=ratios, label=fig_label)
    for ax, signal in zip(axes, signals):
        for voltage in indicate_voltages:
            ax.axhline(voltage, color='0.5', linestyle=':')
        for time in indicate_times:
            ax.axvline(time, color='r', linestyle='--')
        ax.set_ylabel('v' + signal)
        for analysis, label in zip(analyses, legend_labels):
            t = analysis.time # TODO: Figure out how to get time unit from this
            ax.plot(t, analysis['v' + signal])
    axes[0].set_title(title)
    axes[-1].set_xlabel('Time')
    return figure
