"""Plotting utilities for characterization results"""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


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
    figure, axs = plt.subplots(nrows=len(signals), sharex=True, height_ratios=ratios,
                               label=fig_label)
    for ax, signal in zip(axs, signals):
        for voltage in indicate_voltages:
            ax.axhline(voltage, color='0.5', linestyle=':')
        for time in indicate_times:
            ax.axvline(time, color='r', linestyle='--')
        ax.set_ylabel('v' + signal)
        for analysis, label in zip(analyses, legend_labels):
            t = analysis.time # TODO: Figure out how to get time unit from this
            ax.plot(t, analysis['v' + signal], label=label)
    axs[0].set_title(title)
    axs[-1].set_xlabel('Time')
    axs[-1].legend()
    return figure


def plot_delay_surfaces(lut_groups, fig_label='', title='Cell Delays'):
    """Plot delay surfaces from a series of liberty.LookupTable groups.

    Given a list of 2D LUTs which share common index variables, plot each as a 3D surface.

    :param lut_groups: A list of liberty.LookupTable groups containing delay data.
    """
    figure, ax = plt.subplots(label=fig_label, subplot_kw={'projection': '3d'})
    ax.set(
        xlabel=list(lut_groups[0].template.variables.keys())[0],
        ylabel=list(lut_groups[0].template.variables.keys())[1],
        zlabel='Delay',
        title=title
    )
    indices = np.meshgrid(*(lut_groups[0].index_values), indexing='ij')
    for lut, color in zip(lut_groups, list(mcolors.TABLEAU_COLORS)[:len(lut_groups)]):
        ax.plot_wireframe(*indices, lut.values, label=lut.name, color=color)
    figure.legend(loc='center left')
    return figure


def plot_contour(settings, points, min_setup, max_hold, max_setup, min_hold,
                 debug_path, filename, title, knee_point=None, knee_is_fallback=None):
    """Save a scatter plot of (setup, hold) points. No-ops if debug_path is None.

    :param points: List of (setup_val, hold_val, color) tuples in display time units.
    :param filename: Output filename under debug_path.
    :param title: Full plot title string.
    :param knee_point: Optional (setup_val, hold_val) in display time units to highlight.
    """
    if debug_path is None:
        return
    debug_path.mkdir(parents=True, exist_ok=True)

    t_unit = settings.units.time.prefixed_unit
    t_unit_str = t_unit.str_spice()

    def _to_unit(qty):
        return float(qty.convert(t_unit).value)

    fig, ax = plt.subplots(figsize=(8, 6))

    for s_s, h_s, color in points:
        ax.plot(s_s, h_s, 'o', color=color, markersize=6)

    ax.plot(_to_unit(min_setup), _to_unit(max_hold),
            'b^', markersize=9, label='step1/step2 (min setup, max hold)')
    ax.plot(_to_unit(max_setup), _to_unit(min_hold),
            'bs', markersize=9, label='step4/step3 (max setup, min hold)')

    if knee_point is not None:
        knee_label = 'knee point (midpoint fallback)' if knee_is_fallback else 'knee point (knee search)'
        ax.plot(knee_point[0], knee_point[1], 'y*', markersize=14, label=knee_label)

    ax.axvline(0, color='gray', linewidth=0.8, linestyle='--')
    ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    ax.set_xlabel(f'Setup time ({t_unit_str})')
    ax.set_ylabel(f'Hold time ({t_unit_str})')
    ax.set_title(title)
    ax.legend(fontsize='small')
    fig.tight_layout()

    plot_path = debug_path / filename
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)
