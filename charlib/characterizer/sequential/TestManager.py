"""Test orchestration for sequential cells"""

import numpy as np
import matplotlib.pyplot as plt

from PySpice import Circuit, Simulator
from PySpice.Unit import *

from charlib.characterizer.sequential.Harness import SequentialHarness
from charlib.characterizer.procedures.PinCapacitance import ac_sweep as measure_input_capacitance
from charlib.characterizer.Harness import find_harness_by_arc
from charlib.characterizer.TestManager import TestManager, _parse_triggered_pin, _flip_direction
from charlib.liberty.cell import Cell, Pin, TimingData, TableTemplate

class SequentialTestManager(TestManager):
    """A sequential cell test manager"""

    def __init__(self, name: str, in_ports: list, out_ports: list, clock: str, flops: str, function: str, **kwargs):
        super().__init__(name, in_ports, out_ports, function, **kwargs)
        # TODO: Use flops in place of functions for sequential cells
        self.set = kwargs.get('set')
        self.reset = kwargs.get('reset')
        self.clock = clock
        self.flops = flops

        self._clock_slew = kwargs.get('clock_slew', 0)

        # Setup and Hold time search parameters
        self.setup_time_range = kwargs.get('setup_time_range', [0.1, 1])
        self.hold_time_range = kwargs.get('hold_time_range', [0.1, 1])

    @property
    def clock(self) -> Pin:
        """Return clock pin"""
        return self.cell[self.clock_name]

    @property
    def clock_name(self) -> str:
        """Return clock pin name."""
        return self._clock_name

    @property
    def clock_trigger(self) -> str:
        """Return clock trigger type."""
        return self._clock_trigger

    @clock.setter
    def clock(self, value: str):
        """Assign clock trigger and pin"""
        (self._clock_trigger, pin) = _parse_triggered_pin(value, 'clock')
        self._clock_name = pin.name
        self.cell.add_pin(pin.name, pin.direction, pin.role)

    @property
    def clock_slew(self) -> float:
        """Return clock slew rate"""
        if self.in_slews and not self._clock_slew:
            return min(self.in_slews)
        return float(self._clock_slew)

    @property
    def set(self):
        """Return set pin"""
        return self.cell.pins.get(self.set_name)

    @property
    def set_name(self) -> str:
        """Return set pin name"""
        return self._set_name

    @property
    def set_trigger(self) -> str:
        "Return set pin trigger type"
        return self._set_trigger

    @set.setter
    def set(self, value):
        """Assign set pin and trigger"""
        if value is not None:
            (self._set_trigger, pin) = _parse_triggered_pin(value, 'set')
            self._set_name = pin.name
            self.cell.add_pin(pin.name, pin.direction, pin.role)
        else:
            self._set_name = None

    @property
    def reset(self):
        """Return reset pin"""
        return self.cell.pins.get(self.reset_name)

    @property
    def reset_name(self) -> str:
        """Return reset pin name"""
        return self._reset_name

    @property
    def reset_trigger(self) -> str:
        """Return reset trigger type"""
        return self._reset_trigger

    @reset.setter
    def reset(self, value):
        """Assign reset pin and trigger"""
        if value is not None:
            (self._reset_trigger, pin) = _parse_triggered_pin(value, 'reset')
            self._reset_name = pin.name
            self.cell.add_pin(pin.name, pin.direction, pin.role)
        else:
            self._reset_name = None

    @property
    def flops(self) -> list:
        # TODO: Use flops in place of functions for sequential cells
        return self._flops

    @flops.setter
    def flops(self, value):
        # TODO: Use flops in place of functions for sequential cells
        if isinstance(value, str):
            self._flops = value.split()
        elif isinstance(value, list):
            self._flops = value
        else:
            raise TypeError(f'Invalid type for sequential cell flop names: {type(value)}')

    def characterize(self, settings):
        """Run Delay, Recovery & Removal characterization for a sequential cell"""

        # IDEA: Refactor this into multiple distinct procedures:
        # - measure_capacitance
        # - measure_metastability_timings
        # - measure_transient_timings
        # Allow methods to be registered for each procedure so users can provide their own if
        # desired. User procedures will have to generate their own harnesses & circuits.

        # Measure input capacitance for all input pins
        in_cap_pins = [*self.in_ports, self.clock]
        if self.set:
            in_cap_pins += [self.set]
        if self.reset:
            in_cap_pins += [self.reset]
        for pin in in_cap_pins:
            input_capacitance = measure_input_capacitance(self, settings, pin.name) @ u_F
            self.cell[pin.name].capacitance = input_capacitance.convert(settings.units.capacitance.prefixed_unit).value

        # Save test results to cell
        normalize_t_units = lambda value: (value @ u_s).convert(settings.units.time.prefixed_unit).value

        # FIXME: pg_pins should not be added here, but this is the first place we have access to
        # the CharacterizationSettings after Cell init
        self.add_pg_pins(settings.vdd, settings.vss, settings.pwell, settings.nwell)

        for out_port in self.out_ports:
            unsorted_harnesses = []
            # Generate Harnesses and run characterization
            for test_vector in out_port.function.test_vectors:
                # Map pins
                inputs = out_port.function.operands
                state_map = dict(zip([*inputs, out_port.name], test_vector))
                state_map[self.clock.name] = '0101' if self.clock_trigger == 'posedge' else '1010'
                if self.set:
                    state_map[self.set.name] = '0' if self.set_trigger == 'posedge' else '1'
                if self.reset:
                    state_map[self.reset.name] = '0' if self.reset_trigger == 'posedge' else '1'
                # TODO: Add flops

                # Generate harness
                harness = SequentialHarness(self, state_map)
                trial_name = f'delay {self.cell.name} {harness.short_str()}'

                # Run characterization
                for slew in self.in_slews:
                    for load in self.out_loads:
                        harness.results[str(slew)][str(load)] = self._run_delay(settings, harness, slew, load, trial_name)
                unsorted_harnesses.append(harness)

            # TODO: Filter out harnesses that aren't worst-case conditions
            harnesses = unsorted_harnesses

            # Store timing results
            for in_port in self.in_ports: # TODO: Add set and reset
                index_1 = [str(slew) for slew in self.in_slews]
                index_2 = [str(load) for load in self.out_loads]

                # Set up timing groups and table templates
                clock_edge = 'rising' if self.clock_trigger == 'posedge' else 'falling'
                delay_template = TableTemplate()
                delay_template.name = f'delay_template_{len(index_1)}x{len(index_2)}'
                delay_template.variables = ['input_net_transition', 'total_output_net_capacitance']
                delay_timing = TimingData(out_port.name, f'{clock_edge}_edge')
                setup_template = TableTemplate()
                setup_template.name = f'setup_template_{len(index_1)}x{len(index_2)}'
                setup_template.variables = ['related_pin_transition', 'constrained_pin_transition']
                setup_timing = TimingData(self.clock_name, f'setup_{clock_edge}')
                hold_template = TableTemplate()
                hold_template.name = f'hold_template_{len(index_1)}x{len(index_2)}'
                hold_template.variables = setup_template.variables
                hold_timing = TimingData(self.clock_name, f'hold_{clock_edge}')
                for direction in ['rise', 'fall']:
                    # Fetch and format data for timing tables
                    harness = find_harness_by_arc(harnesses, in_port, out_port, direction)
                    prop_values = []
                    tran_values = []
                    setup_values = []
                    hold_values = []
                    for slew in index_1:
                        for load in index_2:
                            result = harness.results[slew][load]
                            prop_values.append(f'{normalize_t_units(result["prop_in_out"]):7f}')
                            tran_values.append(f'{normalize_t_units(result["trans_out"]):7f}')
                            setup_values.append(f'{normalize_t_units(result["t_setup"]):7f}')
                            hold_values.append(f'{normalize_t_units(result["t_hold"]):7f}')

                    # Store propagation and transient delays on the output pin
                    delay_timing.add_table(f'cell_{direction}', delay_template, prop_values, index_1, index_2)
                    delay_timing.add_table(f'{direction}_transition', delay_template, tran_values, index_1, index_2)

                    # Store setup and hold constraints on the input pin
                    setup_timing.add_table(f'{direction}_constraint', setup_template, setup_values, index_1, index_2)
                    hold_timing.add_table(f'{direction}_constraint', hold_template, hold_values, index_1, index_2)

                # Add timing groups to pins
                self.cell[out_port.name].timings.append(delay_timing)
                self.cell[in_port.name].timings.append(setup_timing)
                self.cell[in_port.name].timings.append(hold_timing)

            # TODO: Store internal power results

            # Display plots
            if 'io' in self.plots:
                [self.plot_io(settings, harness) for harness in harnesses]
            if 'delay' in self.plots:
                [self.cell[out_pin.name].plot_delay(settings, self.cell.name) for out_pin in self.out_ports]
            if 'energy' in self.plots:
                pass # TODO
            if plt.get_figlabels():
                plt.tight_layout()
                plt.show()

        return self.cell

    def _run_delay(self, settings, harness: SequentialHarness, slew, load, trial_name):
        """Run a single sequential delay trial"""
        # Set up slew and load parameters
        t_slew = slew * settings.units.time
        c_load = load * settings.units.capacitance
        debug_path = settings.debug_dir / self.cell.name / 'delay' / harness.debug_path / \
                     f'slew_{slew}' / f'load_{load}'

        if not settings.quiet:
            print(f'Running sequential {trial_name} with slew={str(t_slew)}, load={str(c_load)}')
        t_stab = self._find_stabilizing_time(settings, harness, t_slew, c_load, debug_path)
        (t_setup, t_hold) = self._find_setup_hold_delay(settings, harness, t_slew, c_load, t_stab, debug_path)

        # Characterize using identified setup and hold time
        simulation, timings = self._build_test_circuit('delay', settings, harness, t_slew, c_load, t_setup, t_hold, t_stab)
        return self._measure_cell_delays(settings, harness, simulation, timings, debug_path)

    def _find_stabilizing_time(self, settings, harness, t_slew, c_load, debug_path):
        """Find a reasonable stablilizing time for the current configuration.

        The stabilizing time is the delay between the first half of the procedure, where we zero
        out any initial state, and the second half of the procedure, where we measure delay
        characteristics. It's important to minimize stabilizing time as it has a major effect on
        total simulation time."""
        # Run a single simulation and measure the time it takes for the Q output to change from 1%
        # of vdd to 99% of vdd
        t_stab = 500 * max(self.in_slews) * settings.units.time
        t_setup = max(self.setup_time_range) * settings.units.time
        t_hold = max(self.hold_time_range) * settings.units.time
        sim, t = self._build_test_circuit('stabilizing', settings, harness, t_slew, c_load, t_setup, t_hold, t_stab)

        # Measure time it takes for Q to stabilize
        match harness.out_direction:
            case 'rise':
                v_start = 0.01 * settings.vdd.voltage
                v_end = 0.99 * settings.vdd.voltage
            case 'fall':
                v_start = 0.99 * settings.vdd.voltage
                v_end = 0.01 * settings.vdd.voltage
        sim.measure(
            'tran', 't_stabilizing',
            f'trig v(vout) val={v_start} {harness.out_direction}=1',
            f'targ v(vout) val={v_end} {harness.out_direction}=1',
            run=False
        )

        # Log simulation
        if settings.debug:
            debug_path.mkdir(parents=True, exist_ok=True)
            with open(debug_path/'stabilizing.sp', 'w') as spice_file:
                spice_file.write(str(sim))

        step_time = t['sim_end']/5000 # Run with low precision
        results = sim.transient(step_time=step_time, end_time=t['sim_end'])
        return results['t_stabilizing'] @ u_s

    def _find_setup_hold_delay(self, settings, harness, t_slew, c_load, t_stabilizing, debug_path):
        """Calculate setup and hold time.

        Calculate the minimum setup and hold time for the current configuration, accounting for
        interdependence between the two. Uses the procedure proposed by Salman et. al.; See
        https://ieeexplore.ieee.org/document/4167994"""
        # Identify msp
        th = max(self.hold_time_range) * settings.units.time
        t_setup_min = self._sweep_ts(settings, harness, t_slew, c_load, t_stabilizing, th, 'ts_min', debug_path)
        t_hold_max = self._sweep_th(settings, harness, t_slew, c_load, t_stabilizing, t_setup_min, 'th_max', debug_path)

        # Identify mhp
        ts = max(self.setup_time_range) * settings.units.time
        t_hold_min = self._sweep_th(settings, harness, t_slew, c_load, t_stabilizing, ts, 'th_min', debug_path)
        t_setup_max = self._sweep_ts(settings, harness, t_slew, c_load, t_stabilizing, t_hold_min, 'ts_max', debug_path)

        # Interpolate mshp along the contour formed by msp, mhp
        # For now we use a simple average, which may be overly pessimistic
        # We'll also increase setup by 40% as a sort of "safety factor"
        mshp = (1.4*(t_setup_min+t_setup_max)/2, (t_hold_min+t_hold_max)/2)
        return mshp

    def _sweep_ts(self, settings, harness, t_slew, c_load, t_stabilizing, t_hold, title, debug_path):
        """Perform a binary search to find the minimum viable t_setup with the given t_hold"""
        t_step = self.sim_timestep * settings.units.time
        ts_max = max(self.setup_time_range) * settings.units.time
        ts_min = min(self.setup_time_range) * settings.units.time
        ts = ts_max
        i = 0
        while ts - ts_min > t_step:
            i += 1
            sim, t = self._build_test_circuit(f'{title}_{i}', settings, harness, t_slew, c_load, ts, t_hold, t_stabilizing)
            try:
                self._measure_c2q(settings, harness, sim, t, debug_path)
            except NameError:
                ts_min = ts
                ts = (ts_max + ts_min) / 2
                continue
            ts_max = ts
            ts = (ts_max + ts_min) / 2
        return ts_max

    def _sweep_th(self, settings, harness, t_slew, c_load, t_stabilizing, t_setup, title, debug_path):
        """Perform a binary search to find the minimum viable t_hold with the given t_setup"""
        t_step = self.sim_timestep * settings.units.time
        th_max = max(self.hold_time_range) * settings.units.time
        th_min = min(self.hold_time_range) * settings.units.time
        th = th_max
        i = 0
        while th - th_min > t_step:
            i += 1
            sim, t = self._build_test_circuit(f'{title}_{i}', settings, harness, t_slew, c_load, t_setup, th, t_stabilizing)
            try:
                self._measure_c2q(settings, harness, sim, t, debug_path)
            except NameError:
                th_min = th
                th = (th_max + th_min) / 2
                continue
            th_max = th
            th = (th_max + th_min) / 2
        return th_max

    def _build_test_circuit(self, title, settings, harness, t_slew, c_load, t_setup, t_hold, t_stabilizing):
        """Construct the circuit simulation object with the provided test parameters"""
        # Set up parameters
        clk_slew = self.clock_slew * settings.units.time
        vdd = settings.vdd.voltage * settings.units.voltage
        vss = settings.vss.voltage * settings.units.voltage

        # Set up timing parameters for clock and data events
        t = {}
        t['clk_edge_1_start'] = t_setup
        t['clk_edge_1_end'] = t['clk_edge_1_start'] + clk_slew
        t['clk_edge_2_start'] = t['clk_edge_1_end'] + max(t_setup, t_hold)
        t['clk_edge_2_end'] = t['clk_edge_2_start'] + clk_slew
        t['removal'] = t['clk_edge_2_end'] + t_hold # initial state has now been zeroed out
        t['data_edge_1_start'] = t['removal'] + t_stabilizing # wait for the system to stabilize
        t['data_edge_1_end'] = t['data_edge_1_start'] + t_slew
        t['clk_edge_3_start'] = t['data_edge_1_start'] + t_slew/2 + t_setup + clk_slew/2
        t['clk_edge_3_end'] = t['clk_edge_3_start'] + clk_slew
        t['data_edge_2_start'] = t['clk_edge_3_start'] + clk_slew/2 + t_hold + t_slew/2
        t['data_edge_2_end'] = t['data_edge_2_start'] + t_slew
        t['sim_end'] = t['data_edge_2_end'] + 2*t_stabilizing # wait for the system to stabilize

        # Initialize circuit
        circuit = Circuit(title)
        self._include_models(circuit)
        circuit.include(self.netlist)
        circuit.V('high', 'vhigh', circuit.gnd, vdd)
        circuit.V('low', 'vlow', circuit.gnd, vss)
        circuit.V('dd_dyn', 'vdd_dyn', circuit.gnd, vdd)
        circuit.V('ss_dyn', 'vss_dyn', circuit.gnd, vss)
        circuit.V('o_cap', 'vout', 'wout', 0)
        circuit.C('0', 'wout', 'vss_dyn', c_load)

        # Set up clock input
        (v0, v1) = (vdd, vss) if harness.timing_type_clock == 'falling_edge' else (vss, vdd)
        circuit.PieceWiseLinearVoltageSource('cin', 'vcin', circuit.gnd, values=[
            (0, v0),
            (t['clk_edge_1_start'], v0),
            (t['clk_edge_1_end'], v1),
            (t['clk_edge_2_start'], v1),
            (t['clk_edge_2_end'], v0),
            (t['clk_edge_3_start'], v0),
            (t['clk_edge_3_end'], v1),
            (t['sim_end'], v1)
        ])

        # Set up data input node
        (v0, v1) = (vss, vdd) if harness.in_direction == 'rise' else (vdd, vss)
        circuit.PieceWiseLinearVoltageSource('in', 'vin', circuit.gnd, values=[
            (0, v0),
            (t['data_edge_1_start'], v0),
            (t['data_edge_1_end'], v1),
            (t['data_edge_2_start'], v1),
            (t['data_edge_2_end'], v0),
            (t['sim_end'], v0)
        ])

        # Set up set and reset node
        if harness.reset:
            circuit.V('rin', 'vrin', circuit.gnd, vdd if harness.reset.state == '1' else vss)
        if harness.set:
            circuit.V('sin', 'vsin', circuit.gnd, vdd if harness.set.state == '1' else vss)

        # Initialize device under test subcircuit and wire up ports
        ports = self.definition().upper().split()[1:]
        connections = [ports.pop(0)]
        for port in ports:
            if port == harness.target_in_port.pin.name:
                connections.append('vin')
            elif port == harness.target_out_port.pin.name:
                connections.append('vout')
            elif port == settings.vdd.name.upper():
                connections.append('vdd_dyn')
            elif port == settings.vss.name.upper():
                connections.append('vss_dyn')
            elif port == harness.clock.pin.name:
                connections.append('vcin')
            elif self.reset and port == harness.reset.pin.name:
                connections.append('vrin')
            elif self.set and port == harness.set.pin.name:
                connections.append('vsin')
            elif port in [pin.pin.name for pin in harness.stable_in_ports]:
                for stable_port in harness.stable_in_ports:
                    if port == stable_port.pin.name:
                        if stable_port.state == '1':
                            connections.append('vhigh')
                        elif stable_port.state == '0':
                            connections.append('vlow')
                        else:
                            raise ValueError(f'Invalid state identified during simulation setup for port {port}: {state}')
            else:
                connections.append('wfloat0') # Float any unrecognized ports
        if len(connections) is not len(ports)+1:
            raise ValueError(f'Failed to match all ports identified in definition "{self.definition().strip()}"')
        circuit.X('dut', *connections)

        # Initialize simulation
        simulator = Simulator.factory(simulator=settings.simulator)
        simulation = simulator.simulation(
            circuit,
            temperature=settings.temperature,
            nominal_temperature=settings.temperature
        )

        return simulation, t

    def _measure_cell_delays(self, settings, harness, simulation, timings, debug_path):
        """Run delay measurement for a single test circuit."""

        # Set up voltage bounds for measurements
        pct_vdd = lambda x : x * settings.vdd.voltage
        match harness.in_direction:
            case 'rise':
                v_prop_start = settings.logic_threshold_low_to_high
            case 'fall':
                v_prop_start = settings.logic_threshold_high_to_low
        match harness.out_direction:
            case 'rise':
                v_prop_end = settings.logic_threshold_low_to_high
                v_trans_start = settings.logic_threshold_low
                v_trans_end = settings.logic_threshold_high
            case 'fall':
                v_prop_end = settings.logic_threshold_high_to_low
                v_trans_start = settings.logic_threshold_high
                v_trans_end = settings.logic_threshold_low
        match harness.timing_type_clock:
            case 'rising_edge':
                clk_direction = 'rise'
                v_clk_transition = settings.logic_threshold_low_to_high
            case 'falling_edge':
                clk_direction = 'fall'
                v_clk_transition = settings.logic_threshold_high_to_low

        # Measure propagation delay from first data edge to last output edge
        simulation.measure(
            'tran', 'prop_in_out',
            f'trig v(vin) val={pct_vdd(v_prop_start)} td={float(timings["removal"])} {harness.in_direction}=1',
            f'targ v(vout) val={pct_vdd(v_prop_end)} {harness.out_direction}=last',
            run=False
        )

        # Measure transient delay from first data edge to first output edge
        simulation.measure(
            'tran', 'trans_out',
            f'trig v(vout) val={pct_vdd(v_trans_start)} td={float(timings["removal"])} {harness.out_direction}=1',
            f'targ v(vout) val={pct_vdd(v_trans_end)} {harness.out_direction}=1',
            run=False
        )

        # Measure setup delay from first data edge to last clock edge
        simulation.measure(
            'tran', 't_setup',
            f'trig v(vin) val={pct_vdd(v_prop_start)} td={float(timings["removal"])} {harness.in_direction}=1',
            f'targ v(vcin) val={pct_vdd(v_clk_transition)} {clk_direction}=last',
            run=False
        )

        # Measure hold delay from last clock edge to last data edge
        simulation.measure(
            'tran', 't_hold',
            f'trig v(vcin) val={pct_vdd(v_clk_transition)} td={float(timings["removal"])} {clk_direction}=last',
            f'targ v(vin) val={pct_vdd(v_prop_end)} {_flip_direction(harness.in_direction)}=last',
            run=False
        )

        # Log simulation
        if settings.debug:
            debug_path.mkdir(parents=True, exist_ok=True)
            with open(debug_path/'delay.sp', 'w') as spice_file:
                spice_file.write(str(simulation))

        step_time = min(self.sim_timestep*settings.units.time, timings['sim_end']/1000)
        simulation.options('autostop', 'nopage', 'nomod', post=1, ingold=2)
        return simulation.transient(step_time=step_time, end_time=timings['sim_end'])

    def _measure_c2q(self, settings, harness, simulation, timings, debug_path):
        """Measure Clock-to-Q delay."""

        # Measure clock-to-latch time
        match harness.timing_type_clock:
            case 'rising_edge':
                clk_direction = 'rise'
                v_clk_transition = settings.logic_threshold_low_to_high * settings.vdd.voltage
            case 'falling_edge':
                clk_direction = 'fall'
                v_clk_transition = settings.logic_threshold_high_to_low * settings.vdd.voltage
        match harness.out_direction:
            case 'rise':
                v_prop_end = settings.logic_threshold_low_to_high * settings.vdd.voltage
            case 'fall':
                v_prop_end = settings.logic_threshold_high_to_low * settings.vdd.voltage
        simulation.measure('tran', 't_c2q',
            f'trig v(vcin) val={v_clk_transition} td={float(timings["removal"])} {clk_direction}=last',
            f'targ v(vout) val={v_prop_end} {harness.out_direction}=last',
            run=False
        )

        # Log simulation
        if settings.debug:
            debug_path = debug_path / 'c2q'
            debug_path.mkdir(parents=True, exist_ok=True)
            with open(debug_path/f'{simulation.circuit.title}.sp', 'w') as spice_file:
                spice_file.write(str(simulation))

        step_time = min(self.sim_timestep*settings.units.time, t['sim_end']/1000)
        simulation.options('autostop', 'nopage', 'nomod', post=1, ingold=2)
        return simulation.transient(step_time=step_time, end_time=timings['sim_end'])

    def plot_io(self, settings, harness):
        """Plot I/O voltages vs time"""
        # TODO: Look for ways to generate fewer plots here - maybe a creative 3D plot
        figures = []
        # Group data by slew rate so that inputs are the same
        for slew in self.in_slews:
            for load in self.out_loads:
                # Add axes for clk, s, r, d, q (in that order)
                # Use an additive approach in case some of those aren't present
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
                ratios = np.ones(num_axes).tolist()
                ratios[-1] = num_axes
                figure, axes = plt.subplots(num_axes,
                    sharex=True,
                    height_ratios=ratios,
                    label=f'{self.cell.name} | {harness.short_str()}'
                )

                # Set up plots
                for ax in axes:
                    for level in [settings.logic_threshold_low, settings.logic_threshold_high]:
                        ax.axhline(level*settings.vdd.voltage, color='0.5', linestyle='--')
                    # TODO: Set up vlines for important timing events
                    ax.set_yticks([settings.vss.voltage, settings.vdd.voltage])
                volt_units = str(settings.units.voltage.prefixed_unit)
                time_units = str(settings.units.time.prefixed_unit)
                axes[CLK].set(
                    title=f'Slew Rate: {str(slew*settings.units.time)} | Fanout: {str(load*settings.units.capacitance)}',
                    ylabel=f'CLK [{volt_units}]'
                )
                if self.set:
                    axes[S].set_ylabel(f'S [{volt_units}]')
                if self.reset:
                    axes[R].set_ylabel(f'R [{volt_units}]')
                axes[D].set_ylabel(f'D [{volt_units}]')
                axes[Q].set_ylabel(f'Q [{volt_units}]')
                axes[-1].set_xlabel(f'Time [{str(settings.units.time.prefixed_unit)}]')
                analysis = harness.results[str(slew)][str(load)]
                t = analysis.time / settings.units.time
                axes[CLK].plot(t, analysis.vcin)
                if self.set:
                    axes[S].plot(t, analysis.vsin)
                if self.reset:
                    axes[R].plot(t, analysis.vrin)
                axes[D].plot(t, analysis.vin)
                axes[Q].plot(t, analysis.vout)

                figures.append(figure)
        return figures
