from characterizer.LogicCell import LogicCell, SequentialCell
from characterizer.UnitsSettings import UnitsSettings, EngineeringUnit

class Harness:
    """Characterization parameters for one path through a cell
    
    A Harness defines characterization parameters from one input to one
    output of a standard cell circuit. The target input port and output
    port are defined by the value of test_vector passed to the
    constructor."""

    def __init__(self, target_cell: LogicCell, test_vector: list) -> None:
        """Create a new Harness.
        
        The key parameter here is test_vector. It describes the expected
        state of each input pin and output pin, as well as which input and
        output this Harness is testing. It should be formatted as a list of
        strings with N+M entries, where N is the number of input ports and
        M is the number of output ports in target_cell:

        [in1, ..., inN, out1, ..., outM]

        Each entry in test_vector is a string that represents the state of
        the corresponding I/O on the standard cell. For inputs, the values
        '0' and '1' represent nontarget input ports. These ports will be
        held stable with the corresponding logic values. Values of '01' or
        '10' indicate target input ports that are rising or falling
        respectively. The case is similar for outputs: '0' and '1' represent
        expected results for nontarget output ports, and '01' or '10'
        represent target outputs that are expected to fall or rise as the
        input changes.

        For example, a test vector for a single-input single-output inverter
        might look like this: ['01', '10'].
        Or a test vector for an AND gate with 2 inputs and a single output
        might look like: ['01', '1', '01'].

        Note that target_cell is only required for initialization checks,
        such as ensuring that test_vector correctly maps to the input and
        output pins of the cell under test. A Harness does not keep track of
        changes to target_cell. If target_cell is altered after the Harness
        was generated, a new Harness should be generated."""

        self._stable_in_ports = []              # input pins to hold stable
        self._stable_in_port_states = []        # states for stable pins
        self._nontarget_out_ports = []          # output pins that we aren't specifically evaluating
        self._nontarget_out_port_states = []    # states for nontarget outputs
        self.results =  {}                      # nested dictionary of characterization results grouped by in_slope and out_load

        # Parse inputs from test vector
        # Test vector should be formatted like [in1, ..., inN, out1, ..., outM]
        num_inputs = len(target_cell.in_ports)
        num_outputs = len(target_cell.out_ports)
        input_test_vector = test_vector[0:num_inputs]
        output_test_vector = test_vector[num_inputs:num_inputs+num_outputs]
        state_to_direction = lambda s: 'rise' if s == '01' else 'fall' if s == '10' else s

        # Get inputs from test vector
        for in_port, state in zip(target_cell.in_ports, input_test_vector):
            if len(state) > 1:
                self._target_in_port = in_port
                self.in_direction = state_to_direction(state)
            else:
                self._stable_in_ports.append(in_port)
                self._stable_in_port_states.append(state)
        if not self._target_in_port:
            raise ValueError(f'Unable to parse target input port from test vector {test_vector}')

        # Get outputs from test vector
        for out_port, state in zip(target_cell.out_ports, output_test_vector):
            if len(state) > 1:
                self._target_out_port = out_port
                self.out_direction = state_to_direction(state)
            else:
                self._nontarget_out_ports.append(out_port)
                self._nontarget_out_port_states.append(state)
        if not self._target_out_port:
            raise ValueError(f'Unable to parse target output port from test vector {test_vector}')

        # Initialize results from target_cell input slopes and loads
        for in_slope in target_cell.in_slopes:
            self.results[str(in_slope)] = {}
            for out_load in target_cell.out_loads:
                self.results[str(in_slope)][str(out_load)] = {}

    def __str__(self) -> str:
        lines = []
        lines.append(f'Route Under Test: {self.target_in_port} ({self.in_direction}) -> {self.target_out_port} ({self.out_direction})')
        if self.stable_in_ports:
            lines.append(f'Stable Input Ports:')
            for port, state in zip(self.stable_in_ports, self.stable_in_port_states):
                lines.append(f'    {port}: {state}')
        if self.nontarget_out_ports:
            lines.append(f'Nontarget Output Ports:')
            for port, state in zip(self.nontarget_out_ports, self.nontarget_out_port_states):
                lines.append(f'    {port}: {state}')
        # TODO: Display results if available
        return '\n'.join(lines)

    @property
    def target_in_port(self) -> str:
        return self._target_in_port

    @property
    def stable_in_ports(self) -> list:
        return self._stable_in_ports

    @property
    def stable_in_port_states(self) -> list:
        return self._stable_in_port_states

    @property
    def target_out_port(self) -> str:
        return self._target_out_port

    @property
    def nontarget_out_ports(self) -> list:
        return self._nontarget_out_ports

    @property
    def nontarget_out_port_states(self) -> list:
        return self._nontarget_out_port_states

    @property
    def in_direction(self) -> str:
        return self._in_direction

    @in_direction.setter
    def in_direction(self, value: str):
        if value is not None:
            if isinstance(value, str):
                if value == "rise":
                    self._in_direction = str(value)
                elif value == "fall":
                    self._in_direction = str(value)
                else:
                    raise ValueError(f'Harness input direction must be "rise" or "fall", not {value}')
            else:
                raise TypeError(f'Invalid type for harness input direction: {type(value)}')
        else:
            raise ValueError(f'Invalid value for harness input direction: {value}')

    @property
    def target_inport_val(self) -> str:
        # TODO: Deprecate
        if self.in_direction == 'rise':
            return '01'
        elif self.in_direction == 'fall':
            return '10'

    @property
    def out_direction(self) -> str:
        return self._out_direction

    @out_direction.setter
    def out_direction(self, value: str):
        if value is not None:
            if isinstance(value, str):
                if value == "rise":
                    self._out_direction = str(value)
                elif value == "fall":
                    self._out_direction = str(value)
                else:
                    raise ValueError(f'Harness output direction must be "rise" or "fall", not {value}')
            else:
                raise TypeError(f'Invalid type for harness output direction: {type(value)}')
        else:
            raise ValueError(f'Invalid value for harness output direction: {value}')

    @property
    def target_outport_val(self) -> str:
        # TODO: Deprecate
        if self.out_direction == 'rise':
            return '01'
        elif self.out_direction == 'fall':
            return '10'

    @property
    def direction_prop(self) -> str:
        return f'cell_{self.out_direction}'

    @property
    def direction_tran(self) -> str:
        return f'{self.out_direction}_transition'

    @property
    def direction_power(self) -> str:
        return f'{self.out_direction}_power'
    
    def _calc_leakage_power(self, in_slope, out_load, vdd_voltage: float):
        i_vdd_leak = abs(self.results[in_slope][out_load]['i_vdd_leak'])
        i_vss_leak = abs(self.results[in_slope][out_load]['i_vss_leak'])
        avg_current = (i_vdd_leak + i_vss_leak) / 2
        return avg_current * vdd_voltage
    
    def get_leakage_power(self, vdd_voltage, power_unit: EngineeringUnit):
        leakage_power = 0
        n = 0
        for slope in self.results.keys():
            for load in self.results[slope].keys():
                leakage_power += self._calc_leakage_power(slope, load, vdd_voltage)
                n += 1
        leakage_power = leakage_power / n / power_unit.magnitude
        return leakage_power

    def _get_lut_value_groups_by_key(self, in_slopes, out_loads, unit, key: str):
        value_groups = []
        for in_slope in in_slopes:
            values = [self.results[str(in_slope)][str(out_load)][key]/unit for out_load in out_loads]
            value_groups.append(f'"{", ".join(["{:f}".format(value) for value in values])}"')
        return f'values({", ".join(value_groups)});'

    def get_propagation_delay_lut(self, in_slopes, out_loads, time_unit: EngineeringUnit) -> list:
        lines = [f'index_1("{", ".join([str(slope) for slope in in_slopes])}");']
        lines.append(f'index_2("{", ".join([str(load) for load in out_loads])}");')
        lines.append(self._get_lut_value_groups_by_key(in_slopes, out_loads, time_unit.magnitude, 'prop_in_out'))
        return lines

    def get_transition_delay_lut(self, in_slopes, out_loads, time_unit: EngineeringUnit):
        lines = [f'index_1("{", ".join([str(slope) for slope in in_slopes])}");']
        lines.append(f'index_2("{", ".join([str(load) for load in out_loads])}");')
        lines.append(self._get_lut_value_groups_by_key(in_slopes, out_loads, time_unit.magnitude, 'trans_out'))
        return lines

    def _calc_internal_energy(self, in_slope: str, out_load: str, energy_meas_high_threshold_voltage: float):
        """Calculates internal energy for a particular slope/load combination"""
        # Fetch calculation parameters
        # TODO: Check units. Currently we treat results as if they are in base units - unsure whether this is correct
        e_start = self.results[in_slope][out_load]['energy_start']
        e_end = self.results[in_slope][out_load]['energy_end']
        q_vdd_dyn = self.results[in_slope][out_load]['q_vdd_dyn']
        q_vss_dyn = self.results[in_slope][out_load]['q_vss_dyn']
        i_vdd_leak = abs(self.results[in_slope][out_load]['i_vdd_leak'])
        i_vss_leak = abs(self.results[in_slope][out_load]['i_vss_leak'])
        # Perform the calculation
        energy_delta = e_end - e_start
        avg_current = (i_vdd_leak + i_vss_leak) / 2
        internal_charge = min(q_vss_dyn, q_vdd_dyn) - energy_delta * avg_current
        return abs(internal_charge * energy_meas_high_threshold_voltage)

    def get_internal_energy_lut(self, in_slopes, out_loads, v_eth: float, e_unit: EngineeringUnit):
        lines = [f'index_1("{", ".join([str(slope) for slope in in_slopes])}");']
        lines.append(f'index_2("{", ".join([str(load) for load in out_loads])}");')
        energy_groups = []
        for in_slope in in_slopes:
            energies = [self._calc_internal_energy(str(in_slope), str(out_load), v_eth)/e_unit.magnitude for out_load in out_loads]
            energy_groups.append(f'"{", ".join(["{:f}".format(energy) for energy in energies])}"')
        lines.append(f'values({", ".join(energy_groups)})')
        return lines

class CombinationalHarness (Harness):
    def __init__(self, target_cell: LogicCell, test_vector) -> None:
        super().__init__(target_cell, test_vector)

    @property
    def timing_type(self) -> str:
        return "combinational"

    @property
    def timing_sense(self) -> str:
        # Determine timing_sense from target i/o directions
        if self.in_direction == self.out_direction:
            return 'positive_unate'
        else:
            return 'negative_unate'


class SequentialHarness (Harness):
    def __init__(self, target_cell: SequentialCell, test_vector) -> None:
        super().__init__(target_cell, test_vector)
        self.clock = target_cell.clock  # Clock pin
        self.set = target_cell.set      # Set pin (optional)
        self.reset = target_cell.reset  # Reset pin (optional)

        # TODO