"""Encapsulates a cell to be tested."""

import itertools
from enum import StrEnum, Flag
from pathlib import Path

from charlib.characterizer.logic.functions import Function, StateFunction
from charlib.characterizer.logic.Parser import parse_logic
from charlib.liberty import liberty

class Cell:
    """A standard cell and its functional details"""

    def __init__(self, name: str, netlist: str|Path, functions: list, state_aliases: list=[],
                 diff_pairs: list=[], input_pins: list=[], output_pins: list=[],
                 special_pins: dict={}, area: float=0.0):
        """Construct a new cell, detecting ports from netlist & functions

        Cells must provide at least a name, netlist, and a complete listing of pins. Pin names
        included in functions will be inferred as outputs if on the LHS, or inputs if on the RHS.

        :param name: The cell name as it appears in the spice netlist.
        :param netlist: Path to the cell spice netlist.
        :param functions: A list of functions this cell implements as verilog-syntax Boolean
                          expressions.
        :param state_aliases: A list of 'alias=output' statements describing feedback paths within
                              the cell. These are used to explicitly identify recurrence
                              relations within the cell's function, usually encoding cell state.
        :param diff_pairs: A list of 'A B' pairs of pin names which make up differential pairs.
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
        self.pins = list()
        self.diff_pairs = list()
        function_outputs = set(self.functions.keys())
        function_inputs = set.union(*[set(function.operands) for function in self.functions.values()])
        diff_pairs = [tuple(pair.split()) for pair in diff_pairs]
        unassigned_ports = self.subckt().split()[2:]
        while unassigned_ports:
            port = unassigned_ports.pop(0)
            direction = 'inout' if port in function_outputs and port in function_inputs \
                    else 'output' if port in function_outputs \
                    else 'input' if port in function_inputs \
                    else f'unable to determine direction for pin "{port}"'
            if port in special_pins:
                # This pin has a special (i.e. non-logic) role
                *modifiers, role = special_pins[port].split()
                if len(modifiers) > 1:
                    raise ValueError(f'A maximum of 2 components are allowed in role, but pin ' \
                                     f'"{port}" has role "{special_pins[port]}"')
                if any([sub in role for sub in ['primary', 'well', 'set', 'enable', 'clock']]):
                    direction = 'input'
                edge_triggered = any(['edge' in m for m in modifiers])
                inverted = any(['not' in m for m in modifiers]) \
                        or any(['neg' in m for m in modifiers])
                self.pins.append(Pin(port, direction, role, inverted, edge_triggered))
            elif not any([port in pair for pair in diff_pairs]):
                # This pin is not a member of a diff pair; assume defaults
                self.pins.append(Pin(port, direction))
            else:
                # This pin is a member of a diff pair; find and build the pair
                [pair] = [pair for pair in diff_pairs if port in pair]
                (noninv_pin, inv_pin) = pair
                self.diff_pairs.append(DifferentialPair(noninv_pin, inv_pin, direction))
                unassigned_ports.remove(pair[pair.index(port)-1]) # Don't add the other port twice

        # If we have feedback paths, convert corresponding functions
        self.state_aliases = {k.strip(): a.strip() for a, k in [s.split('=') for s in state_aliases]}
        for output, state_name in self.state_aliases.items():
            try:
                self.functions[output] = StateFunction(self.functions[output], state_name,
                                                       enable=self.enable, clock=self.clock,
                                                       preset=self.preset, clear=self.clear)
            except KeyError as e:
                raise KeyError(f'Cell {self.name} has no port {output}') from e

        # Validate pin names (if given)
        if input_pins:
            if not all([input_pin in self.inputs for input_pin in input_pins]):
                raise ValueError(f'Failed to validate input pins! Expected {input_pins}, found' \
                                 f'{self.inputs}')
        if output_pins:
            if not all([output_pin in self.outputs for output_pin in output_pins]):
                raise ValueError(f'Failed to validate output pins! Expected {output_pins}, found' \
                                 f'{self.outputs}')

        # Add ports to liberty data
        for port in self.ports:
            if port.name in self.pg_pins:
                pin_group = liberty.Group('pg_pin', port.name)
                pin_group.add_attribute('voltage_name', port.name)
                pin_group.add_attribute('pg_type', port.role)
            else:
                pin_group = liberty.Group('pin', port.name)
                pin_group.add_attribute('direction', port.direction)
                if port.name in self.outputs:
                    pin_group.add_attribute('function', str(self.functions[port.name]))
                elif port.role == Port.Role.CLOCK:
                    pin_group.add_attribute('clock', "true")
            self.liberty.add_group(pin_group)

    def subckt(self) -> str:
        """Return the subckt line from the spice file"""
        with open(self.netlist, 'r') as file:
            for line in file:
                if self.name in line and 'SUBCKT' in line.upper():
                    return line.upper()
            raise ValueError(f'Failed to identify a .subckt in netlist "{self.netlist}"')

    @property
    def ports(self):
        """Yield all ports as pins, including those stored as members of differential pairs"""
        yield from self.pins
        for pair in self.diff_pairs:
            yield from pair.as_pins()

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

    def _get_singular_port_by_role(self, role):
        """Return the first port with the specified role. If there is no such port, return None."""
        if not self.ports:
            return None
        try:
            port = next(self.filter_ports(roles=[role]))
        except StopIteration:
            port = None
        return port

    @property
    def enable(self):
        """Return the cell's enable port, if present"""
        return self._get_singular_port_by_role('enable')

    @property
    def clock(self):
        """Return the cell's clock port, if present"""
        return self._get_singular_port_by_role('clock')

    @property
    def preset(self):
        """Return the cell's set port, if present"""
        return self._get_singular_port_by_role('set')

    @property
    def clear(self):
        """Return the cell's reset port, if present"""
        return self._get_singular_port_by_role('reset')

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
    """Encapsulate port names with role and signaling characteristics"""

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

    def __init__(self, name: str, direction: str, role: str, trigger: bool):
        """Construct a new port.

        :param name: The port's name as it appears in the netlist
        :param direction: The port's direction. See the Port.Direction enum for details.
        :param role: The port's role. See the Port.Role enum for details.
        :param edge_triggered: Whether the port is edge-sensitive or level-sensitive. See the
                               Port.Trigger enum for details.
        """
        self.name = name
        self.direction = self.Direction(direction)
        self.role = self.Role(role)
        self.trigger = self.Trigger(trigger)

    def __repr__(self) -> str:
        return f'Port({self.name}, {self.direction}, {self.role}, {self.trigger})'

    def is_edge_triggered(self) -> bool:
        """Return whether this port is edge-triggered."""
        return bool(self.trigger)


class Pin(Port):
    """A port with a single physical pin."""
    def __init__(self, name: str, direction: str, role='logic', inverted=False,
                 edge_triggered=False):
        """Construct a new pin."""
        super().__init__(name, direction, role, edge_triggered)
        self.inversion = inverted

    def is_inverted(self) -> bool:
        """Return whether this port is inverted.

        Inputs which are inverted are either falling-edge triggered or logic-0 active. Useful for
        differential complementary inputs, inverting flip-flop outputs, active-low set and enable
        pins, etc."""
        return self.inversion


class DifferentialPair(Port):
    """Encapsulate a port consisting of a differential pair of physical pins"""
    def __init__(self, noninverting_port_name: str, inverting_port_name: str, direction: str,
                 role='logic', edge_triggered=False):
        super().__init__(noninverting_port_name, direction, role, edge_triggered)
        self.noninverting_port_name = noninverting_port_name
        self.inverting_port_name = inverting_port_name

    def as_pins(self):
        yield Pin(self.noninverting_port_name, self.direction, self.role, inverted=False,
                  edge_triggered=self.trigger)
        yield Pin(self.inverting_port_name, self.direction, self.role, inverted=True,
                  edge_triggered=self.trigger)


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
