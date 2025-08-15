"""Encapsulates a cell to be tested. May be combinational, sequential, or tristate"""

from enum import StrEnum
from pathlib import Path

from charlib.characterizer.logic import Function
from charlib.characterizer.logic.Parser import parse_logic

class Cell:
    def __init__(self, netlist: str|Path, functions: list|None=None, **kwargs):
        """Bind netlist, ports, and functions"""
        if isinstance(netlist, (str, Path)):
            if not Path(netlist).is_file():
                raise ValueError(f'Invalid value for netlist: "{netlist}" is not a file')
            self.netlist = Path(netlist)
        else:
            raise TypeError(f'Invalid type for netlist: {type(value)}')

        # Validate functions
        for function in functions:
            output, expr = function.split('=')
            # TODO: complete

        # Use netlist .subckt line and functions to identify and assign ports
        ports = self.subckt().upper().split()[2:]

    def subckt(self) -> str:
        """Return the subckt line from the spice file"""
        with open(self.netlist, 'r') as file:
            for line in file:
                if 'SUBCKT' in line.upper():
                    return line
            raise ValueError(f'Failed to identify a .subckt in netlist "{self.netlist}"')

class Port:
    """Encapsulate port names with directions"""

    class Direction(StrEnum):
        """Enumerate valid port directions"""
        IN = 'input'
        OUT = 'output'
        INOUT = 'inout'

    def __init(self, name: str, direction: str):
        """Construct a new port"""
        self.name = name
        self.direction = Direction(direction)
