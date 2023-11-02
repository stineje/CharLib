"""This module contains test managers for various types of standard cells"""

from itertools import product
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from PySpice.Spice.Library import SpiceLibrary
from PySpice.Spice.Netlist import Circuit
from PySpice.Tools.StringTools import str_spice
from PySpice.Unit import *

from characterizer.functions import Function, registered_functions
from characterizer.Harness import CombinationalHarness, SequentialHarness, filter_harnesses_by_ports, find_harness_by_arc
from characterizer.LogicParser import parse_logic
from liberty.cell import Cell, Pin, TableTemplate

class TestManager:
    """A test manager for a standard cell"""
    def __init__ (self, name: str, in_ports: str|list, out_ports: list|None, functions: str|list, **kwargs):
        """Create a new TestManager for a standard cell.

        A TestManager manages cell data, runs simulations on cells, and stores results
        on the cell.
        
        :param name: cell name
        :param in_ports: a list of input pin names
        :param out_ports: a list of output pin names
        :param functions: a list of functions implemented by each of the cell's outputs (in verilog syntax)
        :param **kwargs: a dict of configuration and test parameters for the cell, including
            - netlist: path to the cell's spice netlist
            - model: path to transistor spice models
            - slews: input slew rates to test
            - loads: output capacitave loads to test
            - simulation_timestep: the time increment to use during simulation"""
        # Initialize the cell under test
        self._cell = Cell(name, kwargs.get('area', 0))
        for pin_name in in_ports:
            self.cell.add_pin(pin_name, 'input')
        for pin_name in out_ports:
            self.cell.add_pin(pin_name, 'output')

        # Parse functions and add to pins
        if isinstance(functions, str):
            functions = functions.upper().split() # Capitalize and split on space, then proceed
        if isinstance(functions, list):
            # Should be in the format ['Y=expr1', 'Z=expr2']
            for func in functions:
                if '=' in func:
                    func_pin, expr = func.split('=')
                    # Check for nonblocking assign in LHS of equation
                    if '<' in func_pin:
                        func_pin = func_pin.replace('<','').strip()
                    for pin_name in out_ports:
                        if pin_name == func_pin:
                            if parse_logic(expr):
                                # Check if we already recognize this function
                                function = Function(expr)
                                for reg_name, reg_func in registered_functions.items():
                                    if reg_func == function:
                                        # Copy test vectors
                                        print(f'Recognized {self.cell.name} pin {pin_name} function as {reg_name}')
                                        function.stored_test_vectors = reg_func.test_vectors
                                self.cell[pin_name].function = function
                            else:
                                raise ValueError(f'Invalid function "{expr}"')
                else:
                    raise ValueError(f'Expected an expression of the form "Y=A Z=B" for cell function, got "{func}"')

        # Characterization settings
        self.netlist = kwargs.get('netlist')
        self.models = kwargs.get('models', [])
        self._in_slews = kwargs.get('slews', [])
        self._out_loads = kwargs.get('loads', [])
        self._sim_timestep = 0
        if 'simulation_timestep' in kwargs:
            self.sim_timestep = kwargs['simulation_timestep']

        # Behavioral/internal-use settings
        self.plots = kwargs.get('plots', [])
        self._is_exported = False

    @property
    def cell(self) -> Cell:
        """Return the cell under test"""
        return self._cell

    @property
    def in_ports(self) -> list:
        """Return cell input io pins."""
        return [pin for pin in self.cell.pins.values() if pin.direction == 'input' and pin.is_io()]

    @property
    def out_ports(self) -> list:
        """Return cell output io pins."""
        return [pin for pin in self.cell.pins.values() if pin.direction == 'output' and pin.is_io()]

    @property
    def functions(self) -> list:
        """Return a list of functions on this cell's output pins."""
        return [pin.function for pin in self.out_ports]

    @property
    def models(self) -> list:
        """Return cell models"""
        return self._models

    @models.setter
    def models(self, value):
        models = []
        """Set paths to cell transistor models"""
        for model in value:
            modelargs = model.split()
            path = Path(modelargs.pop(0))
            if modelargs: # If the list is not empty (e.g. there is a section parameter)
                section = modelargs.pop(0)
                # Use a tuple so that this is included with .lib path section syntax
                if not path.is_file():
                    raise ValueError(f'Invalid model {path} {section}: {path} is not a file')
                models.append((path, section))
            else:
                if path.is_dir():
                    models.append(SpiceLibrary(path))
                elif path.is_file():
                    models.append(path)
                else:
                    raise FileNotFoundError(f'File {value} not found')
        self._models = models

    def _include_models(self, circuit):
        """Include models in the circuit netlist."""
        for model in self.models:
            if isinstance(model, SpiceLibrary):
                for device in self.used_models():
                    # TODO: Handle the case where we have multiple spice libraries
                    circuit.include(model[device])
            elif isinstance(model, Path):
                circuit.include(model)
            elif isinstance(model, tuple):
                circuit.lib(*model)

    @property
    def netlist(self) -> str:
        """Return path to cell netlist."""
        return self._netlist

    @netlist.setter
    def netlist(self, value):
        """Set path to cell netlist."""
        if isinstance(value, (str, Path)):
            if not Path(value).is_file():
                raise ValueError(f'Invalid value for netlist: {value} is not a file')
            self._netlist = Path(value)
        else:
            raise TypeError(f'Invalid type for netlist: {type(value)}')

    def definition(self) -> str:
        """Return the cell's spice definition"""
        # Search the netlist file for the circuit definition
        with open(self.netlist, 'r') as file:
            for line in file:
                if self.cell.name in line.upper() and 'SUBCKT' in line.upper():
                    file.close()
                    return line
            # If we reach this line before returning, the netlist file doesn't contain a circuit definition
            file.close()
            raise ValueError(f'No cell definition found in netlist {self.netlist}')

    def instance(self) -> str:
        """Return a subcircuit instantiation for this cell."""
        # Reorganize the definition into an instantiation with instance name XDUT
        # TODO: Instance name should probably be configurable from library settings
        instance = self.definition().split()[1:]  # Delete .subckt
        instance.append(instance.pop(0))        # Move circuit name to last element
        instance.insert(0, 'XDUT')                # Insert instance name
        return ' '.join(instance)

    def used_models(self) -> list:
        """Return a list of subcircuits used by this cell."""
        subckts = []
        with open(self.netlist, 'r') as file:
            for line in file:
                if line.lower().startswith('x'):
                    # Get the subckt name
                    # This should be the last item that doesn't contain =
                    for term in reversed(line.split()):
                        if '=' not in term:
                            subckts.append(term)
                            break
            file.close()
        print(subckts)
        return subckts

    @property
    def in_slews(self) -> list:
        """Return slew rates to use during testing."""
        return self._in_slews

    def add_in_slew(self, value: float):
        """Add a slew rate to the list of slew rates."""
        self._in_slews.append(float(value))

    @property
    def out_loads(self) -> list:
        """Return output capacitive loads to use during testing."""
        return self._out_loads

    def add_out_load(self, value: float):
        """Add a load to the list of output loads."""
        self._out_loads.append(float(value))

    @property
    def plots(self) -> list:
        """Return plotting configuration."""
        return self._plots
    
    @plots.setter
    def plots(self, value):
        """Set plot configuration

        :param value: a str or list specifying which plot types to generate."""
        if value == 'all':
            self._plots = ['io', 'delay', 'power']
        elif value == 'none':
            self._plots = []
        elif isinstance(value, list):
            self._plots = value
        else:
            raise ValueError(f'Invalid value for plots: "{value}"')

    @property
    def is_exported(self) -> bool:
        """Return whether the results have been exported"""
        return self._is_exported

    def set_exported(self):
        """Set a flag that this test manager's results have been exported"""
        self._is_exported = True

    @property
    def sim_timestep(self):
        """Return simulation timestep."""
        return self._sim_timestep

    @sim_timestep.setter
    def sim_timestep(self, value):
        """Set simulation timestep.
        
        :param value: The timestep to use during simulation. If `'auto'`, use 1/10 of smalleset slew rate."""
        if value == 'auto':
            if self.in_slews:
                # Use 1/10th of minimum slew rate
                self._sim_timestep = min(self.in_slews)/10.0
            else:
                raise ValueError('Cannot use auto for sim_timestep unless in_slews is set first!')
        elif isinstance(value, (float, int, str)):
            self._sim_timestep = float(value)
        else:
            raise TypeError(f'Invalid type for sim_timestep: {type(value)}')

    def _run_input_capacitance(self, settings, target_pin):
        """Measure the input capacitance of target_pin.

        Assuming a black-box model, treat the cell as a grounded capacitor with fixed capacitance.
        Perform an AC sweep on the circuit and evaluate the capacitance as d/ds(i(s)/v(s))."""
        print(f'Running input_capacitance for pin {target_pin} of cell {self.cell.name}')
        vdd = settings.vdd.voltage * settings.units.voltage
        vss = settings.vss.voltage * settings.units.voltage
        # TODO: Make these values configurable from settings
        f_start = 10 @ u_Hz
        f_stop = 10 @ u_GHz
        r_in = 10 @ u_GOhm
        i_in = 1 @ u_uA
        r_out = 10 @ u_GOhm
        c_out = 1 @ u_pF

        # Initialize circuit
        circuit = Circuit(f'{self.cell.name}_pin_{target_pin}_cap')
        self._include_models(circuit)
        circuit.include(self.netlist)
        circuit.V('dd', 'vdd', circuit.gnd, vdd)
        circuit.V('ss', 'vss', circuit.gnd, vss)
        circuit.I('in', circuit.gnd, 'vin', f'DC 0 AC {str_spice(i_in)}')
        circuit.R('in', circuit.gnd, 'vin', r_in)

        # Initialize device under test and wire up ports
        ports = self.definition().upper().split()[1:]
        subcircuit_name = ports.pop(0)
        connections = []
        for port in ports:
            if port == target_pin:
                connections.append('vin')
            elif port == settings.vdd.name.upper():
                connections.append('vdd')
            elif port == settings.vss.name.upper():
                connections.append('vss')
            else:
                # Add a resistor and capacitor to each output
                circuit.C(port, f'v{port}', circuit.gnd, c_out)
                circuit.R(port, f'v{port}', circuit.gnd, r_out)
                connections.append(f'v{port}')
        circuit.X('dut', subcircuit_name, *connections)

        # Measure capacitance as the slope of the conductance
        simulator = circuit.simulator(temperature=settings.temperature,
                                      nominal_temperature=settings.temperature,
                                      simulator=settings.simulator)
        analysis = simulator.ac('dec', 100, f_start, f_stop)
        impedance = np.abs(analysis.vin)/i_in
        [capacitance, _] = np.polyfit(analysis.frequency, np.reciprocal(impedance)/(2*np.pi), 1)

        return capacitance


class CombinationalTestManager(TestManager):
    """A combinational cell test manager"""

    def characterize(self, settings):
        """Characterize a combinational cell"""
        # Measure input capacitance for all input pins
        for pin in self.in_ports:
            input_capacitance = self._run_input_capacitance(settings, pin.name) @ u_F
            self.cell[pin.name].capacitance = input_capacitance.convert(settings.units.capacitance.prefixed_unit).value

        # Run delay simulation for all test vectors of each function
        for out_port in self.out_ports:
            unsorted_harnesses = []
            # Run characterization
            for test_vector in out_port.function.test_vectors:
                # Map pins to test vector
                inputs = out_port.function.operands
                state_map = dict(zip([*inputs, out_port.name], test_vector))

                # Generate harness
                harness = CombinationalHarness(self, state_map)
                trial_name = f'delay {self.cell.name} {harness.short_str()}'

                # Run delay characterization
                for slew in self.in_slews:
                    for load in self.out_loads:
                        self._run_delay(settings, harness, slew, load, trial_name)
                unsorted_harnesses.append(harness)

            # Filter out harnesses that aren't worst-case conditions
            # We should be left with the critical path rise and fall harnesses for each i/o path
            harnesses = []
            for in_port in self.in_ports:
                for direction in ['rise', 'fall']:
                    # Iterate over harnesses that match output, input, and direction
                    matching_harnesses = [harness for harness in filter_harnesses_by_ports(unsorted_harnesses, in_port, out_port) if harness.out_direction == direction]
                    worst_case_harness = matching_harnesses[0]
                    for harness in matching_harnesses:
                        # FIXME: Currently we compare by average prop delay. Consider alternative strategies
                        if worst_case_harness.average_propagation_delay() < harness.average_propagation_delay():
                            worst_case_harness = harness # This harness is worse
                    harnesses.append(worst_case_harness)

            # Store propagation and transient delay in pin timing tables
            for in_port in self.in_ports:
                self.cell[out_port.name].add_timing(in_port.name)
                for direction in ['rise', 'fall']:
                    # Identify the correct harness
                    harness = find_harness_by_arc(harnesses, in_port, out_port, direction)

                    # Construct the table
                    index_1 = [str(slew) for slew in self.in_slews]
                    index_2 = [str(load) for load in self.out_loads]
                    prop_values = []
                    tran_values = []
                    for slew in index_1:
                        for load in index_2:
                            result = harness.results[slew][load]
                            prop_value = (result['prop_in_out'] @ u_s).convert(settings.units.time.prefixed_unit).value
                            prop_values.append(f'{prop_value:7f}')
                            tran_value = (result['trans_out'] @ u_s).convert(settings.units.time.prefixed_unit).value
                            tran_values.append(f'{tran_value:7f}')
                    # TODO: Template names should probably be in LibrarySettings
                    template = TableTemplate()
                    template.name = f'delay_template_{len(index_1)}x{len(index_2)}'
                    template.variables = ['input_net_transition', 'total_output_net_capacitance']
                    self.cell[out_port.name].timing[in_port.name].add_table(f'cell_{direction}', template, prop_values, index_1, index_2)
                    self.cell[out_port.name].timing[in_port.name].add_table(f'{direction}_transition', template, tran_values, index_1, index_2)

            # Display plots
            if 'io' in self.plots:
                [self.plot_io(settings, harness) for harness in harnesses]
            if 'delay' in self.plots:
                [self.cell[out_pin.name].plot_delay(settings, self.cell.name) for out_pin in self.out_ports]
            if 'energy' in self.plots:
                print("Energy plotting not yet supported") # TODO: Add correct energy measurement procedure
            if plt.get_figlabels():
                plt.tight_layout()
                plt.show()

        return self.cell

    def _run_delay(self, settings, harness: CombinationalHarness, slew, load, trial_name):
        print(f'Running {trial_name} with slew={slew*settings.units.time}, load={load*settings.units.capacitance}')
        harness.results[str(slew)][str(load)] = self._run_delay_trial(settings, harness, slew, load)

    def _run_delay_trial(self, settings, harness: CombinationalHarness, slew, load):
        """Run delay measurement for a single trial"""
        # Set up parameters
        data_slew = slew * settings.units.time
        t_start = data_slew
        t_end = t_start + data_slew
        t_simend = 10000 * data_slew
        vdd = settings.vdd.voltage * settings.units.voltage
        vss = settings.vss.voltage * settings.units.voltage

        # Initialize circuit
        # TODO: Consider adding a driving cell (such as an inverter) to improve accuracy
        circuit = Circuit(f'{self.cell.name}_delay')
        self._include_models(circuit)
        circuit.include(self.netlist)
        (v_start, v_end) = (vss, vdd) if harness.in_direction == 'rise' else (vdd, vss)
        pwl_values = [(0, v_start), (t_start, v_start), (t_end, v_end), (t_simend, v_end)]
        circuit.PieceWiseLinearVoltageSource('in', 'vin', circuit.gnd, values=pwl_values)
        circuit.V('high', 'vhigh', circuit.gnd, vdd)
        circuit.V('low', 'vlow', circuit.gnd, vss)
        circuit.V('dd_dyn', 'vdd_dyn', circuit.gnd, vdd)
        circuit.V('ss_dyn', 'vss_dyn', circuit.gnd, vss)
        circuit.V('o_cap', 'vout', 'wout', circuit.gnd)
        circuit.C('0', 'wout', 'vss_dyn', load * settings.units.capacitance)

        # Initialize device under test subcircuit and wire up ports
        ports = self.definition().upper().split()[1:]
        subcircuit_name = ports.pop(0)
        connections = []
        for port in ports:
            if port == harness.target_in_port.pin.name:
                connections.append('vin')
            elif port == harness.target_out_port.pin.name:
                connections.append('vout')
            elif port == settings.vdd.name.upper():
                connections.append('vdd_dyn')
            elif port == settings.vss.name.upper():
                connections.append('vss_dyn')
            elif port in [pin.pin.name for pin in harness.stable_in_ports]:
                for stable_port in harness.stable_in_ports:
                    if port == stable_port.pin.name:
                        if stable_port.state == '1':
                            connections.append('vhigh')
                        elif stable_port.state == '0':
                            connections.append('vlow')
                        else:
                            raise ValueError(f'Invalid state identified during simulation setup for port {port}: {state}')
            else:
                connections.append('wfloat0') # Float any unrecognized ports
        if len(connections) is not len(ports):
            raise ValueError(f'Failed to match all ports identified in definition "{self.definition().strip()}"')
        circuit.X('dut', subcircuit_name, *connections)

        # Initialize simulator
        simulator = circuit.simulator(temperature=settings.temperature,
                                      nominal_temperature=settings.temperature,
                                      simulator=settings.simulator)
        simulator.options('autostop', 'nopage', 'nomod', post=1, ingold=2, trtol=1)

        # Measure delay
        pct_vdd = lambda x : x * settings.vdd.voltage
        match harness.in_direction:
            case 'rise':
                v_prop_start = settings.logic_threshold_low_to_high
            case 'fall':
                v_prop_start = settings.logic_threshold_high_to_low
        match harness.out_direction:
            case 'rise':
                v_prop_end = settings.logic_threshold_low_to_high
                v_trans_start = settings.logic_threshold_low
                v_trans_end = settings.logic_threshold_high
            case 'fall':
                v_prop_end = settings.logic_threshold_high_to_low
                v_trans_start = settings.logic_threshold_high
                v_trans_end = settings.logic_threshold_low
        simulator.measure('tran', 'prop_in_out',
                        f'trig v(vin) val={pct_vdd(v_prop_start)} {harness.in_direction}=1',
                        f'targ v(vout) val={pct_vdd(v_prop_end)} {harness.out_direction}=1')
        simulator.measure('tran', 'trans_out',
                        f'trig v(vout) val={pct_vdd(v_trans_start)} {harness.out_direction}=1',
                        f'targ v(vout) val={pct_vdd(v_trans_end)} {harness.out_direction}=1')

        # Run transient analysis
        return simulator.transient(step_time=(self.sim_timestep * settings.units.time), end_time=t_simend)

    def plot_io(self, settings, harness):
        """Plot I/O voltages vs time"""
        # TODO: Look for ways to generate fewer plots here - maybe a creative 3D plot
        figures = []
        # Group data by slew rate so that inputs are the same
        for slew in self.in_slews:
            # Generate plots for Vin and Vout
            figure, (ax_i, ax_o) = plt.subplots(2,
                sharex=True,
                height_ratios=[3, 7],
                label=f'{self.cell.name} | {harness.arc_str()} | {str(slew*settings.units.time)}'
            )
            volt_units = str(settings.units.voltage.prefixed_unit)
            time_units = str(settings.units.time.prefixed_unit)
            ax_i.set(
                ylabel=f'Vin (pin {harness.target_in_port.pin.name}) [{volt_units}]',
                title='I/O Voltages vs. Time'
            )
            ax_o.set(
                ylabel=f'Vout (pin {harness.target_out_port.pin.name}) [{volt_units}]',
                xlabel=f'Time [{time_units}]'
            )
            for load in self.out_loads:
                analysis = harness.results[str(slew)][str(load)]
                ax_o.plot(analysis.time / settings.units.time, analysis.vout, label=f'Fanout={load*settings.units.capacitance}')
            ax_o.legend()
            ax_i.plot(analysis.time / settings.units.time, analysis.vin)

            # Add lines indicating logic levels and timing
            for ax in [ax_i, ax_o]:
                ax.grid()
                for level in [settings.logic_threshold_low, settings.logic_threshold_high]:
                    ax.axhline(level*settings.vdd.voltage, color='0.5', linestyle='--')
                for t in [slew, 2*slew]:
                    ax.axvline(float(t), color='r', linestyle=':')

            figures.append(figure)
        return figures
        

class SequentialTestManager(TestManager):
    """A sequential cell test manager"""

    def __init__(self, name: str, in_ports: list, out_ports: list, clock: str, flops: str, function: str, **kwargs):
        super().__init__(name, in_ports, out_ports, function, **kwargs)
        # TODO: Use flops in place of functions for sequential cells
        self.set = kwargs.get('set')
        self.reset = kwargs.get('reset')
        self.clock = clock
        self.flops = flops

        self._clock_slew = kwargs.get('clock_slew', 0)

        # Setup and Hold time search parameters
        self.setup_time_range = kwargs.get('setup_time_range', [0.1, 1])
        self.hold_time_range = kwargs.get('hold_time_range', [0.1, 1])

    @property
    def clock(self) -> Pin:
        """Return clock pin"""
        return self.cell[self.clock_name]

    @property
    def clock_name(self) -> str:
        """Return clock pin name."""
        return self._clock_name

    @property
    def clock_trigger(self) -> str:
        """Return clock trigger type."""
        return self._clock_trigger

    @clock.setter
    def clock(self, value: str):
        """Assign clock trigger and pin"""
        (self._clock_trigger, pin) = _parse_triggered_pin(value, 'clock')
        self._clock_name = pin.name
        self.cell.add_pin(pin.name, pin.direction, pin.role)

    @property
    def clock_slew(self) -> float:
        """Return clock slew rate"""
        if self.in_slews and not self._clock_slew:
            return min(self.in_slews)
        return float(self._clock_slew)

    @property
    def set(self):
        """Return set pin"""
        return self.cell.pins.get(self.set_name)

    @property
    def set_name(self) -> str:
        """Return set pin name"""
        return self._set_name

    @property
    def set_trigger(self) -> str:
        "Return set pin trigger type"
        return self._set_trigger

    @set.setter
    def set(self, value):
        """Assign set pin and trigger"""
        if value is not None:
            (self._set_trigger, pin) = _parse_triggered_pin(value, 'set')
            self._set_name = pin.name
            self.cell.add_pin(pin.name, pin.direction, pin.role)
        else:
            self._set_name = None

    @property
    def reset(self):
        """Return reset pin"""
        return self.cell.pins.get(self.reset_name)

    @property
    def reset_name(self) -> str:
        """Return reset pin name"""
        return self._reset_name
    
    @property
    def reset_trigger(self) -> str:
        """Return reset trigger type"""
        return self._reset_trigger

    @reset.setter
    def reset(self, value):
        """Assign reset pin and trigger"""
        if value is not None:
            (self._reset_trigger, pin) = _parse_triggered_pin(value, 'reset')
            self._reset_name = pin.name
            self.cell.add_pin(pin.name, pin.direction, pin.role)
        else:
            self._reset_name = None

    @property
    def flops(self) -> list:
        # TODO: Use flops in place of functions for sequential cells
        return self._flops

    @flops.setter
    def flops(self, value):
        # TODO: Use flops in place of functions for sequential cells
        if isinstance(value, str):
            self._flops = value.split()
        elif isinstance(value, list):
            self._flops = value
        else:
            raise TypeError(f'Invalid type for sequential cell flop names: {type(value)}')

    def characterize(self, settings):
        """Run Delay, Recovery & Removal characterization for a sequential cell"""
        # Measure input capacitance for all input pins
        in_cap_pins = [*self.in_ports, self.clock]
        if self.set:
            in_cap_pins += [self.set]
        if self.reset:
            in_cap_pins += [self.reset]
        for pin in in_cap_pins:
            input_capacitance = self._run_input_capacitance(settings, pin.name) @ u_F
            self.cell[pin.name].capacitance = input_capacitance.convert(settings.units.capacitance.prefixed_unit).value

        # Save test results to cell
        normalize_t_units = lambda value: (value @ u_s).convert(settings.units.time.prefixed_unit).value

        for out_port in self.out_ports:
            unsorted_harnesses = []
            # Generate Harnesses and run characterization
            for test_vector in out_port.function.test_vectors:
                # Map pins
                inputs = out_port.function.operands
                state_map = dict(zip([*inputs, out_port.name], test_vector))
                state_map[self.clock.name] = '0101' if self.clock_trigger == 'posedge' else '1010'
                if self.set:
                    state_map[self.set.name] = '0' if self.set_trigger == 'posedge' else '1'
                if self.reset:
                    state_map[self.reset.name] = '0' if self.reset_trigger == 'posedge' else '1'
                # TODO: Add flops

                # Generate harness
                harness = SequentialHarness(self, state_map)
                trial_name = f'delay {self.cell.name} {harness.short_str()}'

                # Run characterization
                for slew in self.in_slews:
                    for load in self.out_loads:
                        self._run_delay(settings, harness, slew, load, trial_name)
                unsorted_harnesses.append(harness)

            # TODO: Filter out harnesses that aren't worst-case conditions
            harnesses = unsorted_harnesses

            # Store propagation and transient delay in pin timing tables
            for in_port in self.in_ports: # TODO: Add set and reset
                self.cell[out_port.name].add_timing(in_port.name)
                for direction in ['rise', 'fall']:
                    # Identify the correct harness
                    harness = find_harness_by_arc(harnesses, in_port, out_port, direction)

                    # Construct the table
                    index_1 = [str(slew) for slew in self.in_slews]
                    index_2 = [str(load) for load in self.out_loads]
                    prop_values = []
                    tran_values = []
                    for slew in index_1:
                        for load in index_2:
                            result = harness.results[slew][load]
                            prop_values.append(f'{normalize_t_units(result["prop_in_out"]):7f}')
                            tran_values.append(f'{normalize_t_units(result["trans_out"]):7f}')
                    # TODO: Template names should probably be in LibrarySettings
                    template = TableTemplate()
                    template.name = f'delay_template_{len(index_1)}x{len(index_2)}'
                    template.variables = ['input_net_transition', 'total_output_net_capacitance']
                    self.cell[out_port.name].timing[in_port.name].add_table(f'cell_{direction}', template, prop_values, index_1, index_2)
                    self.cell[out_port.name].timing[in_port.name].add_table(f'{direction}_transition', template, tran_values, index_1, index_2)

            # TODO: Store setup and hold constraints

            # TODO: Store internal power results

            # Display plots
            if 'io' in self.plots:
                [self.plot_io(settings, harness) for harness in harnesses]
            if 'delay' in self.plots:
                [self.cell[out_pin.name].plot_delay(settings, self.cell.name) for out_pin in self.out_ports]
            if 'energy' in self.plots:
                pass # TODO
            if plt.get_figlabels():
                plt.tight_layout()
                plt.show()

        return self.cell

    def _run_delay(self, settings, harness: SequentialHarness, slew, load, trial_name):
        # Set up slew and load parameters
        t_slew = slew * settings.units.time
        c_load = load * settings.units.capacitance
    
        print(f'Running sequential {trial_name} with slew={str(t_slew)}, load={str(c_load)}')
        t_stab = self._find_stabilizing_time(settings, harness, t_slew, c_load)
        msp, mhp = self._find_setup_hold_delay(settings, harness, t_slew, c_load, t_stab)
        print(msp)
        print(mhp)

    def _find_stabilizing_time(self, settings, harness, t_slew, c_load):
        """Find a reasonable stablilizing time for the current configuration.

        The stabilizing time is the delay between the first half of the procedure, where we zero
        out any initial state, and the second half of the procedure, where we measure delay
        characteristics. It's important to minimize stabilizing time as it has a major effect on
        total simulation time."""
        # Start with 100x max slew rate. Run a single simulation and measure the time it takes for
        # the Q output to change from 1% of vdd to 99% of vdd
        t_stab = 100 * max(self.in_slews) * settings.units.time
        t_setup = max(self.setup_time_range) * settings.units.time
        t_hold = max(self.hold_time_range) * settings.units.time
        sim, t = self._build_test_circuit(settings, harness, t_slew, c_load, t_setup, t_hold, t_stab)

        # Measure time it takes for Q to stabilize
        sim.measure('tran', 't_stabilizing',
            f'trig v(vout) val={0.01*settings.vdd.voltage} td={float(t["removal"])} {harness.out_direction}=last',
            f'targ v(vout) val={0.99*settings.vdd.voltage} {harness.out_direction}=last')
        results = sim.transient(step_time=(self.sim_timestep*settings.units.time), end_time=t['sim_end'])
        return results['t_stabilizing'] @ u_s

    def _find_setup_hold_delay(self, settings, harness, t_slew, c_load, t_stabilizing):
        """Calculate setup and hold time.

        Calculate the minimum setup and hold time for the current configuration, accounting for
        interdependence between the two. Uses the procedure proposed by Salman et. al.; See
        https://ieeexplore.ieee.org/document/4167994"""
        # Goal: Find two critical setup & hold delay pairs that approximate the c2q contour
        t_step = self.sim_timestep * settings.units.time

        # Use large hold time and sweep setup time to find ts_min
        th = max(self.hold_time_range) * settings.units.time
        ts_max = max(self.setup_time_range) * settings.units.time
        ts_min = min(self.setup_time_range) * settings.units.time
        ts = ts_max
        while ts - ts_min > 2*t_step: # Search until within 2 timesteps
            ts = (ts_max + ts_min) / 2
            sim, t = self._build_test_circuit(settings, harness, t_slew, c_load, ts, th, t_stabilizing)
            try:
                self._measure_c2q(settings, harness, sim, t)
            except NameError:
                ts_min = ts
                continue
            ts_max = ts
        t_setup_min = ts

        # Using t_setup = ts_min, sweep t_hold to find th_max
        th_max = max(self.hold_time_range) * settings.units.time
        th_min = min(self.hold_time_range) * settings.units.time
        th = th_max
        while th - th_min > 2*t_step: # Search until within 2 timesteps
            th = (th_max + th_min) / 2
            sim, t = self._build_test_circuit(settings, harness, t_slew, c_load, t_setup_min, th, t_stabilizing)
            try:
                self._measure_c2q(settings, harness, sim, t)
            except NameError:
                th_min = th
                continue
            th_max = th
        t_hold_max = th

        # Use large setup time and sweep hold time to find th_min
        ts = max(self.setup_time_range) * settings.units.time
        th_max = max(self.hold_time_range) * settings.units.time
        th_min = min(self.hold_time_range) * settings.units.time
        th = th_max
        while th - th_min > 2*t_step: # Search until within 2 timesteps
            th = (th_max + th_min) / 2
            sim, t = self._build_test_circuit(settings, harness, t_slew, c_load, ts, th, t_stabilizing)
            try:
                self._measure_c2q(settings, harness, sim, t)
            except NameError:
                th_min = th
                continue
            th_max = th
        t_hold_min = th

        # Using t_hold = th_min, sweep setup time to find ts_max
        ts_max = max(self.setup_time_range) * settings.units.time
        ts_min = min(self.setup_time_range) * settings.units.time
        ts = ts_max
        while ts - ts_min > 2*t_step: # Search until within 2 timesteps
            ts = (ts_max + ts_min) / 2
            sim, t = self._build_test_circuit(settings, harness, t_slew, c_load, ts, t_hold_min, t_stabilizing)
            try:
                self._measure_c2q(settings, harness, sim, t)
            except NameError:
                ts_min = ts
                continue
            ts_max = ts
        t_setup_max = ts

        return (t_setup_min, t_hold_max), (t_setup_max, t_hold_min) 

    def _build_test_circuit(self, settings, harness, t_slew, c_load, t_setup, t_hold, t_stabilizing):
        """Construct the circuit simulator object with the provided test parameters"""
        # Set up parameters
        clk_slew = self.clock_slew * settings.units.time
        vdd = settings.vdd.voltage * settings.units.voltage
        vss = settings.vss.voltage * settings.units.voltage

        # Set up timing parameters for clock and data events
        t = {}
        t['clk_edge_1_start'] = t_setup
        t['clk_edge_1_end'] = t['clk_edge_1_start'] + clk_slew
        t['clk_edge_2_start'] = t['clk_edge_1_end'] + max(t_setup, t_hold)
        t['clk_edge_2_end'] = t['clk_edge_2_start'] + clk_slew
        t['removal'] = t['clk_edge_2_end'] + t_hold # initial state has now been zeroed out
        t['data_edge_1_start'] = t['removal'] + t_stabilizing # wait for the system to stabilize
        t['data_edge_1_end'] = t['data_edge_1_start'] + t_slew
        t['clk_edge_3_start'] = t['data_edge_1_end'] + t_setup - (t_slew + clk_slew)/2
        t['clk_edge_3_end'] = t['clk_edge_3_start'] + clk_slew
        t['data_edge_2_start'] = t['clk_edge_3_end'] + t_hold - (t_slew + clk_slew)/2
        t['data_edge_2_end'] = t['data_edge_2_start'] + t_slew
        t['sim_end'] = t['data_edge_2_end'] + t_stabilizing # wait for the system to stabilize

        # Initialize circuit
        circuit = Circuit(self.cell.name)
        self._include_models(circuit)
        circuit.include(self.netlist)
        circuit.V('high', 'vhigh', circuit.gnd, vdd)
        circuit.V('low', 'vlow', circuit.gnd, vss)
        circuit.V('dd_dyn', 'vdd_dyn', circuit.gnd, vdd)
        circuit.V('ss_dyn', 'vss_dyn', circuit.gnd, vss)
        circuit.V('o_cap', 'vout', 'wout', 0)
        circuit.C('0', 'wout', 'vss_dyn', c_load)

        # Set up clock input
        (v0, v1) = (vss, vdd) if harness.timing_type_clock == 'falling_edge' else (vdd, vss)
        circuit.PieceWiseLinearVoltageSource('cin', 'vcin', circuit.gnd, values=[
            (0, v0),
            (t['clk_edge_1_start'], v0),
            (t['clk_edge_1_end'], v1),
            (t['clk_edge_2_start'], v1),
            (t['clk_edge_2_end'], v0),
            (t['clk_edge_3_start'], v0),
            (t['clk_edge_3_end'], v1),
            (t['sim_end'], v1)
        ])

        # Set up data input node
        (v0, v1) = (vss, vdd) if harness.in_direction == 'rise' else (vdd, vss)
        circuit.PieceWiseLinearVoltageSource('in', 'vin', circuit.gnd, values=[
            (0, v0),
            (t['data_edge_1_start'], v0),
            (t['data_edge_1_end'], v1),
            (t['data_edge_2_start'], v1),
            (t['data_edge_2_end'], v0),
            (t['sim_end'], v0)
        ])

        # Set up set and reset node
        if harness.reset:
            circuit.V('rin', 'vrin', circuit.gnd, vdd if harness.reset.state == '1' else vss)
        if harness.set:
            circuit.V('sin', 'vsin', circuit.gnd, vdd if harness.set.state == '1' else vss)

        # Initialize device under test subcircuit and wire up ports
        ports = self.definition().upper().split()[1:]
        connections = [ports.pop(0)]
        for port in ports:
            if port == harness.target_in_port.pin.name:
                connections.append('vin')
            elif port == harness.target_out_port.pin.name:
                connections.append('vout')
            elif port == settings.vdd.name.upper():
                connections.append('vdd_dyn')
            elif port == settings.vss.name.upper():
                connections.append('vss_dyn')
            elif port == harness.clock.pin.name:
                connections.append('vcin')
            elif self.reset and port == harness.reset.pin.name:
                connections.append('vrin')
            elif self.set and port == harness.set.pin.name:
                connections.append('vsin')
            elif port in [pin.pin.name for pin in harness.stable_in_ports]:
                for stable_port in harness.stable_in_ports:
                    if port == stable_port.pin.name:
                        if stable_port.state == '1':
                            connections.append('vhigh')
                        elif stable_port.state == '0':
                            connections.append('vlow')
                        else:
                            raise ValueError(f'Invalid state identified during simulation setup for port {port}: {state}')
            else:
                connections.append('wfloat0') # Float any unrecognized ports
        if len(connections) is not len(ports)+1:
            raise ValueError(f'Failed to match all ports identified in definition "{self.definition().strip()}"')
        circuit.X('dut', *connections)

        # Initialize simulator
        simulator = circuit.simulator(temperature=settings.temperature,
                                      nominal_temperature=settings.temperature,
                                      simulator=settings.simulator)
        simulator.options('autostop', 'nopage', 'nomod', post=1, ingold=2)
        return simulator, t

    def _measure_cell_delays(self, settings, harness, simulator, timings):
        """Run delay measurement for a single test circuit."""

        # Set up voltage bounds for measurements
        pct_vdd = lambda x : x * settings.vdd.voltage
        match harness.in_direction:
            case 'rise':
                v_prop_start = settings.logic_threshold_low_to_high
            case 'fall':
                v_prop_start = settings.logic_threshold_high_to_low
        match harness.out_direction:
            case 'rise':
                v_prop_end = settings.logic_threshold_low_to_high
                v_trans_start = settings.logic_threshold_low
                v_trans_end = settings.logic_threshold_high
            case 'fall':
                v_prop_end = settings.logic_threshold_high_to_low
                v_trans_start = settings.logic_threshold_high
                v_trans_end = settings.logic_threshold_low
        match harness.timing_type_clock:
            case 'rising_edge':
                clk_direction = 'rise'
                v_clk_transition = settings.logic_threshold_low_to_high
            case 'falling_edge':
                clk_direction = 'fall'
                v_clk_transition = settings.logic_threshold_high_to_low

        # Measure propagation delay from first data edge to last output edge
        simulator.measure('tran', 'prop_in_out',
            f'trig v(vin) val={pct_vdd(v_prop_start)} td={float(timings["removal"])} {harness.in_direction}=1',
            f'targ v(vout) val={pct_vdd(v_prop_end)} {harness.out_direction}=last')

        # Measure transient delay from first data edge to first output edge
        simulator.measure('tran', 'trans_out',
            f'trig v(vin) val={pct_vdd(v_trans_start)} td={float(timings["removal"])} {harness.in_direction}=1',
            f'targ v(vout) val={pct_vdd(v_trans_end)} {harness.out_direction}=1')

        # Measure setup delay from first data edge to last clock edge
        simulator.measure('tran', 't_setup',
            f'trig v(vin) val={pct_vdd(v_prop_start)} td={float(timings["removal"])} {harness.in_direction}=1',
            f'targ v(vcin) val={pct_vdd(v_clk_transition)} {clk_direction}=1')

        # Measure hold delay from last clock edge to last data edge
        simulator.measure('tran', 't_hold',
            f'trig v(vcin) val={pct_vdd(v_clk_transition)} td={float(timings["removal"])} {_flip_direction(clk_direction)}=last',
            f'targ v(vin) val={pct_vdd(v_prop_end)} {_flip_direction(harness.in_direction)}=1')

        return simulator.transient(
            step_time=(self.sim_timestep * settings.units.time),
            end_time=timings['sim_end'])

    def _measure_c2q(self, settings, harness, simulator, timings):
        """Measure Clock-to-Q delay."""

        # Measure clock-to-latch time
        match harness.timing_type_clock:
            case 'rising_edge':
                clk_direction = 'rise'
                v_clk_transition = settings.logic_threshold_low_to_high
            case 'falling_edge':
                clk_direction = 'fall'
                v_clk_transition = settings.logic_threshold_high_to_low
        match harness.out_direction:
            case 'rise':
                v_prop_end = settings.logic_threshold_low_to_high
            case 'fall':
                v_prop_end = settings.logic_threshold_high_to_low
        simulator.measure('tran', 't_c2q',
            f'trig v(vcin) val={pct_vdd(v_clk_transition)} td={float(timings["removal"])} {clk_direction}=last',
            f'targ v(vout) val={pct_vdd(v_prop_end)} {harness.out_direction}=last')

        return simulator.transient(
            step_time=(self.sim_timestep * settings.units.time),
            end_time=timings['sim_end'])

    def plot_io(self, settings, harness):
        """Plot I/O voltages vs time"""
        # TODO: Look for ways to generate fewer plots here - maybe a creative 3D plot
        figures = []
        # Group data by slew rate so that inputs are the same
        for slew in self.in_slews:
            for load in self.out_loads:
                # Add axes for clk, s, r, d, q (in that order)
                # Use an additive approach in case some of those aren't present
                num_axes = 1
                CLK = 0
                if self.set:
                    S = num_axes
                    num_axes += 1
                if self.reset:
                    R = num_axes
                    num_axes += 1
                D = num_axes
                num_axes += 1
                Q = num_axes
                num_axes += 1
                ratios = np.ones(num_axes).tolist()
                ratios[-1] = num_axes
                figure, axes = plt.subplots(num_axes,
                    sharex=True,
                    height_ratios=ratios,
                    label=f'{self.cell.name} | {harness.short_str()}'
                )

                # Set up plots
                for ax in axes:
                    for level in [settings.logic_threshold_low, settings.logic_threshold_high]:
                        ax.axhline(level*settings.vdd.voltage, color='0.5', linestyle='--')
                    # TODO: Set up vlines for important timing events
                    ax.set_yticks([settings.vss.voltage, settings.vdd.voltage])
                volt_units = str(settings.units.voltage.prefixed_unit)
                time_units = str(settings.units.time.prefixed_unit)
                axes[CLK].set(
                    title=f'Slew Rate: {str(slew*settings.units.time)} | Fanout: {str(load*settings.units.capacitance)}',
                    ylabel=f'CLK [{volt_units}]'
                )
                if self.set:
                    axes[S].set_ylabel(f'S [{volt_units}]')
                if self.reset:
                    axes[R].set_ylabel(f'R [{volt_units}]')
                axes[D].set_ylabel(f'D [{volt_units}]')
                axes[Q].set_ylabel(f'Q [{volt_units}]')
                axes[-1].set_xlabel(f'Time [{str(settings.units.time.prefixed_unit)}]')
                analysis = harness.results[str(slew)][str(load)]
                t = analysis.time / settings.units.time
                axes[CLK].plot(t, analysis.vcin)
                if self.set:
                    axes[S].plot(t, analysis.vsin)
                if self.reset:
                    axes[R].plot(t, analysis.vrin)
                axes[D].plot(t, analysis.vin)
                axes[Q].plot(t, analysis.vout)

                figures.append(figure)
        return figures

def _flip_direction(direction: str) -> str:
    return 'fall' if direction == 'rise' else 'rise'

def _gen_graycode(length: int):
    """Generate the list of Gray Codes of specified length"""
    if length <= 1:
        return [[0],[1]]
    inputs = []
    for j in _gen_graycode(length-1):
        j.insert(0, 0)
        inputs.append(j)
    for j in reversed(_gen_graycode(length-1)):
        j.insert(0, 1)
        inputs.append(j)
    return inputs

def _parse_triggered_pin(value: str, role: str) -> (str, Pin):
    """Parses input pin names with trigger types, e.g. 'posedge CLK'"""
    if not isinstance(value, str):
        raise TypeError(f'Invalid type for edge-triggered pin: {type(value)}')
    try:
        edge, name = value.split()
    except ValueError:
        raise ValueError(f'Invalid value for edge-triggered pin: {value}. Make sure you include both the trigger type and pin name (e.g. "posedge CLK")')
    if not edge in ['posedge', 'negedge']:
        raise ValueError(f'Invalid trigger type: {edge}. Trigger type must be one of "posedge" or "negedge"')
    return (edge, Pin(name, 'input', role))
