import PySpice
import matplotlib.pyplot as plt
from numpy import average

from charlib.characterizer import utils
from charlib.characterizer.cell import Port
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty import liberty
from charlib.liberty.library import LookupTable

@register
def combinational_worst_case(cell, config, settings):
    """Measure worst-case combinational transient and propagation delays"""
    for variation in config.variations('data_slews', 'loads'):
        for path in cell.paths():
            yield (measure_delay_for_path_with_criterion, cell, config, settings, variation, path,
                   max)

@register
def combinational_average(cell, config, settings):
    """Measure combinational transient and propagation delays using a uniform average"""
    for variation in config.variations('data_slews', 'loads'):
        for path in cell.paths():
            yield (measure_delay_for_path_with_criterion, cell, config, settings, variation, path,
                   average)

def measure_delay_for_path_with_criterion(cell, config, settings, variation, path,
                                          criterion=max) -> liberty.Group:
    """Given a particular path through the cell, find delay according to a selection criterion.

    This method tests all nonmasking conditions for the path through the cell from target_input to
    target_output with the given slew rate and capacitive load, then returns the delay selected
    using the passed criterion function.

    The default criterion selects the worst-case (i.e. maximum) delay. This is in theory an overly
    pessimistic method of delay estimation. A more accurate method would be to perform a weighted
    average of each delay based on the likelihood of the corresponding state transition. However,
    at the time of writing this function, CharLib has no mechanism for accepting prior transition
    likelihood information.

    :param cell: A Cell object to test.
    :param config: A CellTestConfig object containing cell-specific test configuration details.
    :param settings: A CharacterizationSettings object containing library-wide configuration
                     details.
    :param variation: A dict containing test parameters for this configuration variation, such
                      as slew rates and loads.
    :param path: A list in the format [input_port, input_transition, output_port,
                 output_transtition] describing the path under test in the cell.
    :param criterion: A function which returns a single value given a list of numeric values.
                      Default max.
    """
    # Set up key parameters
    [input_port, _, output_port, _] = path
    data_slew = variation['data_slew'] * settings.units.time
    load = variation['load'] * settings.units.capacitance
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # Measure delays for all nonmasking conditions
    analyses = {}
    measurement_names = set()
    for state_map in cell.nonmasking_conditions_for_path(*path):
        # Build the test circuit
        circuit = utils.init_circuit('comb_delay', cell.netlist, config.models,
                                     settings.named_nodes, settings.units)

        # Initialize device under test and wire up ports
        pin_map = utils.PinStateMap(cell.inputs, cell.outputs, state_map)
        connections = []
        measurements = []
        for port in cell.ports:
            match port.role:
                case Port.Role.LOGIC: # Digital logic inputs or outputs
                    if port.name in pin_map.target_inputs:
                        connections.append(f'v{port.name}')
                        (v_0, v_1) = (vss, vdd) if pin_map.target_inputs[port.name] == '01' else (vdd, vss)
                        circuit.PieceWiseLinearVoltageSource(
                            port.name,
                            f'v{port.name}', circuit.gnd,
                            values=utils.slew_pwl(v_0, v_1, data_slew, 3*data_slew,
                                                  1e-2*settings.logic_thresholds.low,
                                                  1e-2*settings.logic_thresholds.high))
                    elif port.name in pin_map.target_outputs:
                        connections.append(f'v{port.name}')
                        circuit.C(port.name, f'v{port.name}', circuit.gnd, load)
                        for in_port in pin_map.target_inputs:
                            if pin_map.target_inputs[in_port] == '01':
                                in_direction = 'rise'
                                threshold_prop_0 = settings.logic_thresholds.rising
                            else:
                                in_direction = 'fall'
                                threshold_prop_0 = settings.logic_thresholds.falling
                            if pin_map.target_outputs[port.name] == '01':
                                out_direction = 'rise'
                                threshold_prop_1 = settings.logic_thresholds.rising
                                threshold_tran_0 = settings.logic_thresholds.low
                                threshold_tran_1 = settings.logic_thresholds.high
                            else:
                                out_direction = 'fall'
                                threshold_prop_1 = settings.logic_thresholds.falling
                                threshold_tran_0 = settings.logic_thresholds.high
                                threshold_tran_1 = settings.logic_thresholds.low
                            prop_name = f'cell_{out_direction}__{in_port}_to_{port.name}'.lower()
                            measurement_names.add(prop_name)
                            measurements.append((
                                'tran', prop_name,
                                f'trig v(v{in_port}) val={float(vdd*1e-2*threshold_prop_0)} {in_direction}=1',
                                f'targ v(v{port.name}) val={float(vdd*1e-2*threshold_prop_1)} {out_direction}=1'))
                            tran_name = f'{out_direction}_transition__{in_port}_to_{port.name}'.lower()
                            measurement_names.add(tran_name)
                            measurements.append((
                                'tran', tran_name,
                                f'trig v(v{port.name}) val={float(vdd*1e-2*threshold_tran_0)} {out_direction}=1',
                                f'targ v(v{port.name}) val={float(vdd*1e-2*threshold_tran_1)} {out_direction}=1'))
                    elif port.name in pin_map.stable_inputs:
                        if pin_map.stable_inputs[port.name] == '0':
                            connections.append(settings.primary_ground.name)
                        else:
                            connections.append(settings.primary_power.name)
                    elif port.name in pin_map.ignored_outputs:
                        connections.append('wfloat0')
                    else:
                        raise ValueError(f'Unable to connect unrecognized logic port {port.name} in cell {cell.name}')
                case Port.Role.POWER:
                    connections.append(settings.primary_power.name)
                case Port.Role.GROUND:
                    connections.append(settings.primary_ground.name)
                case Port.Role.NWELL:
                    connections.append(settings.nwell.name)
                case Port.Role.PWELL:
                    connections.append(settings.pwell.name)
                case _:
                    raise ValueError(f'Unable to connect unrecognized port {port.name} in cell {cell.name}')
        circuit.X('dut', cell.name, *connections)

        # Run the simulation, taking all measurements
        simulator = PySpice.Simulator.factory(simulator=settings.simulation.backend)
        simulation = simulator.simulation(
            circuit,
            temperature=settings.temperature,
            nominal_temperature=settings.temperature
        )
        simulation.options('autostop', 'nopage', 'nomod', post=1, ingold=2, trtol=1)
        for measure in measurements:
            simulation.measure(*measure, run=False)
        simulation.transient(step_time=data_slew/8, end_time=1000*data_slew, run=False)

        stable_pins_map_str = ', '.join(['='.join([pin, state]) for pin, state in pin_map.stable_inputs.items()])
        try:
            analyses[stable_pins_map_str] = simulator.run(simulation)
        except Exception as e:
            msg = f'Procedure measure_worst_case_delay_for_path failed for cell {cell.name} ' \
                  f'with variation {variation}, pin states {state_map}'
            if settings.debug:
                debug_path = settings.debug_dir / cell.name / __name__.split('.')[-1]
                debug_path.mkdir(parents=True, exist_ok=True)
                with open(debug_path / f'slew = {data_slew} load = {load}.sp') as file:
                    file.write(str(simulation))
            raise ProcedureFailedException(msg) from e

    # Select the worst-case delays and add to LUTs
    result = cell.liberty
    result.group('pin', output_port).add_group('timing', f'/* {input_port} */') # FIXME: This is a \
    # hack to allow multiple timing groups while the liberty API doesn't yet support multiple
    # groups with the same name and no id. In practice timing groups are distinguished by
    # their related_pin attribute.
    result.group('pin', output_port).group('timing', f'/* {input_port} */').add_attribute('related_pin', input_port) # FIXME
    for name in measurement_names:
        # Get the worst delay & plot io
        if 'io' in config.plots:
            fig = utils.plot_io_voltages(analyses.values(), list(pin_map.target_inputs.keys()),
                                         list(pin_map.target_outputs.keys()),
                                         legend_labels=analyses.keys(),
                                         indicate_voltages=[settings.primary_power.voltage*1e-2*settings.logic_thresholds.low,
                                                            settings.primary_power.voltage*1e-2*settings.logic_thresholds.high])
            # FIXME: let user decide whether to show or save
            fig_path = settings.plots_dir / cell.name / 'io'
            fig_path.mkdir(parents=True, exist_ok=True)
            fig.savefig(fig_path / f'{name} with slew = {data_slew} load = {load}.png') # FIXME: filetype should be configurable
            plt.close(fig)

        # Build LUT
        delay = criterion([analysis.measurements[name] for analysis in analyses.values()]) @ PySpice.Unit.u_s
        lut_name, meas_path = name.split('__')
        lut_template_size = f'{len(config.parameters["loads"])}x{len(config.parameters["data_slews"])}'
        lut = LookupTable(lut_name, f'delay_template_{lut_template_size}',
                          total_output_net_capacitance=[load.convert(settings.units.capacitance.prefixed_unit).value],
                          input_net_transition=[data_slew.convert(settings.units.time.prefixed_unit).value])
        lut.values[0,0] = delay.convert(settings.units.time.prefixed_unit).value
        result.group('pin', output_port).group('timing', f'/* {input_port} */').add_group(lut) # FIXME

    return result
