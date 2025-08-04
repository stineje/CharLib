"""This module contains test managers for various types of standard cells"""

from itertools import product
from pathlib import Path

from PySpice import Circuit, Simulator, SpiceLibrary
from PySpice.Spice.unit import str_spice
from PySpice.Unit import *

from charlib.characterizer.functions import Function, registered_functions
from charlib.characterizer.Harness import filter_harnesses_by_ports, find_harness_by_arc
from charlib.characterizer.LogicParser import parse_logic
from charlib.liberty.cell import Cell, Pin, TimingData, TableTemplate

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
                                        # print(f'Recognized {self.cell.name} pin {pin_name} function as {reg_name}')
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
        self.sim_timestep = kwargs.get('simulation_timestep', min(self.in_slews)/4.0)

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
        match value:
            case 'all':
                self._plots = ['io', 'delay', 'power']
            case 'none':
                self._plots = []
            case list():
                self._plots = value
            case _:
                raise ValueError(f'Invalid value for plots: "{value}"')

    @property
    def is_exported(self) -> bool:
        """Return whether the results have been exported"""
        return self._is_exported

    def set_exported(self):
        """Set a flag that this test manager's results have been exported"""
        self._is_exported = True

    def add_pg_pins(self, vdd, vss, pwell, nwell):
        """Annotate cell liberty file with pg_pins"""
        self._cell.add_pg_pin(vdd.name, vdd.name, 'primary_power')
        self._cell.add_pg_pin(vss.name, vss.name, 'primary_ground')
        self._cell.add_pg_pin(pwell.name, pwell.name, 'pwell')
        self._cell.add_pg_pin(nwell.name, nwell.name, 'nwell')


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
