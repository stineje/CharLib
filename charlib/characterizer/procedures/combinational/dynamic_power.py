import math
import PySpice

from charlib.characterizer import utils
from charlib.characterizer.cell import Port
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty.library import LookupTable


@register('data_slews', 'loads', 'transient_sim_end_time')
def combinational_dynamic_power(cell, config, settings):
    """Measure worst-case switching energy for all combinational input-to-output paths"""
    for variation in config.variations('data_slews', 'loads', 'transient_sim_end_time'):
        for path in cell.paths():
            yield (measure_dynamic_power_for_path, cell, config, settings, variation, path)


def measure_dynamic_power_for_path(cell, config, settings, variation, path):
    """Measure worst-case switching energy for one input-to-output path.

    Runs a transient simulation with a .meas INTEGRAL command to capture VDD*I_VDD energy
    over the switching window, subtracts the pre-transition leakage baseline, and writes a
    rise_power or fall_power LUT into an internal_power group on the output pin.

    :param cell: A Cell object to test.
    :param config: A CellTestConfig object containing cell-specific test configuration details.
    :param settings: A CharacterizationSettings object containing library-wide configuration
                     details.
    :param variation: A dict containing test parameters for this configuration variation, such
                      as slew rates and loads.
    :param path: A list in the format [input_pin, input_transition, output_pin,
                 output_transition] describing the path under test in the cell.
    """
    [input_pin, input_transition, output_pin, output_transition] = path
    data_slew = variation['data_slews'] * settings.units.time
    load = variation['loads'] * settings.units.capacitance
    t_sim_end = max(variation['transient_sim_end_time'] * settings.units.time, 1000 * data_slew)
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # Integration window: input slew begins at t_wait (matching slew_pwl call in delay.py)
    t_wait = 3 * data_slew
    # .value is the coefficient in the canonicalized unit; .scale is the SI scale factor (e.g., 1e-9 for ns)
    t_wait_s = float(t_wait.value) * float(t_wait.scale)
    t_sim_end_s = float(t_sim_end.value) * float(t_sim_end.scale)

    # VDD element name for the .meas integral expression
    vdd_elem = f'v{settings.primary_power.subscript}'.lower()

    lut_name = 'rise_power' if output_transition == '01' else 'fall_power'
    meas_name = f'{lut_name}__{input_pin}_to_{output_pin}'.lower()

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
        simulation.measure('tran', meas_name,
                           f'integ i({vdd_elem})',
                           f'from={t_wait_s:.6g}',
                           f'to={t_sim_end_s:.6g}',
                           run=False)
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

        if meas_name not in analysis.measurements or math.isnan(analysis.measurements[meas_name]):
            continue
        # by SPICE convention, i(vdd_elem) is negative when VDD sources current
        gross_charge_C = abs(analysis.measurements[meas_name])
        gross_J = gross_charge_C * settings.primary_power.voltage

        # Subtract pre-transition leakage baseline to isolate switching energy
        initial_state = {name: trans[0] for name, trans in pin_map.target_inputs.items()}
        initial_state.update(pin_map.stable_inputs)
        debug_path = (settings.debug_dir / cell.name / __name__.split('.')[-1]) if settings.debug else None
        try:
            op_analysis = utils.operating_point_analysis(
                cell, config, settings, initial_state, debug_path=debug_path)
            i_leakage = float(op_analysis.branches[settings.primary_power.name.lower()][0])
            leakage_J = settings.primary_power.voltage * abs(i_leakage) * (t_sim_end_s - t_wait_s)
        except Exception:
            leakage_J = 0.0

        energies.append(max(0.0, gross_J - leakage_J))

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
