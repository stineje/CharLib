import matplotlib.pyplot as plt
import numpy as np
from PySpice.Unit import *

class BaseHarness:
    """A Harness encapsulates wiring configuration for testing a cell.

    Harnesses capture information about how a standard cell should be
    connected during testing. Think 'wiring harness'."""

    def __init__(self, cell, *target_ports, **kwargs) -> None:
        """Create a new Harness.

        Harnesses can be initialized one of two ways:
        - by specifying one or more target input(s) and zero or more
        target output(s)
        - OR by supplying a test vector using the `test_vector` kwarg
        
        If a test vector is supplied, provided target inputs and
        outputs will be ignored."""

        if 'test_vector' not in kwargs:
            # Parse input ports
            self._target_in_ports = []
            self._nontarget_in_ports = []
            for port in cell.in_ports:
                if port.name in target_ports:
                    self._target_in_ports.append(port)
                else:
                    self._nontarget_in_ports.append(port)
            # Parse output ports
            self._target_out_ports = []
            self._nontarget_out_ports = []
            for port in cell.out_ports:
                if port.name in target_ports:
                    self._target_out_ports.append(port)
                else:
                    self._nontarget_out_ports.append(port)
            # Handle other ports
            for port in {*target_ports}.difference(cell.in_ports, cell.out_ports):
                print(port)


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
                self._target_in_port = in_port.name.upper()
                self._target_in_port_state = state
            else:
                self._stable_in_ports.append(in_port.name.upper())
                self._stable_in_port_states.append(state)

        # Get outputs from test vector
        for out_port, state in zip(target_cell.out_ports, output_test_vector):
            if len(state) > 1:
                self._target_out_port = out_port.name.upper()
                self._target_out_port_state = state
            else:
                self._nontarget_out_ports.append(out_port.name.upper())
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
    
    def short_str(self):
        # Create an abbreviated string for the test vector represented by this harness
        # TODO: Replace this with a method that generates the test vector string (if possible)
        harness_str = f'{self.target_in_port}={"01" if self.in_direction == "rise" else "10"}'
        for input, state in zip(self.stable_in_ports, self.stable_in_port_states):
            harness_str += f' {input}={state}'
        harness_str += f' {self.target_out_port}={"01" if self.out_direction == "rise" else "10"}'
        for output, state in zip(self.nontarget_out_ports, self.nontarget_out_port_states):
            harness_str += f' {output}={state}'
        return harness_str

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

    def average_input_capacitance(self, vdd: float):
        """Calculates the average input capacitance over all trials"""
        total_capacitance = 0.0 @ u_F
        n = 0
        for slope in self.results.keys():
            for load in self.results[slope].keys():
                # TODO: Correct for cases where q is negative
                q = self.results[slope][load]['q_in_dyn'] @ u_C
                total_capacitance += q / (vdd @ u_V)
                n += 1
        return total_capacitance / n
    
    def minimum_input_capacitance(self, vdd: float):
        """Finds the minimum measured input capacitance"""
        # Find minimum q
        q = min([self.results[slope][load]['q_in_dyn'] for slope in self.results.keys() for load in self.results[slope].keys()]) @ u_C
        return q / (vdd @ u_V)

    def average_transition_delay(self):
        """Calculates the average transition delay over all trials"""
        # TODO: Usually we want longest transport delay instead of average
        total_delay = 0.0 @ u_s
        n = 0
        for slope in self.results.keys():
            for load in self.results[slope].keys():
                total_delay += self.results[slope][load]['trans_out'] @ u_s
                n += 1
        return total_delay / n
    
    def average_propagation_delay(self):
        """Calculates the average propagation delay over all trials"""
        # TODO: Usually we want longest prop delay instead of average
        total_delay = 0.0 @ u_s
        n = 0
        for slope in self.results.keys():
            for load in self.results[slope].keys():
                total_delay += self.results[slope][load]['prop_in_out'] @ u_s
                n += 1
        return total_delay / n

    def _calc_leakage_power(self, slew, load, vdd: float):
        # Calculate leakage power, using units to validate calculation
        i_vdd_leak = abs(self.results[slew][load]['i_vdd_leak']) @ u_A
        i_vss_leak = abs(self.results[slew][load]['i_vss_leak']) @ u_A
        i_avg = (i_vdd_leak + i_vss_leak) / 2
        return i_avg * (vdd @ u_V)
    
    def get_leakage_power(self, vdd: float):
        """Calculates the average leakage power over all trials"""
        leakage_power = 0.0 @ u_W
        n = 0
        for slew in self.results.keys():
            for load in self.results[slew].keys(): 
                leakage_power += self._calc_leakage_power(slew, load, vdd)
                n += 1
        return leakage_power / n

    def _get_lut_value_groups_by_key(self, slews, loads, key: str, base_unit, output_unit):
        value_groups = []
        for slew in slews:
            values = [(self.results[str(slew)][str(load)][key]@base_unit).convert(output_unit).value for load in loads]
            value_groups.append(f'"{", ".join([f"{value:f}" for value in values])}"')
        sep = ', \\\n  '
        return f'values( \\\n  {sep.join(value_groups)});'

    def get_propagation_delay_lut(self, in_slews, out_loads, time_unit) -> list:
        lines = [f'index_1("{", ".join([str(slew) for slew in in_slews])}");']
        lines.append(f'index_2("{", ".join([str(load) for load in out_loads])}");')
        values = self._get_lut_value_groups_by_key(in_slews, out_loads, 'prop_in_out', u_s, time_unit)
        [lines.append(value_line) for value_line in values.split('\n')]
        return lines

    def get_transport_delay_lut(self, in_slews, out_loads, time_unit):
        lines = [f'index_1("{", ".join([str(slew) for slew in in_slews])}");']
        lines.append(f'index_2("{", ".join([str(load) for load in out_loads])}");')
        values = self._get_lut_value_groups_by_key(in_slews, out_loads, 'trans_out', u_s, time_unit)
        [lines.append(value_line) for value_line in values.split('\n')]
        return lines

    def _calc_internal_energy(self, slew: str, load: str, energy_meas_high_threshold_voltage: float):
        """Calculates internal energy for a particular slope/load combination"""
        # Fetch calculation parameters, using units to validate calculation
        slew = str(slew)
        load = str(load)
        t_start = self.results[slew][load]['t_energy_start'] @ u_s
        t_end = self.results[slew][load]['t_energy_end'] @ u_s
        q_vdd_dyn = self.results[slew][load]['q_vdd_dyn'] @ u_C
        q_vss_dyn = self.results[slew][load]['q_vss_dyn'] @ u_C
        i_vdd_leak = abs(self.results[slew][load]['i_vdd_leak']) @ u_A
        i_vss_leak = abs(self.results[slew][load]['i_vss_leak']) @ u_A
        # Perform the calculation
        time_delta = (t_end - t_start)
        avg_current = ((i_vdd_leak + i_vss_leak) / 2)
        internal_charge = min(abs(q_vss_dyn), abs(q_vdd_dyn)) - time_delta * avg_current
        return internal_charge * (energy_meas_high_threshold_voltage @ u_V)

    def get_internal_energy_lut(self, in_slews, out_loads, v_eth: float, energy_unit):
        lines = [f'index_1("{", ".join([str(slope) for slope in in_slews])}");']
        lines.append(f'index_2("{", ".join([str(load) for load in out_loads])}");')
        energy_groups = []
        for slew in in_slews:
            energies = [self._calc_internal_energy(str(slew), str(out_load), v_eth) for out_load in out_loads]
            energy_groups.append(f'"{", ".join(["{:f}".format(float(energy.convert(energy_unit).value)) for energy in energies])}"')
        sep = ', \\\n  '
        [lines.append(value_line) for value_line in f'values( \\\n  {sep.join(energy_groups)});'.split('\n')]
        return lines

class CombinationalHarness (Harness):
    def __init__(self, target_cell, test_vector) -> None:
        super().__init__(target_cell, test_vector)
        # Error if we don't have a target input port
        if not self._target_in_port:
            raise ValueError(f'Unable to parse target input port from test vector {test_vector}')

    @property
    def timing_type(self) -> str:
        return "combinational"

    def plot_io(self, settings, slews, loads, cell_name):
        """Plot I/O voltages vs time for the given slew rates and output loads"""
        # TODO: Evaluate whether a 3d plot might be apt here instead of creating a huge number of 2d plots
        # Group data by slew rate so that Vin is the same
        for slew in slews:
            # Generate plots for Vin and Vout
            figure, (ax_i, ax_o) = plt.subplots(2, sharex=True, height_ratios=[3, 7])
            figure.suptitle(f'Cell {cell_name} | Arc: {self.target_in_port} ({self.in_direction}) -> {self.target_out_port} ({self.out_direction}) | Slew Rate: {str(slew * settings.units.time)}')

            # Set up plot parameters
            ax_i.set_ylabel(f'Vin (pin {self.target_in_port}) [{str(settings.units.voltage.prefixed_unit)}]')
            ax_i.set_title('I/O Voltage vs. Time')
            ax_o.set_ylabel(f'Vout (pin {self.target_out_port}) [{str(settings.units.voltage.prefixed_unit)}]')
            ax_o.set_xlabel(f'Time [{str(settings.units.time.prefixed_unit)}]')

            # Add dotted lines indicating logic levels, energy measurement bounds, and timing
            for ax in [ax_i, ax_o]:
                ax.grid()
                for level in [settings.logic_threshold_low_voltage(), settings.logic_threshold_high_voltage()]:
                    ax.axhline(level, color='0.5', linestyle='--')
                for level in [settings.energy_meas_low_threshold_voltage(), settings.energy_meas_high_threshold_voltage()]:
                    ax.axhline(level, color='g', linestyle=':')
                for t in [slew, 2*slew]:
                    ax.axvline(float(t), color='r', linestyle=':')

            # Plot simulation data
            # Input is plotted once per slew rate group
            # Output is plotted by fanout (aka output capacitive load)
            for load in loads:
                data = self.results[str(slew)][str(load)]
                ax_o.plot(data.time / settings.units.time, data['vout'], label=f'Fanout={load*settings.units.capacitance}')
            ax_i.plot(data.time / settings.units.time, data['vin'])
            ax_o.legend()

    def plot_delay(self, settings, slews, loads, cell_name):
        """Plot propagation delay and transport delay vs slew rate vs fanout"""
        figure = plt.figure()
        figure.suptitle(f'Cell {cell_name} | Arc: {self.target_in_port} ({self.in_direction}) -> {self.target_out_port} ({self.out_direction})')

        ax = figure.add_subplot(projection='3d')
        ax.set_proj_type('ortho')

        # Tabulate delay data
        prop_data = []
        tran_data = []
        for slew in slews:
            prop_row = []
            tran_row = []
            for load in loads:
                prop_delay = self.results[str(slew)][str(load)]['prop_in_out'] @ u_s
                prop_row.append(float(prop_delay.convert(settings.units.time.prefixed_unit).value))
                tran_delay = self.results[str(slew)][str(load)]['trans_out'] @ u_s
                tran_row.append(float(tran_delay.convert(settings.units.time.prefixed_unit).value))
            prop_data.append(prop_row)
            tran_data.append(tran_row)

        # Expand x and y vectors to 2d arrays
        x_data = np.repeat(np.expand_dims(slews, 1), len(loads), 1)
        y_data = np.swapaxes(np.repeat(np.expand_dims(loads, 1), len(slews), 1), 0, 1)

        # Plot delay data
        p = ax.plot_surface(x_data, y_data, np.asarray(prop_data), edgecolor='red', cmap='inferno', alpha=0.3, label='Propagation Delay')
        p._edgecolors2d = p._edgecolor3d # Workaround for legend. See https://stackoverflow.com/questions/54994600/pyplot-legend-poly3dcollection-object-has-no-attribute-edgecolors2d
        p._facecolors2d = p._facecolor3d # Workaround for legend
        t = ax.plot_surface(x_data, y_data, np.asarray(tran_data), edgecolor='blue', cmap='viridis', alpha=0.3, label='Transport Delay')
        t._edgecolors2d = t._edgecolor3d # Workaround for legend
        t._facecolors2d = t._facecolor3d # Workaround for legend
        ax.set(xlabel=f'Slew Rate [{str(settings.units.time.prefixed_unit)}]',
               ylabel=f'Fanout [{str(settings.units.capacitance.prefixed_unit)}]',
               zlabel=f'Delay [{str(settings.units.time.prefixed_unit)}]',
               title='Transport and Propagation delay vs. Slew Rate vs. Fanout')
        ax.legend()

    def plot_energy(self, settings, slews, loads, cell_name):
        """Plot energy vs slew rate vs fanout"""
        figure = plt.figure()
        figure.suptitle(f'Cell {cell_name} | Arc: {self.target_in_port} ({self.in_direction}) -> {self.target_out_port} ({self.out_direction})')

        ax = figure.add_subplot(projection='3d')
        ax.set_proj_type('ortho')

        energy_data = []
        for slew in slews:
            energy_row = []
            for load in loads:
                energy = self._calc_internal_energy(slew, load, settings.energy_meas_high_threshold_voltage())
                energy_row.append(float(energy.convert(settings.units.energy.prefixed_unit).value))
            energy_data.append(energy_row)

        # Expand x and y vectors to 2d arrays
        x_data = np.repeat(np.expand_dims(slews, 1), len(loads), 1)
        y_data = np.swapaxes(np.repeat(np.expand_dims(loads, 1), len(slews), 1), 0, 1)

        # Plot energy data
        ax.plot_surface(x_data, y_data, np.asarray(energy_data), cmap='viridis', label='Energy')
        ax.set(xlabel=f'Slew Rate [{str(settings.units.time.prefixed_unit)}]',
               ylabel=f'Fanout [{str(settings.units.capacitance.prefixed_unit)}]',
               zlabel=f'Energy [{str(settings.units.energy.prefixed_unit)}]',
               title='Energy vs. Slew Rate vs. Fanout')

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
        self.clock = target_cell.clock_name
        self.clock_state = test_vector.pop(0)
        # Set up Reset
        if target_cell.reset:
            self.reset = target_cell.reset_name
            self.reset_state = test_vector.pop(0)
            if len(self.reset_state) > 1:
                self._target_in_port = self.reset
        # Set up Set
        if target_cell.set:
            self.set = target_cell.set_name
            self.set_state = test_vector.pop(0)
            if len(self.set_state) > 1:
                # Overwrite reset if already assigned
                self._target_in_port = self.set
        # Set up flop internal states
        for flop in target_cell.flops:
            self.flops.append(flop)
            self.flop_states.append(test_vector.pop(0))
        super().__init__(target_cell, test_vector)

    def short_str(self):
        harness_str = f'{self.clock}={self.clock_state} {super().short_str()}'
        if self.set:
            harness_str += f' {self.set}={self.set_state}'
        if self.reset:
            harness_str += f' {self.reset}={self.reset_state}'
        return harness_str

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

    def plot_io(self, settings, slews, loads, title):
        """Plot I/O voltages vs time for the given slew rates and output loads"""
        # TODO: evaluate display options and try to find a better way of displaying these
        for slew in slews:
            for load in loads:
                # Create a figure with axes for CLK, S (if present), R (if present) D, and Q in that order
                # Use an additive approach so that we have keys for indexing the axes
                num_axes = 1
                CLK = 0
                if self.set:
                    S = num_axes
                    num_axes += 1
                if self.reset:
                    R = num_axes
                    num_axes += 1
                D = num_axes
                num_axes += 1
                Q = num_axes
                num_axes += 1
                ratios=np.ones(num_axes).tolist()
                ratios[-1] = num_axes
                figure, axes = plt.subplots(num_axes, sharex=True, height_ratios=ratios)
                figure.suptitle(f'{title} | {self.short_str()}')

                # Set up plots
                for ax in axes:
                    for level in [settings.logic_threshold_low_voltage(), settings.logic_threshold_high_voltage()]:
                        ax.axhline(level, color='0.5', linestyle='--')
                    # TODO: Set up vlines for important timing events
                    ax.set_yticks([settings.vss.voltage, settings.vdd.voltage])
                axes[CLK].set_title(f'Slew Rate: {str(slew*settings.units.time)} | Fanout: {str(load*settings.units.capacitance)}')
                axes[CLK].set_ylabel(f'CLK [{str(settings.units.voltage.prefixed_unit)}]')
                if self.set:
                    axes[S].set_ylabel(f'S [{str(settings.units.voltage.prefixed_unit)}]')
                if self.reset:
                    axes[R].set_ylabel(f'R [{str(settings.units.voltage.prefixed_unit)}]')
                axes[D].set_ylabel(f'D [{str(settings.units.voltage.prefixed_unit)}]')
                axes[Q].set_ylabel(f'Q [{str(settings.units.voltage.prefixed_unit)}]')
                for level in [settings.energy_meas_low_threshold_voltage(), settings.energy_meas_high_threshold_voltage()]:
                    axes[Q].axhline(level, color='g', linestyle=':')
                axes[-1].set_xlabel(f'Time [{str(settings.units.time.prefixed_unit)}]')

                # Plot simulation data
                data = self.results[str(slew)][str(load)]
                t = data.time / settings.units.time
                axes[Q].plot(t, data['vout'])
                axes[CLK].plot(t, data['vcin'])
                if self.set:
                    axes[S].plot(t, data['vsin'])
                if self.reset:
                    axes[R].plot(t, data['vrin'])
                axes[D].plot(t, data['vin'])
                axes[Q].plot(t, data['vout'])

    def plot_delay(self, settings, slews, loads, cell_name):
        pass

    def plot_energy(self, settings, slews, loads, cell_name):
        pass

# Utilities for working with Harnesses
def filter_harnesses_by_ports(harness_list: list, in_port, out_port) -> list:
    """Finds harnesses in harness_list which target in_port and out_port"""
    return [harness for harness in harness_list 
            if harness.target_in_port.upper() == in_port.name.upper()
            and harness.target_out_port.upper() == out_port.name.upper()]

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