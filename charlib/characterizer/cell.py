"""Encapsulates a cell to be tested."""

import itertools
from enum import StrEnum, Flag
from pathlib import Path

from charlib.characterizer.logic.functions import Function, StateFunction
from charlib.characterizer.logic.Parser import parse_logic
from charlib.liberty import liberty

class Cell:
    """A standard cell and its functional details"""

    def __init__(self, name: str, netlist: str|Path, functions: list, feedback_paths: list=[],
                 diff_pairs: list=[], input_pins: list=[], output_pins: list=[],
                 special_pins: dict={}, area: float=0.0):
        """Construct a new cell, detecting ports from netlist & functions

        Cells must provide at least a name, netlist, and a complete listing of pins. Pin names
        included in functions will be inferred as outputs if on the LHS, or inputs if on the RHS.

        :param name: The cell name as it appears in the spice netlist.
        :param netlist: Path to the cell spice netlist.
        :param functions: A list of functions this cell implements as verilog-syntax Boolean
                          expressions.
        :param state_paths: A list of feedback paths which encode cell state.
        :param diff_pairs: A list of pairs of pin names which make up differential pairs.
        :param input_pins: A lists of input pin names used to validate pins parsed from netlist
                           (if included).
        :param output_pins: A list of output pin names used to validate pins parsed from netlist
                            (if included).
        :param special_pins: A dict of pin names with special (i.e. non-logic) roles.
        """
        self.name = name
        self.liberty = liberty.Group('cell', name)
        self.liberty.add_attribute('area', area, 2)

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
        self.ports = list()
        function_outputs = set(self.functions.keys())
        function_inputs = set.union(*[set(function.operands) for function in self.functions.values()])
        for port in self.subckt().split()[2:]:
            role = 'logic'
            direction = 'inout' if port in function_outputs and port in function_inputs \
                    else 'output' if port in function_outputs \
                    else 'input' if port in function_inputs \
                    else f'unable to determine direction for port {port}'
            inverted = False
            edge_triggered = False
            # Special pins may override role, direction, etc.
            if port in special_pins:
                *modifiers, role = special_pins[port]
                if len(modifiers) > 1:
                    raise ValueError(f'A maximum of 2 components are allowed in role, but pin ' \
                                     f'"{port}" has role "{special_pins[port]}"')
                if any([substr in role for substr in ['primary', 'well', 'set', 'enable', 'clock']]):
                    direction = 'input'
                match modifiers:
                    case ['posedge']:
                        inverted = False
                        edge_triggered = True
                    case ['negedge']:
                        inverted = True
                        edge_triggered = True
                    case ['not']:
                        inverted = True
            self.ports.append(Port(port, direction, role, inverted, edge_triggered))

        # Set up diff pairs
        # TODO

        # If we have feedback paths, convert corresponding functions to FSMs
        for state_path in state_paths:
            state_name, output = state_path.split('=')
            self.functions[output] = StateFunction(self.functions[output], state_name,
                                                   enable=cell.filter_ports(role='enable'),
                                                   clock=cell.filter_ports(role='clock'),
                                                   preset=cell.filter_ports(role='set'),
                                                   clear=cell.filter_ports(role='reset'))

        # Validate port names (if given)
        if input_pins:
            if not all([input_pin in self.inputs for input_pin in input_pins]):
                raise ValueError(f'Failed to validate input pins! Expected {input_pins}, found' \
                                 f'{self.inputs}')
        if output_pins:
            if not all([output_pin in self.outputs for output_pin in output_pins]):
                raise ValueError(f'Failed to validate output pins! Expected {output_pins}, found' \
                                 f'{self.outputs}')

        # Add ports to liberty data
        # TODO: Handle other port roles
        for port in [p for p in self.ports if p.name in self.pg_pins]:
            pin = liberty.Group('pg_pin', port.name)
            pin.add_attribute('voltage_name', port.name)
            pin.add_attribute('pg_type', port.role)
            self.liberty.add_group(pin)
        for port in self.filter_ports(roles='logic'):
            pin = liberty.Group('pin', port.name)
            pin.add_attribute('direction', port.direction)
            if port.name in function_outputs:
                pin.add_attribute('function', str(self.functions[port.name]))
            self.liberty.add_group(pin)

    def subckt(self) -> str:
        """Return the subckt line from the spice file"""
        with open(self.netlist, 'r') as file:
            for line in file:
                if self.name in line and 'SUBCKT' in line.upper():
                    return line.upper()
            raise ValueError(f'Failed to identify a .subckt in netlist "{self.netlist}"')

    def filter_ports(self, directions: list=[], roles: list=[], inverted: bool|None=None,
                     edge_triggered: bool|None=None):
        """Return a collection of ports matching the given directions, roles, etc.

        :param direction: A list of port directions to match. Elements must be values in
                          Port.Direction.
        :param role: A list of port roles to match. Elements must be values in Port.Role.
        :param inverted: Return only ports with inversion matching this argument.
        :param edge_triggered: Return only ports with trigger matching this argument.

        Any argument may be omitted, in which case it is not used to filter the list of ports.
        """
        for port in self.ports:
            if directions and not port.direction in directions:
                continue
            if roles and not port.role in roles:
                continue
            if inverted is not None and not port.is_inverted() == inverted:
                continue
            if edge_triggered is not None and not port.is_edge_triggered() == edge_triggered:
                continue
            yield port

    @property
    def outputs(self) -> list:
        """Return a list of output logic port names"""
        return [port.name for port in self.filter_ports(['output'], roles=['logic'])]

    @property
    def inputs(self) -> list:
        """Return a list of input logic port names"""
        return [port.name for port in self.filter_ports(['input'], roles=['logic'])]

    @property
    def inouts(self) -> list:
        """Return a list of inout logic port names"""
        return [port.name for port in self.filter_ports(['inout'], roles=['logic'])]

    @property
    def pg_pins(self) -> list:
        """Return a list of supply and bias pin names"""
        return [port.name for port in self.filter_ports(roles=['primary_power', 'primary_ground',
                                                               'pwell', 'nwell'])]

    def paths(self):
        """Generator for input-to-output paths through a cell

        Yields lists in the format [input_name, input_transition, output_name, output_transition].
        All possible combinations of port names and transitions are yielded, regardless of whether
        they are possible given this cell's functions.
        """
        # FIXME: Generate only paths which actually make sense given this cell's function
        transitions = ['01', '10']
        for path in itertools.product(self.inputs, transitions, self.outputs, transitions):
            yield path

    def nonmasking_conditions_for_path(self, input_port, input_transition, output_port,
                                       output_transition):
        """Find all mappings of pin states such that the desired state transitions occur.

        Returns a generator yielding dictionaries of states for which input_port and output_port
        undergo input_transition and output_transition respectively.

        :param input_port: The name of the input port of interest.
        :param input_transition: The desired state transition for the input port. Must be '01' or
                                 '10'.
        :param output_port: The name of the output port of interest.
        :param output_transition: The desired state transition for the output port. Must be '01' or
                                  '10'.
        """
        function = self.functions[output_port]
        for test_vector in function.test_vectors:
            states = dict(zip([*(function.operands), output_port], test_vector))
            if states[input_port] == input_transition and states[output_port] == output_transition:
                yield states

    @property
    def is_sequential(self) -> bool:
        return any([isinstance(f, StateFunction) for f in self.functions.values()])


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
        ANALOG = 'analog'
        POWER = 'primary_power'
        GROUND = 'primary_ground'
        PWELL = 'pwell'
        NWELL = 'nwell'
        CLEAR = 'reset'
        PRESET = 'set'
        ENABLE = 'enable' # Tristate enable

    class Trigger(Flag):
        EDGE = True
        LEVEL = False

    def __init__(self, name: str, direction: str, role='logic', inverted=False, edge_triggered=False):
        """Construct a new port"""
        self.name = name
        self.direction = self.Direction(direction)
        self.role = self.Role(role)
        self.inversion = inverted
        self.trigger = self.Trigger(edge_triggered)

    def is_inverted(self) -> bool:
        """Return whether this port is inverted.

        Inputs which are inverted are either falling-edge triggered or logic-0 active. Useful for
        differential complementary inputs, inverting flip-flop outputs, inverted set and enable
        pins, etc."""
        return self.inversion

    def is_edge_triggered(self) -> bool:
        """Return whether this port is edge-triggered."""
        return bool(self.trigger)


class CellTestConfig:
    """Capture configuration information for testing one or more cells"""

    def __init__(self, models: list, plots=[], timestep=None, **parameters):
        """Construct a new test configuration.

        :param models: Transistor models for the cell under test
        :param plots: A list of plot types to generate from simulation results. Defaults to None.
        :param timestep: The simulation timestep to use for transient simulations, specified in
                         settings.units.time units. Defaults to 1/8 the minimum data_slew or
                         clock_slew if not provided.
        :param **parameters: Keyword arguments containing lists of test parameters, as described
                             below:
            :param data_slews: A list of input data slew rates to test, specified in
                               settings.units.time units.
            :param clock_slews: A list of clock slew rates to test specified in settings.units.time
                               units
            :param loads: A list of output load capacitances to test, specified in
                          settings.units.capacitance units
        """
        self.models = list()
        for model in models:
            # Split to path and (optional) section, then validate both
            filename, *libname = model.split()
            if not Path(filename).exists():
                raise ValueError(f'Unable to locate model at "{filename}"')
            if len(libname) > 1:
                raise ValueError(f'Expected 1 libname in model "{model}", got {len(libname)}:' \
                                 f'{libname}')
            elif not len(libname) == 1:
                libname = []
            self.models.append((Path(filename), *libname))

        self.timestep = timestep
        self.plots = plots
        self.parameters = parameters

    def variations(self, *keys):
        """Generator for test configuration variations

        Yields dictionaries containing key-value pairs for a single combination of parameters. For
        example: {data_slew: 0.01, load: 0.025}

        :param *keys: If provided, only return variations of provided parameter names.
        """
        parameters = self.parameters if not keys else {k: self.parameters[k] for k in keys}
        param_names, values = zip(*parameters.items())
        param_names = [n[0:-1] if n.endswith('s') else n for n in param_names]
        for combination in itertools.product(*values):
            yield dict(zip(param_names, combination))
