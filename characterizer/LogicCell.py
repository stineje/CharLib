import threading
from pathlib import Path

import characterizer.char_comb
import characterizer.char_seq
from characterizer.Harness import CombinationalHarness, SequentialHarness
from characterizer.LibrarySettings import LibrarySettings
from characterizer.LogicParser import parse_logic

class LogicCell:
    def __init__ (self, name: str, in_ports: list, out_ports: list, functions: str, area: float = 0):
        self.name = name            # cell name
        self.in_ports = in_ports    # input pin names
        self.out_ports = out_ports  # output pin names
        self.functions = functions  # cell functions

        # Documentation
        self.area = area        # cell area

        # Characterization settings
        self._netlist = None    # cell netlist
        self._model = None      # cell model definition
        self._definition = None # cell definition (from netlist)
        self._instance = None   # cell instance name
        self._in_slews = []     # input pin slew rates for characterization
        self._out_loads = []    # output pin capacitance loads for characterization
        self._sim_timestep = 0  # simulation timestep

        # From characterization results
        self.harnesses = []     # list of lists of harnesses indexed by in_slews and out_loads

        # Behavioral settings
        self._is_exported = False   # whether the cell has been exported

    def __str__(self) -> str:
        lines = []
        lines.append(f'Cell name:           {self.name}')
        lines.append(f'Inputs:              {", ".join(self.in_ports)}')
        lines.append(f'Outputs:             {", ".join(self.out_ports)}')
        lines.append(f'Functions:')
        for p,f in zip(self.out_ports,self.functions):
            lines.append(f'    {p}={f}')
        if self.area:
            lines.append(f'Area:                {str(self.area)}')
        if self.netlist:
            lines.append(f'Netlist:             {str(self.netlist)}')
            lines.append(f'Definition:          {self.definition.rstrip()}')
            lines.append(f'Instance:            {self.instance}')
        if self.in_slews:
            lines.append(f'Input pin simulation slopes:')
            for slope in self.in_slews:
                lines.append(f'    {str(slope)}')
        if self.out_loads:
            lines.append(f'Output pin simulation loads:')
            for load in self.out_loads:
                lines.append(f'    {str(load)}')
        lines.append(f'Simulation timestep: {str(self.sim_timestep)}')
        if self.harnesses:
            lines.append(f'Harnesses:')
            for harness in self.harnesses:
                lines.append(f'    {str(harness)}')
        return '\n'.join(lines)

    def __repr__(self):
        return f'LogicCell({self.name},{self.in_ports},{self.out_ports},{self.functions},{self.area})'

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if value is not None and len(value) > 0:
            self._name = str(value)
        else:
            raise ValueError(f'Invalid value for cell name: {value}')

    @property
    def in_ports(self) -> list:
        return self._in_ports

    @in_ports.setter
    def in_ports(self, value):
        if value is not None:
            if isinstance(value, str):
                # Should be in the format "A B C"
                # TODO: add parsing for comma separated as well
                self._in_ports = value.split()
            elif isinstance(value, list):
                self._in_ports = value
            else:
                raise TypeError(f'Invalid type for in_ports: {type(value)}')
        else:
            raise ValueError(f'Invalid value for in_ports: {value}')

    @property
    def out_ports(self) -> list:
        return self._out_ports

    @out_ports.setter
    def out_ports(self, value):
        if value is not None:
            if isinstance(value, str):
                # Should be in the format "Y Z"
                # TODO: add parsing for comma separated as well
                self._out_ports = value.split()
            elif isinstance(value, list):
                self._out_ports = value
            else:
                raise TypeError(f'Invalid type for out_ports: {type(value)}')
        else:
            raise ValueError(f'Invalid value for out_ports: {value}')

    @property
    def functions(self) -> list:
        return self._functions

    @functions.setter
    def functions(self, value):
        if value is not None:
            if isinstance(value, list):
                self._functions = value
            elif isinstance(value, str) and '=' in value:
                # Should be in the format "Y=expr1 Y=expr2"
                expressions = []
                for f in value.split():
                    if '=' in f:
                        expr = f.split('=')[1:] # Discard LHS of equation
                        if parse_logic(''.join(expr)): # Make sure the expression is verilog
                            expressions.extend(expr)
                    else:
                        raise ValueError(f'Expected an expression of the form "Y=A Z=B" for cell function, got "{value}"')
                self._functions = expressions
            else:
                raise TypeError(f'Invalid type for cell functions: {type(value)}')
        else:
            raise ValueError(f'Invalid value for cell functions: {value}')

    @property
    def area(self) -> float:
        return self._area

    @area.setter
    def area(self, value: float):
        if value is not None:
            self._area = float(value)
        else:
            raise ValueError(f'Invalid value for cell area: {value}')

    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self, value):
        if value is not None:
            if isinstance(value, Path):
                if not value.is_file():
                    raise ValueError(f'Invalid value for model: {value} is not a file')
                self._model = value
            elif isinstance(value, str):
                if not Path(value).is_file():
                    raise ValueError(f'Invalid value for model: {value} is not a file')
                self._model = value
            else:
                raise TypeError(f'Invalid type for model: {type(value)}')
        else:
            raise ValueError(f'Invalid value for model: {value}')

    @property
    def netlist(self) -> str:
        return self._netlist

    @netlist.setter
    def netlist(self, value):
        if value is not None:
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
            # netlist is now set - update definition
            with open(self.netlist, 'r') as netfile:
                for line in netfile:
                    if self.name.lower() in line.lower() and '.subckt' in line.lower():
                        self.definition = line
                netfile.close()
            if self.definition is None:
                raise ValueError(f'No cell definition found in netlist {value}')
        else:
            raise ValueError(f'Invalid value for netlist: {value}')

    @property
    def definition(self) -> str:
        return self._definition

    @definition.setter
    def definition(self, value: str):
        if value is not None:
            if self.name.lower() not in value.lower():
                raise ValueError(f'Cell name not found in cell definition: {value}')
            elif '.subckt' not in value.lower():
                raise ValueError(f'".subckt" not found in cell definition: {value}')
            else:
                self._definition = value
            # definition is now set - update instance
            circuit_call = value.split()[1:]            # Delete .subckt
            circuit_call.append(circuit_call.pop(0))    # Move circuit name to last element
            circuit_call.insert(0, 'XDUT')              # Insert instance name
            self.instance = ' '.join(circuit_call)
        else:
            raise ValueError(f'Invalid value for cell definiton: {value}')

    @property
    def instance(self) -> str:
        return self._instance

    @instance.setter
    def instance(self, value: str):
        if value is not None:
            self._instance = value
        else:
            raise ValueError(f'Invalid value for instance: {value}')

    @property
    def in_slews(self) -> list:
        return self._in_slews

    def add_in_slew(self, value: float):
        if value is not None:
            self._in_slews.append(float(value))
        else:
            raise ValueError(f'Invalid value for input pin slope: {value}')

    @property
    def out_loads(self) -> list:
        return self._out_loads

    def add_out_load(self, value: float):
        if value is not None:
            self._out_loads.append(float(value))
        else:
            raise ValueError(f'Invalid value for output pin load: {value}')

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
        if value is not None:
            if value == 'auto' and self.in_slews:
                # Use 1/10th of minimum slew rate
                self._sim_timestep = min(self.in_slews)/10.0
            else:
                self._sim_timestep = float(value)
        else:
            raise ValueError(f'Invalid value for sim_timestep: {value}')
    
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
        # Note that this uses "brute force" methods to determine test vectors. It also tests far
        # more vectors than necessary, lengthening simulation times.
        # A smarter approach would be to parse the function for each output, determine potential
        # critical paths, and then test only those paths to determine worst-case delays.
        test_vectors = []
        values = self._gen_graycode(len(self.in_ports))
        for i in range(len(self.out_ports)):
            # Assemble a callable function corresponding to this output port's function
            f = eval(f'lambda {",".join(self.in_ports)} : {self.functions[i]}')
            for j in range(len(values)):
                # Evaluate f at the last two values and see if the output changes
                x0 = values[j-1]
                x = values[j]
                y0 = f(*x0)
                y = f(*x)
                if not y == y0:
                    # If the output differs, we can use these two vectors to test the input at the index where they differ
                    index = [k for k in range(len(x)) if x0[k] != x[k]][0] # If there is more than 1 element here, we have a problem with our gray coding
                    # Add two test vectors: one for rising and one for falling
                    # Generate the first test vector
                    test_vector = [str(e) for e in x]
                    test_vector[index] = f'{x0[index]}{x[index]}'
                    for n in range(len(self.out_ports)):
                        test_vector.append(f'{y0}{y}' if n == i else '0')
                    test_vectors.append(test_vector)
                    # Generate the second test vector
                    test_vector = [str(e) for e in x0]
                    test_vector[index] = f'{x[index]}{x0[index]}'
                    for n in range(len(self.out_ports)):
                        test_vector.append(f'{y}{y0}' if n == i else '0')
                    test_vectors.append(test_vector)
        return test_vectors

class CombinationalCell(LogicCell):
    def __init__(self, name: str, in_ports: list, out_ports: list, functions: str, area: float = 0):
        super().__init__(name, in_ports, out_ports, functions, area)

    def get_input_capacitance(self, in_port, vdd_voltage, capacitance_unit):
        """Average all harnesses that target this input port"""
        if in_port not in self.in_ports:
            raise ValueError(f'Unrecognized input port {in_port}')
        input_capacitance = 0
        n = 0
        for harness in self.harnesses:
            if harness.target_in_port == in_port:
                input_capacitance += harness.get_input_capacitance(vdd_voltage, capacitance_unit)
                n += 1
        return input_capacitance / n

    def characterize(self, target_lib: LibrarySettings):
        """Run delay characterization for an N-input M-output combinational cell"""
        for test_vector in self.test_vectors:
            # Generate harness
            harness = CombinationalHarness(self, test_vector)
            
            # Generate spice file name
            spice_filename = f'delay_{self.name}'
            spice_filename += f'_{harness.target_in_port}{"01" if harness.in_direction == "rise" else "10"}'
            for input, state in zip(harness.stable_in_ports, harness.stable_in_port_states):
                spice_filename += f'_{input}{state}'
            spice_filename += f'_{harness.target_out_port}{"01" if harness.out_direction == "rise" else "10"}'
            for output, state in zip(harness.nontarget_out_ports, harness.nontarget_out_port_states):
                spice_filename += f'_{output}{state}'

            # Run delay characterization
            if target_lib.use_multithreaded:
                # Run multithreaded
                thread_id = 0
                threadlist = []
                for tmp_slope in self.in_slews:
                    for tmp_load in self.out_loads:
                        thread = threading.Thread(target=characterizer.char_comb.runSimCombinational,
                                args=([target_lib, self, harness, spice_filename, tmp_slope, tmp_load]),
                                name="%d" % thread_id)
                        threadlist.append(thread)
                        thread_id += 1
                for thread in threadlist:
                    thread.start()
                for thread in threadlist:
                    thread.join()
            else:
                # Run single-threaded
                for in_slew in self.in_slews:
                    for out_load in self.out_loads:
                        characterizer.char_comb.runSimCombinational(target_lib, self, harness, spice_filename, in_slew, out_load)

            # Save harness to the cell
            self.harnesses.append(harness)

class SequentialCell(LogicCell):
    def __init__(self, name: str, in_ports: list, out_ports: list, clock_pin: str, set_pin: str, reset_pin: str, flops: str, function: str, area: float = 0):
        super().__init__(name, in_ports, out_ports, function, area)
        self.clock = clock_pin  # clock pin name
        self.set = set_pin      # set pin name
        self.reset = reset_pin  # reset pin name
        self._flops = flops     # registers
        self._clock_slope = 0   # input pin clock slope

        # Characterization settings
        self._sim_setup_lowest = 0   ## fastest simulation edge (pos. val.) 
        self._sim_setup_highest = 0  ## lowest simulation edge (pos. val.) 
        self._sim_setup_timestep = 0 ## timestep for setup search (pos. val.) 
        self._sim_hold_lowest = 0    ## fastest simulation edge (pos. val.) 
        self._sim_hold_highest = 0   ## lowest simulation edge (pos. val.) 
        self._sim_hold_timestep = 0  ## timestep for hold search (pos. val.) 

        # From characterization results
        self.cclks = []     # clock pin capacitance
        self.csets = []     # set pin capacitance
        self.crsts = []     # reset pin capacitance

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
    def flops(self):
        return self._flops

    @property
    def clock_slope(self) -> float:
        return self._clock_slope

    @clock_slope.setter
    def clock_slope(self, value):
        if value is not None:
            if isinstance(value, (int, float)):
                if value > 0:
                    self._clock_slope = float(value)
                else:
                    raise ValueError('Clock slope must be greater than zero')
            elif value == 'auto':
                if not self.in_slews:
                    raise ValueError('Cannot use auto clock slope unless in_slews is set first!')
                self._clock_slope = float(self._in_slews[0])
            else:
                raise TypeError(f'Invalid type for clock slope: {type(value)}')
        else:
            raise ValueError(f'Invalid value for clock slope: {value}')

    @property
    def sim_setup_lowest(self) -> float:
        return self._sim_setup_lowest

    @sim_setup_lowest.setter
    def sim_setup_lowest(self, value):
        if value is not None:
            if isinstance(value, (int, float)):
                if value > 0:
                    self._sim_setup_lowest = float(value)
                else:
                    raise ValueError('Value must be greater than zero')
            elif value == 'auto':
                if not self.in_slews:
                    raise ValueError('Cannot use auto for sim_setup_lowest unless in_slews is set first!')
                # Use -10 * max input pin slope
                self._sim_setup_lowest = float(self._in_slews[-1]) * -10
            else:
                raise TypeError(f'Invalid type for sim_setup_lowest: {type(value)}')
        else:
            raise ValueError(f'Invalid value for sim_setup_lowest: {value}')
            
    ## this defines highest limit of setup edge
    def add_simulation_setup_highest(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use 10x of max slope 
        if ((tmp_array[1] == 'auto') and (self.in_slews[-1] != None)):
            self.sim_setup_highest = float(self.in_slews[-1]) * 10 
            print ("auto set setup simulation time highest limit")
        else:
            self.sim_setup_highest = float(tmp_array[1])
            
    def add_simulation_setup_timestep(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use 1/10x min slope
        if ((tmp_array[1] == 'auto') and (self.in_slews[0] != None)):
            self.sim_setup_timestep = float(self.in_slews[0])/10
            print ("auto set setup simulation timestep")
        else:
            self.sim_setup_timestep = float(tmp_array[1])
            
    ## this defines lowest limit of hold edge
    def add_simulation_hold_lowest(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use very small val. 
        #remove# if hold is less than zero, pwl time point does not be incremental
        #remove# and simulation failed
        if ((tmp_array[1] == 'auto') and (self.in_slews[-1] != None)):
            #self.sim_hold_lowest = float(self.in_slews[-1]) * -5 
            self.sim_hold_lowest = float(self.in_slews[-1]) * -10 
            #self.sim_hold_lowest = float(self.in_slews[-1]) * 0.001 
            print ("auto set hold simulation time lowest limit")
        else:
            self.sim_hold_lowest = float(tmp_array[1])
            
    ## this defines highest limit of hold edge
    def add_simulation_hold_highest(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slew is defined, use 5x of max slew 
        ## value should be smaller than "tmp_max_val_loop" in holdSearchFlop
        if ((tmp_array[1] == 'auto') and (self.in_slews[-1] != None)):
            #self.sim_hold_highest = float(self.in_slews[-1]) * 5 
            self.sim_hold_highest = float(self.in_slews[-1]) * 10 
            print ("auto set hold simulation time highest limit")
        else:
            self.sim_hold_highest = float(tmp_array[1])
            
    def add_simulation_hold_timestep(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use 1/10x min slope
        if ((tmp_array[1] == 'auto') and (self.in_slews[0] != None)):
            self.sim_hold_timestep = float(self.in_slews[0])/10 
            print ("auto set hold simulation timestep")
        else:
            self.sim_hold_timestep = float(tmp_array[1])
