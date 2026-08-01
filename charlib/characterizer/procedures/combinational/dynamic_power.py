import numpy as np
import PySpice

from charlib.characterizer import utils
from charlib.characterizer.cell import Port
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty.library import LookupTable


@register('data_slews', 'loads', 'transient_sim_end_time', 'energy_settling_tolerance')
def combinational_dynamic_power(cell, config, settings):
    """Measure worst-case switching energy for all combinational input-to-output paths"""
    for variation in config.variations('data_slews', 'loads', 'transient_sim_end_time',
                                       'energy_settling_tolerance'):
        for path in cell.paths():
            yield (measure_dynamic_power_for_path, cell, config, settings, variation, path)


@register('data_slews', 'loads', 'transient_sim_end_time', 'energy_settling_tolerance')
def combinational_dynamic_power_charge_corrected(cell, config, settings):
    """Measure worst-case switching energy, corrected to approximate industry (e.g. Cadence
    Liberate) internal_power conventions rather than a raw VDD-current integral.

    Applies internal_power = 0.5 * (|raw settle-cutoff energy| - C_load*Vdd^2*charges_load)
    per nonmasking condition, where charges_load is True exactly when the output transitions
    high (output_transition == '01')

    Empirically validated (within a few percent of real Cadence Liberate runs) for any cell
    where the characterized arc's driving path feeds a SINGLE OUTPUT-producing gate stage

    TODO: known limitation, not yet solved. For cells where an internal signal fans out to
    MULTIPLE separate output-producing gates (e.g. decoders, muxes), this procedure
    over-estimates internal_power for the swept/measured output pin, by a factor that grows
    with the number of unmeasured sibling fan-out branches
    Root cause: Cadence Liberate appears to attribute only a fraction of a
    *shared* driving stage's dissipation to each output pin it fans out to, which a single
    whole-cell VDD-current measurement cannot replicate without topology-aware analysis of
    which arcs share internal driving nodes. 
    
    DO NOT TRUST this procedure's numbers for decoder/mux-style cells until this is addressed.
    Use the default combinational_dynamic_power for a simple VDD-current integral.
    """
    for variation in config.variations('data_slews', 'loads', 'transient_sim_end_time',
                                       'energy_settling_tolerance'):
        for path in cell.paths():
            yield (measure_dynamic_power_for_path, cell, config, settings, variation, path, True)


def _apply_charge_correction(gross_J, ideal_charge_energy_J, charges_load):
    """Apply the correction to one nonmasking condition's raw energy. Matched to Cadence Liberate

    :param gross_J: Raw settle-cutoff switching energy for this nonmasking condition, in Joules.
    :param ideal_charge_energy_J: C_load*Vdd^2 for this variation, in Joules.
    :param charges_load: True if this transition charges the output load from VDD (output
                         rises), False otherwise (output falls). See
                         combinational_dynamic_power_charge_corrected's docstring.
    :returns: The corrected energy, 0.5*(gross_J - ideal_charge_energy_J*charges_load).
    """
    return 0.5 * (gross_J - ideal_charge_energy_J * charges_load)


def measure_dynamic_power_for_path(cell, config, settings, variation, path, charge_corrected=False):
    """Measure worst-case switching energy for one input-to-output path.

    Runs a transient simulation and integrates VDD*I_VDD in Python over the actual switching
    event (from the start of the input transition until the supply current settles back to
    within energy_settling_tolerance of its post-transition value), then writes a rise_power
    or fall_power LUT into an internal_power group on the output pin.

    The simulation is still run out to t_sim_end (a generous fixed multiple of the data slew,
    or transient_sim_end_time if larger) so that the settling point can be found reliably, but
    only the settled portion of the waveform is used to locate the integration endpoint --
    any leakage current occurring during the switching event itself is intentionally left in
    the integral, since it is part of what the device actually does while switching.

    :param cell: A Cell object to test.
    :param config: A CellTestConfig object containing cell-specific test configuration details.
    :param settings: A CharacterizationSettings object containing library-wide configuration
                     details.
    :param variation: A dict containing test parameters for this configuration variation, such
                      as slew rates and loads.
    :param path: A list in the format [input_pin, input_transition, output_pin,
                 output_transition] describing the path under test in the cell.
    :param charge_corrected: If True, apply a correction to each nonmasking
                     condition's raw energy before worst-case selection, instead of reporting the
                     raw settle-cutoff energy directly. Correction formula matched to Cadence Liberate
    """
    [input_pin, input_transition, output_pin, output_transition] = path
    data_slew = variation['data_slews'] * settings.units.time
    load = variation['loads'] * settings.units.capacitance
    t_sim_end = max(variation['transient_sim_end_time'] * settings.units.time, 1000 * data_slew)
    settling_tolerance = variation['energy_settling_tolerance']
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # Integration window starts at t_wait, when the input slew begins (matching slew_pwl call
    # in delay.py); its end is found from the simulated waveform, not fixed in advance.
    t_wait = 3 * data_slew
    # .value is the coefficient in the canonicalized unit; .scale is the SI scale factor (e.g., 1e-9 for ns)
    t_wait_s = float(t_wait.value) * float(t_wait.scale)

    # VDD element name, used to look up the branch current in the transient analysis
    vdd_elem = f'v{settings.primary_power.subscript}'.lower()

    lut_name = 'rise_power' if output_transition == '01' else 'fall_power'

    # Simulate all nonmasking conditions and collect net switching energies
    energies = []
    for state_map in cell.nonmasking_conditions_for_path(*path):
        pin_map = utils.PinStateMap(cell.inputs, cell.outputs, state_map)

        circuit = utils.init_circuit('dyn_pwr', cell.netlist, config.models,
                                     settings.named_nodes, settings.units)
        connections = []
        for pin in cell.pins_in_netlist_order():
            match pin.role:
                case Port.Role.LOGIC:
                    if pin.name in pin_map.target_inputs:
                        connections.append(f'v{pin.name}')
                        (v_0, v_1) = (vss, vdd) if pin_map.target_inputs[pin.name] == '01' else (vdd, vss)
                        circuit.PieceWiseLinearVoltageSource(
                            pin.name, f'v{pin.name}', circuit.gnd,
                            values=utils.slew_pwl(v_0, v_1, data_slew, t_wait,
                                                  settings.logic_thresholds.low,
                                                  settings.logic_thresholds.high))
                    elif pin.name in pin_map.target_outputs:
                        connections.append(f'v{pin.name}')
                        circuit.C(pin.name, f'v{pin.name}', circuit.gnd, load)
                    elif pin.name in pin_map.stable_inputs:
                        if pin_map.stable_inputs[pin.name] == '0':
                            connections.append(settings.primary_ground.name)
                        else:
                            connections.append(settings.primary_power.name)
                    elif pin.name in pin_map.ignored_outputs:
                        connections.append(f'wfloat_{pin.name}')
                    else:
                        raise ValueError(
                            f'Unable to connect unrecognized logic pin {pin.name} in cell {cell.name}')
                case Port.Role.POWER:
                    connections.append(settings.primary_power.name)
                case Port.Role.GROUND:
                    connections.append(settings.primary_ground.name)
                case Port.Role.NWELL:
                    connections.append(settings.nwell.name)
                case Port.Role.PWELL:
                    connections.append(settings.pwell.name)
                case _:
                    raise ValueError(
                        f'Unable to connect unrecognized pin {pin.name} in cell {cell.name}')
        circuit.X('dut', cell.name, *connections)

        simulator = PySpice.Simulator.factory(simulator=settings.simulation.backend)
        simulation = simulator.simulation(
            circuit,
            temperature=settings.temperature,
            nominal_temperature=settings.temperature
        )
        simulation.options('nopage', 'nomod', post=1, ingold=2, trtol=1)
        simulation.transient(step_time=data_slew / 8, end_time=t_sim_end, run=False)

        try:
            analysis = simulator.run(simulation)
        except Exception as e:
            msg = (f'Procedure measure_dynamic_power_for_path failed for cell {cell.name} '
                   f'with variation {variation}, pin states {state_map}')
            if settings.debug:
                debug_path = settings.debug_dir / cell.name / __name__.split('.')[-1]
                debug_path.mkdir(parents=True, exist_ok=True)
                with open(debug_path / f'slew = {data_slew} load = {load}.sp', 'w',
                          encoding='utf-8') as file:
                    file.write(str(simulation))
            raise ProcedureFailedException(msg) from e

        t = np.asarray(analysis.time, dtype=float)
        i_vdd = np.asarray(analysis.branches[vdd_elem], dtype=float)
        window = t >= t_wait_s
        tt, ii = t[window], i_vdd[window]
        if tt.size == 0 or np.isnan(ii).any():
            continue

        # Locate the end of the switching event: the last point at which the supply current
        # deviates from its post-transition (settled) value by more than settling_tolerance
        # of the peak excursion.
        i_final = ii[-1]
        i_peak = ii[np.argmax(np.abs(ii))]
        deviation_threshold = settling_tolerance * abs(i_peak - i_final)
        if deviation_threshold <= 0:
            t_settle = tt[0]
        else:
            unsettled = np.where(np.abs(ii - i_final) > deviation_threshold)[0]
            t_settle = tt[unsettled[-1]] if unsettled.size else tt[0]

        integration_window = tt <= t_settle
        # by SPICE convention, i(vdd_elem) is negative when VDD sources current
        gross_charge_C = abs(np.trapezoid(ii[integration_window], tt[integration_window]))
        gross_J = gross_charge_C * settings.primary_power.voltage

        if charge_corrected:
            load_F = float(load.value) * float(load.scale)
            ideal_charge_energy_J = load_F * settings.primary_power.voltage ** 2
            gross_J = _apply_charge_correction(
                gross_J, ideal_charge_energy_J, charges_load=(output_transition == '01'))

        energies.append(gross_J)

    if not energies:
        return cell.liberty

    worst_J = max(energies)
    energy_value = (worst_J @ PySpice.Unit.u_J).convert(
        settings.units.energy.prefixed_unit
    ).value

    result = cell.liberty
    ip_id = f'/* {input_pin} */'
    result.group('pin', output_pin).add_group('internal_power', ip_id)
    result.group('pin', output_pin).group('internal_power', ip_id).add_attribute(
        'related_pin', input_pin)

    lut_template_size = f'{len(config.parameters["loads"])}x{len(config.parameters["data_slews"])}'
    lut = LookupTable(lut_name, f'energy_template_{lut_template_size}',
                      total_output_net_capacitance=[
                          load.convert(settings.units.capacitance.prefixed_unit).value],
                      input_net_transition=[
                          data_slew.convert(settings.units.time.prefixed_unit).value])
    lut.values[0, 0] = energy_value
    result.group('pin', output_pin).group('internal_power', ip_id).add_group(lut)

    return result
