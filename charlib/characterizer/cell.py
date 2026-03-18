"""Encapsulates a cell to be tested."""

import itertools, re
from pathlib import Path

from charlib.characterizer.logic.functions import Function, OPERAND_REGEX
from charlib.characterizer.port import Port, Pin, DifferentialPair
from charlib.characterizer.logic.Parser import parse_logic
from charlib.liberty import liberty

class Cell:
    """A standard cell and its functional details"""

    def __init__(self, name: str, supply_nodes: dict,  **cell_config):
        """Construct a new cell from the given configuration

        :param name: The cell name as it appears in the spice netlist.
        :param named_nodes: Supply node name: role maps from the library configuration.
        :param cell_config: The dict of properties provided in the configuration YAML.

        The cell initialization process is as follows:
        1. Process cell_config to get the following information about the cell:
            - The path to the cell's netlist.
            - Functions implemented in this cell (and optionally input and output pin names).
            - Which pins have special roles or are members of differential pairs.
            - The names of any internal state elements / feedback paths..
            - Cell metadata that belongs in the liberty file (such as area)
        2. Locate the cell netlist and read the .subckt line. For each pin in the netlist:
            a. Determine pin direction from the function list.
            b. Determine pin role and trigger type from special pins (default: logic/level-sensing)
            c. Determine how to construct the pin and bind it to the cell.
                - If the pin is a member of a differential pair, construct with DifferentialPair.
                - Otherwise, construct with Pin.
        3. For each output pin, construct the corresponding Function and bind it to the cell.
        4. Construct a skeleton liberty object for this cell.
        """
        self.name = name
        self.pins = dict()
        self.diff_pairs = dict()
        self.functions = dict()

        ## 1. Process cell_config

        # Validate netlist
        netlist = cell_config['netlist']
        if isinstance(netlist, (str, Path)):
            if not Path(netlist).is_file():
                raise ValueError(f'Invalid value for netlist: "{netlist}" is not a file')
            self.netlist = Path(netlist)
        else:
            raise TypeError(f'Invalid type for netlist: {type(netlist)}')

        # Map supplies and special pins to (trigger, inverted, role) tuples
        special_pins = {p.upper(): (Port.Trigger.LEVEL, False, role) for p, role in supply_nodes.items()}
        for role in ['clock', 'set', 'reset', 'enable']:
            if role in cell_config:
                match cell_config[role].replace('!', 'not ').split():
                    case ['posedge', pin]:
                        special_pins[pin.upper()] = (Port.Trigger.EDGE, False, role)
                    case ['negedge', pin]:
                        special_pins[pin.upper()] = (Port.Trigger.EDGE, True, role)
                    case ['not', pin]:
                        special_pins[pin.upper()] = (Port.Trigger.LEVEL, True, role)
                    case [pin]:
                        special_pins[pin.upper()] = (Port.Trigger.LEVEL, False, role)

        # Identify diff pairs
        diff_pairs = [tuple(pair.split()) for pair in cell_config.get('pairs', [])]

        # Parse functions to determine input and output mapping
        functions = dict()
        inputs = set()
        outputs = set()
        for function in cell_config['functions']:
            output, expression = function.split('=')
            output = ''.join([c for c in output if c.isalnum() or c == '_'])
            if not parse_logic(expression):
                raise ValueError(f'Unable to parse function "{function}"')
            functions[output] = expression
            inputs.update(set(OPERAND_REGEX.findall(expression)))
            outputs.add(output)

        ## 2. Read .subckt line from netlist and construct pins

        # Helper function for direction matching with minimal membership checking
        def match_direction(pin_name):
            match (pin_name in inputs, pin_name in outputs):
                case True, True:  return 'inout'
                case False, True: return 'output'
                case True, False: return 'input'
            raise ValueError('Unable to determine direction for pin "{pin_name}"')

        # Get pin names from subckt and iterate until there are no unassigned pins remaining
        unassigned_ports = self.subckt().split()[2:]
        while unassigned_ports:
            port = unassigned_ports.pop(0)
            if port in special_pins:
                # This pin has a special (i.e. non-logic) role
                trigger_type, inverted, role = special_pins[port]
                self.pins[port] = Pin(port, 'input', role, inverted, trigger_type)
            elif any([port in pair for pair in diff_pairs]):
                # This pin is a member of a differential pair; find and build the pair
                [pair] = [p for p in diff_pairs if port in p]
                (noninv_pin, inv_pin) = pair
                self.diff_pairs[pair] = DifferentialPair(noninv_pin, inv_pin, match_direction(port))
                unassigned_ports.remove(pair[pair.index(port)-1])
            else:
                # This is a standard logic pin
                self.pins[port] = Pin(port, match_direction(port))

        # Validate pin names if 'inputs' and/or 'outputs' keys are in cell_config
        if 'inputs' in cell_config:
            if not set(cell_config['inputs']) <= set(self.inputs):
                raise ValueError(f'Expected inputs {cell_config["inputs"]}, found {self.inputs}')
        if 'outputs' in cell_config:
            if not set(cell_config['outputs']) <= set(self.outputs):
                raise ValueError(f'Expected outputs {cell_config["outputs"]}, found {self.outputs}')

        ## 3. Construct functions based on port types & feedback paths
        for output, expression in functions.items():
            is_inverting = output in [pair.inverting_port_name for pair in diff_pairs]
            state_map = {v: k for k, v in cell_config.get('state', {}).items()}
            state = state_map.get(output, None)
            # TODO: Pass only ports which are related to this function
            # TODO: Handle multiple clocks, etc.
            self.functions[output] = Function(self.pins[output], expression, *self.ports, state=state)

        ## 4. Add as much liberty data as we can right now
        self.liberty = liberty.Group('cell', name)
        self.liberty.add_attribute('area', cell_config.get('area', 0.0), 2)
        for port in self.ports:
            if port.name in self.pg_pins:
                pin_group = liberty.Group('pg_pin', port.name)
                pin_group.add_attribute('voltage_name', port.name)
                pin_group.add_attribute('pg_type', port.role)
            else:
                pin_group = liberty.Group('pin', port.name)
                pin_group.add_attribute('direction', port.direction)
                if port.direction is Port.Direction.OUT:
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
        yield from self.pins.values()
        for pair in self.diff_pairs.values():
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

    def _get_first_port_with_role(self, role):
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
        return self._get_first_port_with_role('enable')

    @property
    def clock(self):
        """Return the cell's clock port, if present"""
        return self._get_first_port_with_role('clock')

    @property
    def preset(self):
        """Return the cell's set port, if present"""
        return self._get_first_port_with_role('set')

    @property
    def clear(self):
        """Return the cell's reset port, if present"""
        return self._get_first_port_with_role('reset')

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
        for tv in self.functions[output_port].test_vectors:
            if tv[input_port] == input_transition and tv[output_port] == output_transition:
                yield tv

    @property
    def is_sequential(self) -> bool:
        return any([f.state is not None for f in self.functions.values()])


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
        supported_parameters = ['data_slews', 'clock_slews', 'loads']
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
        self.parameters = {k: parameters[k] for k in supported_parameters if k in parameters}

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
