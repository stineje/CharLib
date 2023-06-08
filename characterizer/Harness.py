from PySpice.Unit import *

class Harness:
    """Characterization parameters for one path through a cell
    
    A Harness defines characterization parameters from one input to one
    output of a standard cell circuit. The target input port and output
    port are defined by the value of test_vector passed to the
    constructor."""

    def __init__(self, target_cell, test_vector: list) -> None:
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
        self.results =  {}                      # nested dictionary of characterization results grouped by in_slew and out_load

        # Parse inputs from test vector
        # Test vector should be formatted like [in1, ..., inN, out1, ..., outM]
        num_inputs = len(target_cell.in_ports)
        num_outputs = len(target_cell.out_ports)
        input_test_vector = test_vector[0:num_inputs]
        output_test_vector = test_vector[num_inputs:num_inputs+num_outputs]

        # Get inputs from test vector
        for in_port, state in zip(target_cell.in_ports, input_test_vector):
            if len(state) > 1:
                self._target_in_port = in_port.lower()
                self._target_in_port_state = state
            else:
                self._stable_in_ports.append(in_port.lower())
                self._stable_in_port_states.append(state)

        # Get outputs from test vector
        for out_port, state in zip(target_cell.out_ports, output_test_vector):
            if len(state) > 1:
                self._target_out_port = out_port.lower()
                self._target_out_port_state = state
            else:
                self._nontarget_out_ports.append(out_port.lower())
                self._nontarget_out_port_states.append(state)
        if not self._target_out_port:
            raise ValueError(f'Unable to parse target output port from test vector {test_vector}')

        # Initialize results from target_cell input slopes and loads
        for in_slew in target_cell.in_slews:
            self.results[str(in_slew)] = {}
            for out_load in target_cell.out_loads:
                self.results[str(in_slew)][str(out_load)] = {}

    def __str__(self) -> str:
        lines = []
        lines.append(f'Arc Under Test: {self.target_in_port} ({self.in_direction}) -> {self.target_out_port} ({self.out_direction})')
        if self.stable_in_ports:
            lines.append(f'    Stable Input Ports:')
            for port, state in zip(self.stable_in_ports, self.stable_in_port_states):
                lines.append(f'        {port}: {state}')
        if self.nontarget_out_ports:
            lines.append(f'    Nontarget Output Ports:')
            for port, state in zip(self.nontarget_out_ports, self.nontarget_out_port_states):
                lines.append(f'        {port}: {state}')
        # TODO: Display results if available
        return '\n'.join(lines)

    def _state_to_direction(self, state) -> str:
        return 'rise' if state == '01' else 'fall' if state == '10' else None

    @property
    def target_in_port(self) -> str:
        return self._target_in_port

    @property
    def target_in_port_state(self) -> str:
        return self._target_in_port_state

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
    def target_out_port_state(self) -> str:
        return self._target_out_port_state

    @property
    def nontarget_out_ports(self) -> list:
        return self._nontarget_out_ports

    @property
    def nontarget_out_port_states(self) -> list:
        return self._nontarget_out_port_states

    @property
    def in_direction(self) -> str:
        return self._state_to_direction(self.target_in_port_state)

    @property
    def out_direction(self) -> str:
        return self._state_to_direction(self.target_out_port_state)

    @property
    def direction_prop(self) -> str:
        return f'cell_{self.out_direction}'

    @property
    def direction_tran(self) -> str:
        return f'{self.out_direction}_transition'

    @property
    def direction_power(self) -> str:
        return f'{self.out_direction}_power'

    @property
    def timing_sense(self) -> str:
        # Determine timing_sense from target i/o directions
        if self.in_direction == self.out_direction:
            return 'positive_unate'
        else:
            return 'negative_unate'

    def average_input_capacitance(self, vdd_voltage) -> float:
        """Calculates the average input capacitance over all trials"""
        # TODO: Usually we want minimum input capacitance instead of average
        input_capacitance = 0.0 @ u_F
        n = 0
        for slope in self.results.keys():
            for load in self.results[slope].keys():
                # TODO: Correct for cases where q is negative
                q = self.results[slope][load]['q_in_dyn']
                input_capacitance += q / vdd_voltage
                n += 1
        input_capacitance = input_capacitance / n
        return input_capacitance

    def average_transition_delay(self) -> float:
        """Calculates the average transition delay over all trials"""
        # TODO: Usually we want longest transport delay instead of average
        total_delay = 0.0 @ u_s
        n = 0
        for slope in self.results.keys():
            for load in self.results[slope].keys():
                total_delay += self.results[slope][load]['trans_out']
                n += 1
        return total_delay / n
    
    def average_propagation_delay(self) -> float:
        """Calculates the average propagation delay over all trials"""
        # TODO: Usually we want longest prop delay instead of average
        total_delay = 0.0 @ u_s
        n = 0
        for slope in self.results.keys():
            for load in self.results[slope].keys():
                total_delay += self.results[slope][load]['prop_in_out']
                n += 1
        return total_delay / n

    def _calc_leakage_power(self, in_slew, out_load, vdd_voltage: float):
        i_vdd_leak = abs(self.results[in_slew][out_load]['i_vdd_leak'])
        i_vss_leak = abs(self.results[in_slew][out_load]['i_vss_leak'])
        avg_current = (i_vdd_leak + i_vss_leak) / 2
        return avg_current * vdd_voltage
    
    def get_leakage_power(self, vdd_voltage):
        """Calculates the average leakage power over all trials"""
        leakage_power = 0.0 @ u_J
        n = 0
        for slope in self.results.keys():
            for load in self.results[slope].keys():
                leakage_power += self._calc_leakage_power(slope, load, vdd_voltage)
                n += 1
        leakage_power = leakage_power / n
        return leakage_power

    def _get_lut_value_groups_by_key(self, in_slews, out_loads, key: str):
        value_groups = []
        for slew in in_slews:
            values = [self.results[str(slew)][str(load)][key] for load in out_loads]
            value_groups.append(f'"{", ".join([f"{value:f}" for value in values])}"')
        sep = ', \\\n  '
        return f'values( \\\n  {sep.join(value_groups)});'

    def get_propagation_delay_lut(self, in_slews, out_loads) -> list:
        lines = [f'index_1("{", ".join([str(slew) for slew in in_slews])}");']
        lines.append(f'index_2("{", ".join([str(load) for load in out_loads])}");')
        values = self._get_lut_value_groups_by_key(in_slews, out_loads, 'prop_in_out')
        [lines.append(value_line) for value_line in values.split('\n')]
        return lines

    def get_transport_delay_lut(self, in_slews, out_loads):
        lines = [f'index_1("{", ".join([str(slew) for slew in in_slews])}");']
        lines.append(f'index_2("{", ".join([str(load) for load in out_loads])}");')
        values = self._get_lut_value_groups_by_key(in_slews, out_loads, 'trans_out')
        [lines.append(value_line) for value_line in values.split('\n')]
        return lines

    def _calc_internal_energy(self, in_slew: str, out_load: str, energy_meas_high_threshold_voltage: float):
        """Calculates internal energy for a particular slope/load combination"""
        # Fetch calculation parameters
        e_start = self.results[in_slew][out_load]['energy_start']
        e_end = self.results[in_slew][out_load]['energy_end']
        q_vdd_dyn = self.results[in_slew][out_load]['q_vdd_dyn']
        q_vss_dyn = self.results[in_slew][out_load]['q_vss_dyn']
        i_vdd_leak = abs(self.results[in_slew][out_load]['i_vdd_leak'])
        i_vss_leak = abs(self.results[in_slew][out_load]['i_vss_leak'])
        # Perform the calculation
        energy_delta = (e_end - e_start)
        avg_current = (i_vdd_leak + i_vss_leak) / 2
        internal_charge = min(abs(q_vss_dyn), abs(q_vdd_dyn)) - energy_delta * avg_current
        return internal_charge * energy_meas_high_threshold_voltage

    def get_internal_energy_lut(self, in_slews, out_loads, v_eth: float):
        lines = [f'index_1("{", ".join([str(slope) for slope in in_slews])}");']
        lines.append(f'index_2("{", ".join([str(load) for load in out_loads])}");')
        energy_groups = []
        for slew in in_slews:
            energies = [self._calc_internal_energy(str(slew), str(out_load), v_eth) for out_load in out_loads]
            energy_groups.append(f'"{", ".join(["{:f}".format(energy) for energy in energies])}"')
        sep = ', \\\n  '
        [lines.append(value_line) for value_line in f'values( \\\n  {sep.join(energy_groups)});'.split('\n')]
        return lines

class CombinationalHarness (Harness):
    def __init__(self, target_cell, test_vector) -> None:
        super().__init__(target_cell, test_vector)
        # Error if we don't have a target input port
        if not self._target_in_port:
            raise ValueError(f'Unable to parse target input port from test vector {test_vector}')

    def spice_infix(self):
        # Determine the infix for spice files dealing with this harness
        infix = f'{self.target_in_port}{"01" if self.in_direction == "rise" else "10"}'
        for input, state in zip(self.stable_in_ports, self.stable_in_port_states):
            infix += f'_{input}{state}'
        infix += f'_{self.target_out_port}{"01" if self.out_direction == "rise" else "10"}'
        for output, state in zip(self.nontarget_out_ports, self.nontarget_out_port_states):
            infix += f'_{output}{state}'
        return infix

    @property
    def timing_type(self) -> str:
        return "combinational"


class SequentialHarness (Harness):
    def __init__(self, target_cell, test_vector: list) -> None:
        # Parse internal storage states, clock, set, and reset out of test vector
        # For sequential harnesses, test vectors are in the format:
        # [clk, set, reset, flop1, ..., flopK, in1, ..., inN, out1, ..., outM]
        # Note that set and reset are optional, but must be provided if present
        # on the target cell
        self.set = None
        self.reset = None
        self.flops = []
        self.flop_states = []
        self.clock = target_cell.clock
        self.clock_state = test_vector.pop(0)
        # Set up Reset
        if target_cell.reset:
            self.reset = target_cell.reset
            self.reset_state = test_vector.pop(0)
            if len(self.reset_state) > 1:
                self._target_in_port = self.reset
        # Set up Set
        if target_cell.set:
            self.set = target_cell.set
            self.set_state = test_vector.pop(0)
            if len(self.set_state) > 1:
                # Overwrite reset if already assigned
                self._target_in_port = self.set
        # Set up flop internal states
        for flop in target_cell.flops:
            self.flops.append(flop)
            self.flop_states.append(test_vector.pop(0))
        super().__init__(target_cell, test_vector)

    @property
    def set_direction(self) -> str:
        if not self.set:
            return None
        return self._state_to_direction(self.set_state)

    @property
    def reset_direction(self) -> str:
        if not self.reset:
            return None
        return self._state_to_direction(self.reset_state)
    
    def invert_set_reset(self):
        self.set_state = self.set_state[::-1] if self.set_state else None
        self.reset_state = self.reset_state[::-1] if self.reset_state else None

    @property
    def timing_sense_constraint(self) -> str:
        # TODO: Check that this is correct
        return f'{self.in_direction}_constraint'

    def _timing_type_with_mode(self, mode) -> str:
        # Determine from target input and direction
        if self.set_direction or self.reset_direction:
            # We're targeting set or reset
            if mode == 'recovery':
                if self.in_direction == 'rise':
                    return f'{mode}_rising'
                else:
                    return f'{mode}_falling'
            elif mode == 'removal':
                if self.in_direction == 'rise':
                    return f'{mode}_falling'
                else:
                    return f'{mode}_rising'
            else:
                return None
        elif not self.target_in_port in [*self.flops]:
            # We're targeting an input port
            if mode == 'clock':
                if self.clock_state == '0101':
                    return 'falling_edge'
                else:
                    return 'rising_edge'
            elif mode in ['hold', 'setup']:
                if self.in_direction == 'rise':
                    return f'{mode}_rising'
                else:
                    return f'{mode}_falling'
        # If we get here, most likely the harness isn't configured correctly
        raise ValueError(f'Unable to determine timing type for mode "{mode}"')

    @property
    def timing_type_hold(self) -> str:
        return self._timing_type_with_mode('hold')

    @property
    def timing_type_setup(self) -> str:
        return self._timing_type_with_mode('setup')
    
    @property
    def timing_type_recovery(self) -> str:
        return self._timing_type_with_mode('recovery')
    
    @property
    def timing_type_removal(self) -> str:
        return self._timing_type_with_mode('removal')
    
    @property
    def timing_type_clock(self) -> str:
        return self._timing_type_with_mode('clock')
    
    @property
    def timing_when(self) -> str:
        if self.in_direction == 'rise':
            return self.target_in_port
        else:
            return f'!{self.target_in_port}'


# Utilities for working with Harnesses
def filter_harnesses_by_ports(harness_list: list, in_port, out_port) -> list:
    """Finds harnesses in harness_list which target in_port and out_port"""
    return [harness for harness in harness_list if harness.target_in_port == in_port and harness.target_out_port == out_port]

def find_harness_by_arc(harness_list: list, in_port, out_port, out_direction) -> Harness:
    harnesses = [harness for harness in filter_harnesses_by_ports(harness_list, in_port, out_port) if harness.out_direction == out_direction]
    if len(harnesses) > 1:
        raise LookupError('Multiple harnesses present in harness_list with the specified arc!')
    elif len(harnesses) < 1:
        raise LookupError('No harnesses present in harness_list with the specified arc!')
    return harnesses[0]

def check_timing_sense(harness_list: list):
    """Checks that all CombinationalHarnesses in harness_list have the same unateness."""
    for harness in harness_list:
        if not harness.timing_sense == harness_list[0].timing_sense:
            return "non_unate"
    return harness_list[0].timing_sense