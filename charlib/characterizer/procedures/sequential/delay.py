import PySpice
import numpy as np
import math

from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.characterizer.procedures.sequential.constraint.metastability.c2q_contour import (
    get_t_stabilizing,
    sim_latch,
)
from charlib.liberty import liberty
from charlib.liberty.library import LookupTable

@register('data_slews', 'loads', 'transient_sim_end_time')
def sequential_worst_case(cell, config, settings):
    """Measure worst-case sequential clocked (c2q) propagation and transient delays

    For every (data_slew, load) variation, each non-masking data-to-output path is
    simulated with a relaxed setup/hold skew (large enough that the cell always
    latches) and the measured clock-to-output propagation delay and output
    transition are written as rising_edge timing tables on the output pin."""
    for variation in config.variations('data_slews', 'loads', 'transient_sim_end_time'):
        for path in cell.paths():
            state_maps = list(cell.nonmasking_conditions_for_path(*path))
            if not state_maps:
                continue
            yield (measure_delays_for_path, cell, config, settings, variation, path, state_maps)

def _last_crossing_after(time, v, level, rising, t_after):
    """Return the last time after t_after at which v crosses level in the given direction.

    :param time: Simulation time array
    :param v: Signal waveform
    :param level: Threshold voltage
    :param rising: True to detect upward crossings (0->1), False for downward (1->0)
    :param t_after: Only crossings with time >= t_after are considered
    :return: Crossing time (float, simulation time units), or None if not found
    """
    delta = np.diff(np.sign(v - level))
    indices = np.where(delta > 0)[0] if rising else np.where(delta < 0)[0]
    indices = np.array([i for i in indices if time[i] >= t_after], dtype=int)
    if len(indices) < 1:
        return None
    i = indices[-1]
    if i + 1 >= len(v):
        return None
    return float(np.interp(level, [v[i], v[i + 1]], [time[i], time[i + 1]]))

def measure_delays_for_path(cell, config, settings, variation, path, state_maps, criterion=max):
    """Measure worst-case clock-to-output delay & output transition over all non-masking
    conditions for one (data_pin, data_transition, output_pin, output_transition) path.

    A single transient simulation per state map measures both values; the clock edge is
    the final edge of the latch-locking waveform built by sim_latch (relaxed setup/hold
    skews), so every data path latches as expected.

    :param cell: A Cell object to test.
    :param config: A CellTestConfig object containing cell-specific test configuration.
    :param settings: A CharacterizationSettings object with library-wide configuration.
    :param variation: A dict with this variation's data_slews/loads/transient_sim_end_time.
    :param path: [input_pin, input_transition, output_pin, output_transition]
    :param state_maps: Non-masking state maps for this path (from nonmasking_conditions_for_path).
    :param criterion: Selection criterion across state maps (default: worst case).
    :return: The cell's liberty group, augmented with the measured timing tables.
    """
    data_pin, data_transition, output_pin, output_transition = path
    data_slew = variation['data_slews'] * settings.units.time
    load = variation['loads'] * settings.units.capacitance
    clock_pin = cell.clock
    output_is_rising = output_transition == '01'
    th_low = settings.logic_thresholds.low
    th_high = settings.logic_thresholds.high
    th_rise = settings.logic_thresholds.rising
    th_fall = settings.logic_thresholds.falling

    prop_values = []
    tran_values = []
    for state_map in state_maps:
        # Measure a stabilizing time once per variation; this keeps every subsequent
        # simulation short (the latch is guaranteed to be in a settled state).
        t_stabilizing = get_t_stabilizing(cell, config, settings, path, state_map,
                                          clock_slew_rate=None,
                                          data_slew_rate=data_slew,
                                          capacitive_load=load)
        try:
            simulator, simulation = sim_latch(cell, config, settings, path, state_map,
                                              capacitive_load=load,
                                              data_slew_rate=data_slew,
                                              stabilizing_time=t_stabilizing)
            analysis = simulator.run(simulation)
        except Exception as e:
            msg = f'Procedure sequential_worst_case failed for cell {cell.name} ' \
                  f'with variation {variation}, path {path}, state {state_map}'
            raise ProcedureFailedException(msg) from e

        time = np.array(analysis.time)
        vout = np.array(analysis['vout'])
        vclk = np.array(analysis['vclk'])
        vdd = settings.primary_power.voltage * settings.units.voltage

        # Locate the final (measured) clock edge threshold crossing
        clk_is_rising = state_map[cell.clock.name] == '1'
        th_clk_active = th_rise if clk_is_rising else th_fall
        t_clk_edge = _last_crossing_after(time, vclk, float(vdd * th_clk_active),
                                          clk_is_rising, float(0.0))
        if t_clk_edge is None:
            raise ProcedureFailedException(
                f'Procedure sequential_worst_case found no clock edge for cell {cell.name}, path {path}')

        # Output edge & transition (10-90% switching time on the captured edge)
        level_out = float(vdd * (th_rise if output_is_rising else th_fall))
        t_q_edge = _last_crossing_after(time, vout, level_out, output_is_rising, t_clk_edge)
        if t_q_edge is None:
            raise ProcedureFailedException(
                f'Output "{output_pin}" never latched the expected edge for cell {cell.name}, '
                f'path {path}, variation {variation} (setup/hold or netlist problem?)')

        prop_values.append(t_q_edge - t_clk_edge)

        t_th_low = _last_crossing_after(time, vout, float(vdd * th_low), output_is_rising, t_clk_edge)
        t_th_high = _last_crossing_after(time, vout, float(vdd * th_high), output_is_rising, t_clk_edge)
        if t_th_low is None or t_th_high is None:
            raise ProcedureFailedException(
                f'Unable to measure output transition for cell {cell.name}, path {path}')
        tran_values.append(abs(t_th_high - t_th_low))

    # Build liberty output: one timing group on the output pin per clock pin
    result = cell.liberty
    result.group('pin', output_pin).add_group('timing', f'/* {clock_pin.name} */') # FIXME: \
    # Hack to allow multiple timing groups while the liberty API doesn't support \
    # multiple groups with the same name. Timing groups are distinguished by related_pin.
    timing_group = result.group('pin', output_pin).group('timing', f'/* {clock_pin.name} */')
    timing_group.add_attribute('related_pin', clock_pin.name) # FIXME
    timing_group.add_attribute('timing_type',
                               'rising_edge' if not clock_pin.is_inverted() else 'falling_edge')

    lut_template_size = f'{len(config.parameters["loads"])}x{len(config.parameters["data_slews"])}'
    measurements = {
        ('cell_rise' if output_is_rising else 'cell_fall'): prop_values,
        ('rise_transition' if output_is_rising else 'fall_transition'): tran_values,
    }
    for lut_name, values in measurements.items():
        lut = LookupTable(lut_name, f'delay_template_{lut_template_size}',
                          total_output_net_capacitance=[load.convert(settings.units.capacitance.prefixed_unit).value],
                          input_net_transition=[data_slew.convert(settings.units.time.prefixed_unit).value])
        worst = criterion(values) @ PySpice.Unit.u_s
        lut.values[0, 0] = worst.convert(settings.units.time.prefixed_unit).value
        timing_group.add_group(lut)

    return result