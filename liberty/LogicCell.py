import threading
from pathlib import Path

import characterizer.char_comb
import characterizer.char_seq
from characterizer.Harness import CombinationalHarness, SequentialHarness, filter_harnesses_by_ports, find_harness_by_arc, check_timing_sense
from characterizer.LogicParser import parse_logic

class LogicCell:
    def __init__ (self, name: str, in_ports: list, out_ports: list, functions: str, **kwargs):
        self.name = name            # cell name
        self.in_ports = in_ports    # input pin names
        self.out_ports = out_ports  # output pin names
        self.functions = functions  # cell functions

        # Documentation
        self.area = kwargs.get('area', 0) # cell area

        # Characterization settings
        self.harnesses = [] # list of lists of harnesses indexed by in_slews and out_loads
        self._netlist = kwargs.get('netlist')       # Cell spice netlist file
        self._model = kwargs.get('model')           # Cell transistor model file
        self._in_slews = kwargs.get('slews', [])    # input pin slew rates
        self._out_loads = kwargs.get('loads', [])   # output pin capacitive loads
        self._sim_timestep = 0
        if 'simulation_timestep' in kwargs.keys():
            self.sim_timestep = kwargs['simulation_timestep']
        self.stored_test_vectors = kwargs.get('test_vectors')

        # Behavioral settings
        self.plots = kwargs.get('plots', [])    # Which plots to generate for this cell
        self._is_exported = False               # whether the cell has been exported

    def __str__(self) -> str:
        lines = []
        lines.append(self.name)
        lines.append(f'    Inputs:              {", ".join(self.in_ports)}')
        lines.append(f'    Outputs:             {", ".join(self.out_ports)}')
        lines.append(f'    Functions:')
        for p,f in zip(self.out_ports,self.functions):
            lines.append(f'    {p}={f}')
        if self.area:
            lines.append(f'    Area:                {str(self.area)}')
        if self.netlist:
            lines.append(f'    Netlist:             {str(self.netlist)}')
            lines.append(f'    Definition:          {self.definition.rstrip()}')
            lines.append(f'    Instance:            {self.instance}')
        if self.in_slews:
            lines.append(f'    Input pin simulation slopes:')
            for slope in self.in_slews:
                lines.append(f'        {str(slope)}')
        if self.out_loads:
            lines.append(f'    Output pin simulation loads:')
            for load in self.out_loads:
                lines.append(f'        {str(load)}')
        lines.append(f'    Simulation timestep: {str(self.sim_timestep)}')
        if self.harnesses:
            lines.append(f'    Harnesses:')
            for harness in self.harnesses:
                [lines.append(f'        {h}') for h in str(harness).split('\n')]
        return '\n'.join(lines)

    def __repr__(self):
        return f'LogicCell({self.name},{self.in_ports},{self.out_ports},{self.functions},{self.area})'

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if isinstance(value, str):
            if len(value) > 0:
                self._name = str(value)
            else:
                raise ValueError(f'Empty string not allowed for cell name')
        else:
            raise TypeError(f'Invalid type for cell name: {type(value)}')

    @property
    def in_ports(self) -> list:
        return self._in_ports

    @in_ports.setter
    def in_ports(self, value):
        if isinstance(value, str):
            # Should be in the format "A B C"
            # TODO: add parsing for comma separated as well
            self._in_ports = value.split()
        elif isinstance(value, list):
            self._in_ports = value
        else:
            raise TypeError(f'Invalid type for in_ports: {type(value)}')

    @property
    def out_ports(self) -> list:
        return self._out_ports

    @out_ports.setter
    def out_ports(self, value):
        if isinstance(value, str):
            # Should be in the format "Y Z"
            # TODO: add parsing for comma separated as well
            self._out_ports = value.split()
        elif isinstance(value, list):
            self._out_ports = value
        else:
            raise TypeError(f'Invalid type for out_ports: {type(value)}')

    @property
    def functions(self) -> list:
        return self._functions

    @functions.setter
    def functions(self, value):
        if isinstance(value, list):
            # Should be in the format ['Y=expr1', 'Z=expr2']
            expressions = []
            for f in value:
                if '=' in f:
                    expr = f.split('=')[1:] # Discard LHS of equation
                    if parse_logic(''.join(expr)): # Make sure the expression is verilog
                        expressions.extend(expr)
                else:
                    raise ValueError(f'Expected an expression of the form "Y=A Z=B" for cell function, got "{value}"')
            self._functions = expressions
        elif isinstance(value, str) and '=' in value:
            self.functions = value.split() # Split on space and recurse to use the list setter
        else:
            raise TypeError(f'Invalid type for cell functions: {type(value)}')

    @property
    def area(self) -> float:
        return self._area

    @area.setter
    def area(self, value: float):
        if value is not None:
            self._area = float(value)
        else:
            raise TypeError(f'Invalid type for cell area: {type}')

    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self, value):
        if isinstance(value, Path):
            if not value.is_file():
                raise ValueError(f'Invalid value for model: {value} is not a file')
            else:
                self._model = value
        elif isinstance(value, str):
            if not Path(value).is_file():
                raise ValueError(f'Invalid value for model: {value} is not a file')
            else:
                self._model = value
        else:
            raise TypeError(f'Invalid type for model: {type(value)}')

    @property
    def netlist(self) -> str:
        return self._netlist

    @netlist.setter
    def netlist(self, value):
        if isinstance(value, Path):
            if not value.is_file():
                raise ValueError(f'Invalid value for netlist: {value} is not a file')
            self._netlist = value
        elif isinstance(value, str):
            if not Path(value).is_file():
                raise ValueError(f'Invalid value for netlist: {value} is not a file')
            self._netlist = Path(value)
        else:
            raise TypeError(f'Invalid type for netlist: {type(value)}')

    @property
    def definition(self) -> str:
        # Search the netlist file for the circuit definition
        with open(self.netlist, 'r') as f:
            for line in f:
                if self.name.lower() in line.lower() and 'subckt' in line.lower():
                    f.close()
                    return line
            # If we reach this line before returning, the netlist file doesn't contain a circuit definition
            f.close()
            raise ValueError(f'No cell definition found in netlist {self.netlist}')

    @property
    def instance(self) -> str:
        # Reorganize the definition into an instantiation with instance name XDUT
        # TODO: Instance name should probably be configurable from library settings
        instance = self.definition.split()[1:]  # Delete .subckt
        instance.append(instance.pop(0))        # Move circuit name to last element
        instance.insert(0, 'XDUT')              # Insert instance name
        return ' '.join(instance)

    @property
    def in_slews(self) -> list:
        return self._in_slews

    def add_in_slew(self, value: float):
        self._in_slews.append(float(value))

    @property
    def out_loads(self) -> list:
        return self._out_loads

    def add_out_load(self, value: float):
        self._out_loads.append(float(value))

    @property
    def plots(self) -> list:
        return self._plots
    
    @plots.setter
    def plots(self, value):
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
        return self._is_exported

    def set_exported(self):
        self._is_exported = True

    @property
    def sim_timestep(self):
        return self._sim_timestep

    @sim_timestep.setter
    def sim_timestep(self, value):
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
    
    def _gen_graycode(self, n: int):
        """Generate the list of Gray Codes for length n"""
        if n <= 1:
            return [[0],[1]]
        inputs = []
        for j in self._gen_graycode(n-1):
            j.insert(0, 0)
            inputs.append(j)
        for j in reversed(self._gen_graycode(n-1)):
            j.insert(0, 1)
            inputs.append(j)
        return inputs

    @property
    def test_vectors(self) -> list:
        """Generate a list of test vectors from this cell's functions"""
        # TODO: Determine whether this will actually work for sequential cells, or only combinational cells
        # 
        # Note that this uses "brute force" methods to determine test vectors. It also tests far
        # more vectors than necessary, lengthening simulation times.
        # A smarter approach would be to parse the function for each output, determine potential
        # critical paths, and then test only those paths to determine worst-case delays.
        # 
        # Revisiting this: we actually can't know critical path just from the function, as the
        # given function may not match up with hardware implementation in terms of operation order.
        # We have to evaluate all potential masking conditions and determine critical paths
        # afterwards.
        # 
        # Revisiting this again: While we can't know critical paths from the information given, we
        # could provide tools to let users tell us which conditions reveal the critical path.
        # Consider adding an option to let users provide critical path nonmasking conditions.
        if self.stored_test_vectors:
            return self.stored_test_vectors
        else:
            test_vectors = []
            values = self._gen_graycode(len(self.in_ports))
            for out_index in range(len(self.out_ports)):
                # Assemble a callable function corresponding to this output port's function
                f = eval(f'lambda {",".join(self.in_ports)} : int({self.functions[out_index].replace("~", "not ")})')
                for j in range(len(values)):
                    # Evaluate f at the last two values and see if the output changes
                    x0 = values[j-1]
                    x1 = values[j]
                    y0 = f(*x0)
                    y1 = f(*x1)
                    if not y1 == y0:
                        # If the output differs, we can use these two vectors to test the input at the index where they differ
                        in_index = [k for k in range(len(x1)) if x0[k] != x1[k]][0] # If there is more than 1 element here, we have a problem with our gray coding
                        # Add two test vectors: one for rising and one for falling
                        # Generate the first test vector
                        test_vector = [str(e) for e in x1]
                        test_vector[in_index] = f'{x0[in_index]}{x1[in_index]}'
                        for n in range(len(self.out_ports)):
                            test_vector.append(f'{y0}{y1}' if n == out_index else '0')
                        test_vectors.append(test_vector)
                        # Generate the second test vector
                        test_vector = [str(e) for e in x0]
                        test_vector[in_index] = f'{x1[in_index]}{x0[in_index]}'
                        for n in range(len(self.out_ports)):
                            test_vector.append(f'{y1}{y0}' if n == out_index else '0')
                        test_vectors.append(test_vector)
            return test_vectors

    def get_input_capacitance(self, in_port, vdd_voltage, capacitance_unit):
        """Average input capacitance measured by all harnesses that target this input port"""
        if in_port not in self.in_ports:
            raise ValueError(f'Unrecognized input port {in_port}')
        input_capacitance = 0
        n = 0
        for harness in self.harnesses:
            if harness.target_in_port == in_port:
                input_capacitance += harness.average_input_capacitance(vdd_voltage, capacitance_unit)
                n += 1
        return input_capacitance / n

class CombinationalCell(LogicCell):
    def __init__(self, name: str, in_ports: list, out_ports: list, functions: str, **kwargs):
        super().__init__(name, in_ports, out_ports, functions, **kwargs)

    def characterize(self, settings):
        """Run delay characterization for an N-input M-output combinational cell"""
        # Run delay simulation for all test vectors
        unsorted_harnesses = []
        for test_vector in self.test_vectors:
            # Generate harness
            harness = CombinationalHarness(self, test_vector)
            # Determine spice filename prefix
            spice_prefix = f'{settings.work_dir}/delay_{self.name}_{harness.spice_infix()}'
            # Run delay characterization
            if settings.use_multithreaded:
                # Split simulation jobs into threads and run multiple simultaneously
                thread_id = 0
                threadlist = []
                for tmp_slope in self.in_slews:
                    for tmp_load in self.out_loads:
                        thread = threading.Thread(target=characterizer.char_comb.runCombinationalDelay,
                                args=([settings, self, harness, spice_prefix, tmp_slope, tmp_load]),
                                name="%d" % thread_id)
                        threadlist.append(thread)
                        thread_id += 1
                [thread.start() for thread in threadlist]
                [thread.join() for thread in threadlist]
            else:
                # Run simulation jobs sequentially
                for in_slew in self.in_slews:
                    for out_load in self.out_loads:
                        characterizer.char_comb.runCombinationalDelay(settings, self, harness, spice_prefix, in_slew, out_load)
            # Save harness to the cell
            unsorted_harnesses.append(harness)
        # Filter and sort harnesses
        # The result should be:
        # - For each input-output path:
        #   - 1 harness for the critical path rising case
        #   - 1 harness for the critical path falling case
        for output in self.out_ports:
            for input in self.in_ports:
                for direction in ['rise', 'fall']:
                    # Iterate over harnesses that match output, input, and direction
                    harnesses = [harness for harness in filter_harnesses_by_ports(unsorted_harnesses, input, output) if harness.out_direction == direction]
                    worst_case_harness = harnesses[0]
                    for harness in harnesses:
                        if worst_case_harness.average_propagation_delay() < harness.average_propagation_delay():
                            worst_case_harness = harness # This harness is worse
                    self.harnesses.append(worst_case_harness)

    def export(self, settings):
        cell_lib = [
            f'cell ({self.name}) {{',
            f'  area : {self.area};',
            f'  cell_leakage_power : {self.harnesses[0].get_leakage_power(settings.vdd.voltage, settings.units.power):.7f};', # TODO: Check whether we should use the 1st
        ]
        # Input ports
        for in_port in self.in_ports:
            cell_lib.extend([
                f'  pin ({in_port}) {{',
                f'    direction : input;',
                f'    capacitance : {self.get_input_capacitance(in_port, settings.vdd.voltage, settings.units.capacitance):.7f};',
                f'    rise_capacitance : 0;', # TODO: calculate this (average over harnesses?)
                f'    fall_capacitance : 0;', # TODO: calculate this (average over harnesses?)
                f'  }}', # end pin
            ])
        # Output ports and functions
        for out_port in self.out_ports:
            cell_lib.extend([
                f'  pin ({out_port}) {{',
                f'    direction : output;',
                f'    capacitance : 0;', # Matches OSU350_reference, but may not be correct. TODO: Check
                f'    rise_capacitance : 0;', # Matches OSU350_reference, but may not be correct. TODO: Check
                f'    fall_capacitance : 0;', # Matches OSU350_reference, but may not be correct. TODO: Check
                f'    max_capacitance : {max(self.out_loads):.7f};', # TODO: Calculate (average?)
                f'    function : "{self.functions[self.out_ports.index(out_port)]}";'
            ])
            # Timing
            for in_port in self.in_ports:
                # Fetch harnesses which target this in_port/out_port combination
                harnesses = filter_harnesses_by_ports(self.harnesses, in_port, out_port)
                cell_lib.extend([
                    f'    timing () {{',
                    f'      related_pin : {in_port}',
                    f'      timing_sense : {check_timing_sense(harnesses)}',
                ])
                for direction in ['rise', 'fall']:
                    harness = find_harness_by_arc(self.harnesses, in_port, out_port, direction)
                    # Propagation delay
                    cell_lib.append(f'      {harness.direction_prop} (delay_template_{len(self.in_slews)}x{len(self.out_loads)}) {{')
                    for line in harness.get_propagation_delay_lut(self.in_slews, self.out_loads, settings.units.time):
                        cell_lib.append(f'        {line}')
                    cell_lib.append(f'      }}') # end cell_rise/fall LUT
                    # Transition delay
                    cell_lib.append(f'      {harness.direction_tran} (delay_template_{len(self.in_slews)}x{len(self.out_loads)}) {{')
                    for line in harness.get_transport_delay_lut(self.in_slews, self.out_loads, settings.units.time):
                        cell_lib.append(f'        {line}')
                    cell_lib.append(f'      }}') # end rise/fall_transition LUT
                cell_lib.append(f'    }}') # end timing
            # Internal power
            for in_port in self.in_ports:
                # Fetch harnesses which target this in_port/out_port combination
                harnesses = filter_harnesses_by_ports(self.harnesses, in_port, out_port)
                cell_lib.extend([
                    f'    internal_power () {{',
                    f'      related_pin : "{in_port}"',
                ])
                for direction in ['rise', 'fall']:
                    harness = find_harness_by_arc(self.harnesses, in_port, out_port, direction)
                    cell_lib.append(f'      {harness.direction_power} (energy_template_{len(self.in_slews)}x{len(self.out_loads)}) {{')
                    for line in harness.get_internal_energy_lut(self.in_slews, self.out_loads, settings.energy_meas_high_threshold_voltage(), settings.units.energy, settings.units.current):
                        cell_lib.append(f'        {line}')
                    cell_lib.append(f'      }}') # end rise/fall_power LUT
                cell_lib.append(f'    }}') # end internal power
            cell_lib.append(f'  }}') # end pin
        cell_lib.append(f'}}') # end cell
        return '\n'.join(cell_lib)

class SequentialCell(LogicCell):
    def __init__(self, name: str, in_ports: list, out_ports: list, clock_pin: str, flops: str, function: str, **kwargs):
        super().__init__(name, in_ports, out_ports, function, **kwargs)
        self.set = kwargs.get('set_pin')        # set pin name
        self.reset = kwargs.get('reset_pin')    # reset pin name
        self.clock = clock_pin                  # clock pin name
        self.flops = flops                      # registers
        
        self._clock_slew = 0
        if 'clock_slew' in kwargs.keys():
            self.clock_slew = kwargs['clock_slew']

        self._sim_setup_highest = 0
        self._sim_setup_lowest = 0
        self._sim_setup_timestep = 0
        self._sim_hold_highest = 0
        self._sim_hold_lowest = 0
        self._sim_hold_timestep = 0
        if 'simulation' in kwargs.keys():
            sim = kwargs['simulation']
            if 'setup' in sim.keys():
                setup = sim['setup']
                self.sim_setup_highest = setup.get('highest')
                self.sim_setup_lowest = setup.get('lowest')
                self.sim_setup_timestep = setup.get('timestep')
            if 'hold' in sim.keys():
                hold = sim['hold']
                self.sim_hold_highest = hold.get('highest')
                self.sim_hold_lowest = hold.get('lowest')
                self.sim_hold_timestep = hold.get('timestep')

    def __str__(self) -> str:
        lines = super().__str__().split('\n')
        function_line_index = lambda : lines.index(next([line for line in lines if line.startswith('Functions:')]))
        # Insert pin names before functions line
        if self.clock:
            lines.insert(function_line_index, f'Clock pin:           {self.clock}')
        if self.set:
            lines.insert(function_line_index, f'Set pin:             {self.set}')
        if self.reset:
            lines.insert(function_line_index, f'Reset pin:           {self.reset}')
        if self.flops:
            lines.insert(function_line_index, f'Registers:           {", ".join(self.flops)}')

    def __repr__(self):
        return f'SequentialCell({self.name},{self.in_ports},{self.out_ports},{self.clock},{self.set},{self.reset},{self.flops},{self.functions},{self. area})'

    @property
    def clock(self) -> str:
        return self._clock
    
    @clock.setter
    def clock(self, value):
        if not isinstance(value, str):
            raise TypeError(f'Invalid type for cell clock pin: {type(value)}')
        else:
            self._clock = value

    @property
    def set(self) -> str:
        return self._set

    @set.setter
    def set(self, value):
        self._set = str(value) if value else None

    @property
    def reset(self) -> str:
        return self._reset

    @reset.setter
    def reset(self, value):
        self._reset = str(value) if value else None

    @property
    def flops(self) -> list:
        return self._flops

    @flops.setter
    def flops(self, value):
        if isinstance(value, str):
            self._flops = value.split()
        elif isinstance(value, list):
            self._flops = value
        else:
            raise TypeError(f'Invalid type for sequential cell flop names: {type(value)}')

    @property
    def clock_slew(self) -> float:
        return self._clock_slew

    @clock_slew.setter
    def clock_slew(self, value):
        if isinstance(value, (int, float)):
            if value > 0:
                self._clock_slew = float(value)
            else:
                raise ValueError('Clock slew rate must be greater than zero')
        elif value == 'auto':
            if not self.in_slews:
                raise ValueError('Cannot use auto clock slew rate unless in_slews is set first!')
            else:
                # Use minimum slew rate
                self._clock_slew = min(self._in_slews)
        else:
            raise TypeError(f'Invalid type for clock slew rate: {type(value)}')

    @property
    def sim_setup_lowest(self) -> float:
        return self._sim_setup_lowest

    @sim_setup_lowest.setter
    def sim_setup_lowest(self, value):
        if isinstance(value, (int, float)):
            if value > 0:
                self._sim_setup_lowest = float(value)
            else:
                raise ValueError('sim_setup_lowest must be greater than zero')
        elif value == 'auto':
            if not self.in_slews:
                raise ValueError('Cannot use auto for sim_setup_lowest unless in_slews is set first!')
            else:
                # Use -10 * max input slew rate
                self._sim_setup_lowest = max(self.in_slews) * -10.0
        else:
            raise TypeError(f'Invalid type for sim_setup_lowest: {type(value)}')

    @property
    def sim_setup_highest(self) -> float:
        return self._sim_setup_highest

    @sim_setup_highest.setter
    def sim_setup_highest(self, value):
        if isinstance(value, (int, float)):
            if value > 0:
                self._sim_setup_highest = float(value)
            else:
                raise ValueError('sim_setup_highest must be greater than zero')
        elif value == 'auto':
            if not self.in_slews:
                raise ValueError('Cannot use auto for sim_setup_highest unless in_slews is set first!')
            else:
                # Use 10 * max input slew rate
                self._sim_setup_highest = max(self.in_slews) * 10.0
        else:
            raise TypeError(f'Invalid type for sim_setup_highest: {type(value)}')

    @property
    def sim_setup_timestep(self) -> float:
        return self._sim_setup_timestep

    @sim_setup_timestep.setter
    def sim_setup_timestep(self, value):
        if isinstance(value, (int, float)):
            if value > 0:
                self._sim_setup_timestep = float(value)
            else:
                raise ValueError('sim_hold_timestep must be greater than zero')
        elif value == 'auto':
            if self.in_slews:
                # 1st preference: 1/10th of minimum slew rate
                self._sim_setup_timestep = min(self.in_slews)/10.0
            else:
                # Otherwise, use sim timestep
                self._sim_setup_timestep = self.sim_timestep
        else:
            raise TypeError(f'Invalid type for sim_setup_timestamp: {type(value)}')

    @property
    def sim_hold_lowest(self) -> float:
        return self._sim_hold_lowest

    @sim_hold_lowest.setter
    def sim_hold_lowest(self, value):
        if isinstance(value, (int, float)):
            if value > 0:
                self._sim_hold_lowest = float(value)
            else:
                raise ValueError('sim_hold_lowest must be greater than zero')
        elif value == 'auto':
            if self.in_slews:
                # Use -10 * min slew rate
                self._sim_hold_lowest = min(self.in_slews) * -10.0
            else:
                raise ValueError('Cannot use auto for sim_hold_lowest unless in_slews is set first!')
        else:
            raise TypeError(f'Invalid type for sim_hold_lowest: {type(value)}')

    @property
    def sim_hold_highest(self) -> float:
        return self._sim_hold_highest

    @sim_hold_highest.setter
    def sim_hold_highest(self, value):
        if isinstance(value, (int, float)):
            if value > 0:
                self._sim_hold_highest = float(value)
            else:
                raise ValueError('sim_hold_highest must be greater than zero')
        elif value == 'auto':
            if self.in_slews:
                # Use 10 * max slew rate
                self._sim_hold_lowest = max(self.in_slews) * 10.0
            else:
                raise ValueError('Cannot use auto for sim_hold_highest unless in_slews is set first!')
        else:
            raise TypeError(f'Invalid type for sim_hold_highest: {type(value)}')

    @property
    def sim_hold_timestep(self) -> float:
        return self._sim_hold_timestep

    @sim_hold_timestep.setter
    def sim_hold_timestep(self, value):
        if isinstance(value, (int, float)):
            if value > 0:
                self._sim_hold_timestep = float(value)
            else:
                raise ValueError('sim_hold_timestep must be greater than zero')
        elif value == 'auto':
            if self.in_slews:
                # 1st preference: 1/10th of minimum slew rate
                self._sim_hold_timestep = min(self.in_slews)/10.0
            else:
                # Otherwise, use sim timestep
                self._sim_hold_timestep = self.sim_timestep
        else:
            raise TypeError(f'Invalid type for sim_setup_timestamp: {type(value)}')

    def characterize(self, settings):
        """Run Delay, Recovery & Removal characterization for a sequential cell"""
        unsorted_harnesses = []
        for test_vector in self.test_vectors:
            # Generate harness
            harness = SequentialHarness(self, test_vector)
            # Generate spice filename
            spice_prefix = f'{settings.work_dir}/_{self.name}_{harness.spice_infix()}'
            # Run simulation
            characterizer.char_seq.runSequential(settings, self, harness, spice_prefix)
            # Add harness to collection after characterization
            unsorted_harnesses.append(harness)
        # Filter and sort harnesses
        # For clock:
        # - No harnesses TODO: Add clock energy calculations (this will require at least 1 harness)
        # For each input-output path:
        # - 1 harness for setup_rising/falling
        # - 1 harness for hold_rising/falling
        # For each output port:
        # - 2 harnesses characterizing path from clock to output: rise and fall
        # - 1 harness characterizing path from reset to output
        # - 1 harness characterizing path from set to output
        # For reset:
        # - 1 harness for clock to reset recovery_rising/falling
        # - 1 harness for set to reset recovery_rising/falling
        # - 1 harness for clock to reset removal_rising/falling
        # For set:


    def export(self, settings):
        cell_lib = [
            f'cell ({self.name}) {{',
            f'  area : {self.area};',
            f'  cell_leakage_power : {self.harnesses[0].get_leakage_power(settings.vdd.voltage, settings.units.power):.7f};', # TODO: Check whether we should use the 1st
        ]
        # Flip Flop (single flop supported per cell)
        # TODO: This is not a very flexible way to store flops, and should be improved in the future
        cell_lib.append(f'  ff ({",".join(self.flops)}) {{')
        for in_port in self.in_ports:
            cell_lib.append(f'    next_state : "{in_port}";')
        cell_lib.append(f'    clocked_on : "{self.clock}";')
        if self.reset:
            cell_lib.append(f'    clear : "{self.reset}";')
        if self.set:
            cell_lib.append(f'    preset : "{self.set}";')
        if self.reset:
            cell_lib.append(f'    clear_preset_var1: L;') # Hard-coded value for when set and reset are both active
            cell_lib.append(f'    clear_preset_var2: L;')
        cell_lib.append(f'  }}') # end ff
        # Clock and Input ports
        for in_port in [self.clock, *self.in_ports]:
            cell_lib.extend([
                f'  pin ({in_port}) {{',
                f'    direction : input;',
                f'    capacitance : {self.get_input_capacitance(in_port, settings.vdd.voltage, settings.units.capacitance):.7f};',
                f'    rise_capacitance : 0;', # TODO: Calculate this
                f'    fall_capacitance : 0;', # TODO: Calculate this
            ])
            # Timing
            if in_port is self.clock:
                cell_lib.append(f'    clock : true;')
            elif in_port in self.in_ports:
                for out_port in self.out_ports:
                    harnesses = filter_harnesses_by_ports(self.harnesses, in_port, out_port)
                    # TODO: Fetch harnesses for setup and hold timing
                    # TODO: Figure out which harnesses to use here (one for setup, one for hold)
                    for harness in harnesses:
                        cell_lib.extend([
                            f'    timing () {{',
                            f'      related_pin : "{self.clock}";',
                            f'      timing_type : "{harness.timing_type}";',
                            f'      when : "TODO";', # TODO
                            f'      sdf_cond : "TODO";', # TODO
                            f'      /* TODO: add rise_constraint and fall_constraint LUTs */', # TODO
                        ])
                        cell_lib.append(f'    }}') # end timing
            # Internal power
            cell_lib.extend([
                f'    internal_power () {{',
                f'      /* TODO: add rise_power and fall_power LUTs */', # TODO
            ])
            cell_lib.append(f'    }}') # end internal_power
            # Clock pulse widths
            if in_port is self.clock:
                cell_lib.extend([
                    f'    min_pulse_width_high : 0;', # TODO
                    f'    min_pulse_width_low : 0;', # TODO
            ])
            cell_lib.append(f'  }}') # end pin
        # Output ports
        for out_port in self.out_ports:
            cell_lib.extend([
                f'  pin ({out_port}) {{',
                f'    direction : output;',
                f'    capacitance : 0;', # Matches OSU350_reference, but may not be correct. TODO: Check
                f'    rise_capacitance : 0;', # Matches OSU350_reference, but may not be correct. TODO: Check
                f'    fall_capacitance : 0;', # Matches OSU350_reference, but may not be correct. TODO: Check
                f'    max_capacitance : {max(self.out_loads):.7f};', # TODO: Check (or actually calculate this)
                f'    function : "{self.functions[self.out_ports.index(out_port)]}";'
            ])
            # Timing and internal power
            related_ports = [self.clock]
            if self.reset: related_ports.append(self.reset)
            if self.set: related_ports.append(self.set)
            for related_port in related_ports:
                # TODO: Figure out how to properly fetch the right harnesses for this
                harnesses = filter_harnesses_by_ports(self.harnesses, related_port, out_port)
                # Timing
                cell_lib.extend([
                    f'    timing () {{',
                    f'      related_pin : "{related_port}";',
                    f'      timing_sense : "{check_timing_sense(harnesses)}";',
                    f'      timing_type : "{harness[0].timing_type}"'
                ])
                # TODO: add cell_rise, rise_transition, cell_fall, and fall_transition (as appropriate)
                cell_lib.append(f'    }}') # end timing
                # Internal power
                cell_lib.extend([
                    f'    internal_power () {{',
                    f'      related_pin : "{related_port}";',
                ])
                # TODO: Add rise_power/fall_power/power (as appropriate)
                cell_lib.append(f'    }}')
            cell_lib.append(f'  }}') # end pin
        # Reset port
        if self.reset:
            cell_lib.extend([
                f'  pin ({self.reset}) {{',
                f'    direction : input;',
                f'    capacitance : 0;', # TODO: Calculate this
                f'    rise_capacitance : 0;', # TODO: Calculate this
                f'    fall_capacitance : 0;', # TODO: Calculate this
                f'    min_pulse_width_low : 0;' # TODO
            ])
            # TODO: Filter harnesses to get recovery for CLK and S, and removal for CLK
            for harness in self.harnesses: # TODO: Change from self.harnesses (as indicated above)
                cell_lib.extend([
                    f'    timing () {{',
                    f'      related_pin : "{harness.target_in_port}";',
                    f'      timing_type : {harness.timing_type};',
                    f'      when : "TODO";', # TODO
                    f'      sdf_cond : "TODO";', # TODO
                    f'      /* TODO: add rise_constraint LUT */'
                ])
                cell_lib.append(f'    }}') # end timing
            cell_lib.append(f'  }}') # end pin
        # Set port
        if self.set:
            cell_lib.extend([
                f'  pin ({self.reset}) {{',
                f'    direction : input;',
                f'    capacitance : 0;', # TODO: Calculate this
                f'    rise_capacitance : 0;', # TODO: Calculate this
                f'    fall_capacitance : 0;', # TODO: Calculate this
                f'    min_pulse_width_low : 0;' # TODO
            ])
            # TODO: Filter harnesses to get recovery for CLK and R, and removal for CLK
            for harness in self.harnesses: # TODO: Change from self.harnesses (as indicated above)
                cell_lib.extend([
                    f'    timing () {{',
                    f'      related_pin : "{harness.target_in_port}";',
                    f'      timing_type : {harness.timing_type};',
                    f'      when : "TODO";', # TODO
                    f'      sdf_cond : "TODO";', # TODO
                    f'      /* TODO: add rise_constraint LUT */'
                ])
                cell_lib.append(f'    }}') # end timing
            cell_lib.append(f'  }}') # end pin
        cell_lib.append(f'}}') # end cell