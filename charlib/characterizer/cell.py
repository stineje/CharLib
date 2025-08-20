"""Encapsulates a cell to be tested."""

from enum import StrEnum
from pathlib import Path

from charlib.characterizer.logic import Function
from charlib.characterizer.logic.Parser import parse_logic

class Cell:
    """A standard cell and its functional details"""

    def __init__(self, name: str, netlist: str|Path, functions: list,
                 logic_pins={}, special_pins={}):
        """Construct a new cell, detecting ports from netlist & functions

        :param name: The cell name as it appears in the spice netlist
        :param netlist: Path to the cell spice netlist
        :param functions: A list of functions this cell implements in verilog syntax
        :param logic_pins: A dictionary with keys "inputs" and "outputs" containing lists of pin
                           names. Used to validate pins parsed from netlist if included.
        :param special_pins: A dict of pin names with non-logic roles
        """
        self.name = name

        # Validate & bind netlist as an existing filepath
        if isinstance(netlist, (str, Path)):
            if not Path(netlist).is_file():
                raise ValueError(f'Invalid value for netlist: "{netlist}" is not a file')
            self.netlist = Path(netlist)
        else:
            raise TypeError(f'Invalid type for netlist: {type(netlist)}')

        # Validate functions, convert to Function, and bind to this object
        self.functions = dict()
        for function in list(functions):
            # TODO: Add special handling for decap, filler, tap cells
            output, expr = function.split('=')
            output = ''.join([c for c in output if c.isalnum()])
            # Validate function expression
            if not parse_logic(expr):
                raise ValueError(f'Unable to parse function expression "{expr}"')
            self.functions[output] = Function(expr)

        # Use netlist .subckt line and function operands to validate and bind ports
        self.ports = dict()
        function_outputs = set(self.functions.keys())
        function_inputs = set.union(*[set(function.operands) for function in self.functions.values()])
        for port in self.subckt().split()[2:]:
            role = 'logic'
            direction = 'inout' if port in function_outputs and port in function_inputs \
                    else 'output' if port in function_outputs \
                    else 'input' if port in function_inputs \
                    else f'unable to determine direction for port {port}'
            # Special pins override default role (and sometimes direction)
            if port in special_pins:
                role = special_pins[port]
                if 'primary' in role or 'well' in role:
                    direction = 'input'
            self.ports[port] = Port(port, direction, role)

        # If logic_pins kwarg is present, use it to validate port names
        if logic_pins:
            # Note that we do not validate that all self.ports etc. are in logic_pins. This is
            # because self.ports also includes pg_pins and others that are not related to functions
            if not all([input_pin in self.inputs for input_pin in logic_pins['inputs']]):
                raise ValueError(f'Failed to validate input pins! Expected {logic_pins["inputs"]}, found {self.inputs}')
            if not all([output_pin in self.outputs for output_pin in logic_pins['outputs']]):
                raise ValueError(f'Failed to validate output pins! Expected {logic_pins["outputs"]}, found {self.outputs}')

    def subckt(self) -> str:
        """Return the subckt line from the spice file"""
        with open(self.netlist, 'r') as file:
            for line in file:
                if self.name in line and 'SUBCKT' in line.upper():
                    return line
            raise ValueError(f'Failed to identify a .subckt in netlist "{self.netlist}"')

    @property
    def outputs(self) -> list:
        """Return a list of output port names"""
        return [p.name for p in self.ports.values() if p.direction == 'output']

    @property
    def inputs(self) -> list:
        """Return a list of input port names"""
        return [p.name for p in self.ports.values() if p.direction == 'input']

    @property
    def inouts(self) -> list:
        """Return a list of inout port names"""
        return [p.name for p in self.ports.values() if p.direction == 'inout']

    @property
    def pg_pins(self) -> list:
        """Return a list of supply and bias pin names"""
        return [p.name for p in self.ports.values() if p.role in ['primary_power', 'primary_ground', 'pwell', 'nwell']]

class Port:
    """Encapsulate port names with roles and directions"""

    class Direction(StrEnum):
        """Enumerate valid port directions

        Port direction describes whether the cell drives the port or expects the port to be driven
        by an external actor."""
        IN = 'input'
        OUT = 'output'
        INOUT = 'inout'

    class Role(StrEnum):
        """Enumerate valid port roles

        A port's role describes how it is to be used during characterization. Most ports are simple
        logic I/Os, but some ports, such as clocks and resets, have special roles that require
        a different approach to timing characterization. These are also useful for constructing the
        liberty file after characterization.
        """
        LOGIC = 'logic' # Normal inputs and outputs
        CLOCK = 'clock'
        INVERTED = 'inverted' # Diff complementary input or flop inverting output
        ANALOG = 'analog'
        POWER = 'primary_power'
        GROUND = 'primary_ground'
        PWELL = 'pwell'
        NWELL = 'nwell'

    def __init__(self, name: str, direction: str, role='logic'):
        """Construct a new port"""
        self.name = name
        self.direction = self.Direction(direction)
        self.role = self.Role(role)


class CellTestConfig:
    """Capture configuration information for testing one or more cells"""

    def __init__(self, models: list, **parameters):
        """Construct a new test configuration.

        :param models: Transistor models for the cell under test
        :param data_slews: A list of input data slew rates to test, specified in settings.units.time
                           units
        :param clock_slews: A list of clock slew rates to test specified in settings.units.time
                           units
        :param loads: A list of output load capacitances to test, specified in
                      settings.units.capacitance units
        :param timestep: The simulation timestep to use for transient simulations, specified in
                         settings.units.time units. Defaults to 1/8 the minimum data_slew or
                         clock_slew if not provided.
        :param plots: A list of plot types to generate from simulation results
        """
        self.models = list()
        for model in models:
            # Split to path and (optional) section, then validate both
            filename, *libname = model.split()
            if not Path(filename).exists():
                raise ValueError(f'Unable to locate model at "{filename}"')
            if len(libname) > 1:
                raise ValueError(f'Expected 1 libname in model "{model}", got {len(libname)}: {libname}')
            self.models.append((Path(filename), *libname))

        self.parameters = parameters

    def __getitem__(self, key: str):
        """Return the parameter corresponding to key"""
        return self.parameters[key]

