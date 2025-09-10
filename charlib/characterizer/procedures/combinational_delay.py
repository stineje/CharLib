import itertools
import PySpice

from charlib.characterizer.procedures import register
from charlib.characterizer.utils import PinStateMap, slew_pwl
from charlib.liberty import liberty

@register
def combinational_worst_case(cell, config, settings):
    """Measure worst-case combinational transient and propagation delays"""
    # Construct & yield simulation tasks for each permutation of test arc & config variation
    for variation in config.variations():
        for path in cell.paths():
            yield (measure_worst_case_delay_for_path, cell, config, settings, variation, path)

def measure_worst_case_delay_for_path(cell, config, settings, variation, path) -> liberty.Group:
    """Given a particular path through the cell, find the worst-case delay for this test variation.

    This method tests all nonmasking conditions for the path through the cell from target_input to
    target_output with the given slew rate and capacitive load, then returns data for the
    worst-case (i.e. largest) delay.

    This is in theory an overly pessimistic method of delay estimation. A more accurate method
    would be to perform a weighted average of each delay based on the likelihood of the
    corresponding state transition. However, at the time of writing this function, CharLib has no
    mechanism for accepting prior transition likelihood information.

    :param cell: A Cell object to test.
    :param config: A CellTestConfig object containing cell-specific test configuration details.
    :param settings: A CharacterizationSettings object containing library-wide configuration
                     details.
    :param variation: A dict containing test parameters for this configuration variation, such
                      as slew rates and loads.
    :param path: A list in the format [input_port, input_transition, output_port,
                 output_transtition] describing the path under test in the cell.
    """
    result = liberty.Group('cell', cell.name)
    result += cell.liberty

    # Set up key parameters
    data_slew = variation['data_slew'] * settings.units.time
    load = variation['load'] * settings.units.capacitance
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # Measure all nonmasking conditions and keep only the worst case
    analyses = []
    for state_map in cell.nonmasking_conditions_for_path(*path):

        # Build the test circuit
        circuit = PySpice.Circuit('comb_delay')
        circuit.include(cell.netlist)
        for model in config.models:
            if len(model) > 1:
                circuit.lib(*model)
            else:
                circuit.include(model[0])
                # TODO: if model.is_dir(), use SpiceLibrary
        circuit.V('dd', 'vdd', circuit.gnd, vdd)
        circuit.V('ss', 'vss', circuit.gnd, vss)

        # Initialize device under test and wire up ports
        pin_map = PinStateMap(cell.inputs, cell.outputs, state_map)
        connections = []
        measurements = []
        for port in cell.ports:
            if port.name in pin_map.target_inputs:
                connections.append(f'v{port.name}')
                (v_0, v_1) = (vss, vdd) if pin_map.target_inputs[port.name] == '01' else (vdd, vss)
                circuit.PieceWiseLinearVoltageSource(
                    port.name,
                    f'v{port.name}', circuit.gnd,
                    values=slew_pwl(v_0, v_1, data_slew, 3*data_slew,
                                    settings.logic_thresholds.low,
                                    settings.logic_thresholds.high))
            elif port.name in pin_map.stable_inputs:
                connections.append('vss' if pin_map.stable_inputs[port.name] == '0' else 'vdd')
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
                    measurements.append((
                        'tran', f't_{in_port}_to_{port.name}_prop',
                        f'trig v(v{in_port}) val={float(vdd*1e-2*threshold_prop_0)} {in_direction}=1',
                        f'targ v(v{port.name}) val={float(vdd*1e-2*threshold_prop_1)} {out_direction}=1'))
                    measurements.append((
                        'tran', f't_{in_port}_to_{port.name}_tran',
                        f'trig v(v{port.name}) val={float(vdd*1e-2*threshold_tran_0)} {out_direction}=1',
                        f'targ v(v{port.name}) val={float(vdd*1e-2*threshold_tran_1)} {out_direction}=1'))
            elif port.role == 'primary_power':
                connections.append('vdd')
            elif port.role == 'primary_ground':
                connections.append('vss')
            elif port.name in pin_map.ignored_outputs:
                connections.append(f'wfloat0')
            else:
                raise ValueError(f'Unable to connect unrecognized port {port.name}')
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
        analyses += [simulation.transient(step_time=data_slew/8, end_time=1000*data_slew)]

    # Select the worst delay
    print(analyses)

    return result
