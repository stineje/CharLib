"""Encapsulates a cell to be tested."""

from enum import StrEnum
from pathlib import Path

from charlib.characterizer.logic import Function
from charlib.characterizer.logic.Parser import parse_logic

class Cell:
    """A standard cell and its functional details"""

    def __init__(self, name: str, netlist: str|Path, functions: list, supplies=[]):
        """Construct a new cell, detecting ports from netlist & functions

        :param name: The cell name as it appears in the spice netlist
        :param netlist: Path to the cell spice netlist
        :param functions: A list of functions this cell implements in verilog syntax
        :param supplies: A dict of supply nodes and voltages to ignore when mapping ports
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
            output, expr = function.split('=')
            output = ''.join([c for c in output if c.isalnum()])
            # Validate function expression
            if not parse_logic(expr):
                raise ValueError(f'Unable to parse function expression "{expr}"')
            self.functions[output] = Function(expr)

        # If present, store supply & bias node names. These will be ignored during port parsing
        self.supplies = supplies

        # Use netlist .subckt line and function operands to validate and bind ports
        self.ports = dict()
        function_outputs = set(self.functions.keys())
        function_inputs = set.union(*[set(function.operands) for function in self.functions.values()])
        for port in self.subckt().split()[2:]:
            if port in self.supplies:
                continue # Skip supply and bias nodes, we already know what these are
            direction = 'inout' if port in function_outputs and port in function_inputs \
                    else 'output' if port in function_outputs \
                    else 'input' if port in function_inputs \
                    else 'unknown'
            self.ports[port] = Port(port, direction)
            # TODO: Add logic for handling more complex port relationships, such as diff pairs,
            # clocks, flop inverted outputs, etc.

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
        return [p.name for p in self.ports if p.direction == 'output']

    @property
    def inputs(self) -> list:
        """Return a list of input port names"""
        return [p.name for p in self.ports if p.direction == 'input']

    @property
    def inouts(self) -> list:
        """Return a list of inout port names"""
        return [p.name for p in self.ports if p.direction == 'inout']


class Port:
    """Encapsulate port names with directions"""

    class Direction(StrEnum):
        """Enumerate valid port directions"""
        IN = 'input'
        OUT = 'output'
        INOUT = 'inout'

    def __init__(self, name: str, direction: str):
        """Construct a new port"""
        self.name = name
        self.direction = self.Direction(direction)


class CellTestConfig:
    """Capture configuration information for testing one or more cells"""

    def __init__(models: list, **test_conditions)
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
        """
        self.models = list()
        for model in models:
            # Split to path and (optional) section, then validate both
            filename, *libname = model.split()
            if not Path(filename).exists():
                raise ValueError(f'Unable to locate model at "{filename}"')
            if len(libname) > 1:
                raise ValueError(f'Expected 1 libname in model "{model}", got {len(libname)}')
            self.models.append(tuple(Path(filename), *libname))

        self.test_conditions = test_conditions

