"""Test orchestration for combinational cells"""

import matplotlib.pyplot as plt

from PySpice import Circuit, Simulator
from PySpice.Unit import *

from charlib.characterizer.combinational.Harness import CombinationalHarness
from charlib.characterizer.Harness import filter_harnesses_by_ports, find_harness_by_arc
from charlib.characterizer.TestManager import TestManager
from charlib.liberty.cell import Cell, Pin, TimingData, TableTemplate

class CombinationalTestManager(TestManager):
    """Manage test harnesses for a combinational cell"""

    def characterize(self, settings):
        """Characterize a combinational cell"""
        # Measure input capacitance for all input pins
        for pin in self.in_ports:
            input_capacitance = self._run_input_capacitance(settings, pin.name) @ u_F
            self.cell[pin.name].capacitance = input_capacitance.convert(settings.units.capacitance.prefixed_unit).value

        # FIXME: pg_pins should not be added here, but this is the first place we have access to
        # the CharacterizationSettings after Cell init
        self.add_pg_pins(settings.vdd, settings.vss, settings.pwell, settings.nwell)

        # Run delay simulation for all test vectors of each function
        for out_port in self.out_ports:
            unsorted_harnesses = []
            # Run characterization
            for test_vector in out_port.function.test_vectors:
                # Map pins to test vector
                inputs = out_port.function.operands
                state_map = dict(zip([*inputs, out_port.name], test_vector))

                # Generate harness
                harness = CombinationalHarness(self, state_map)
                trial_name = f'delay {self.cell.name} {harness.short_str()}'

                # Run delay characterization
                for slew in self.in_slews:
                    for load in self.out_loads:
                        self._run_delay(settings, harness, slew, load, trial_name)
                unsorted_harnesses.append(harness)

            # Filter out harnesses that aren't worst-case conditions
            # We should be left with the critical path rise and fall harnesses for each i/o path
            harnesses = []
            for in_port in self.in_ports:
                for direction in ['rise', 'fall']:
                    # Iterate over harnesses that match output, input, and direction
                    matching_harnesses = [harness for harness in filter_harnesses_by_ports(unsorted_harnesses, in_port, out_port) if harness.out_direction == direction]
                    worst_case_harness = matching_harnesses[0]
                    for harness in matching_harnesses:
                        # FIXME: Currently we compare by average prop delay. Consider alternative strategies
                        if worst_case_harness.average_propagation_delay() < harness.average_propagation_delay():
                            worst_case_harness = harness # This harness is worse
                    harnesses.append(worst_case_harness)

            # Store propagation and transient delay in pin timing tables
            for in_port in self.in_ports:
                delay_timing = TimingData(in_port.name)
                for direction in ['rise', 'fall']:
                    # Identify the correct harness
                    harness = find_harness_by_arc(harnesses, in_port, out_port, direction)

                    # Construct the table
                    index_1 = [str(slew) for slew in self.in_slews]
                    index_2 = [str(load) for load in self.out_loads]
                    prop_values = []
                    tran_values = []
                    for slew in index_1:
                        for load in index_2:
                            result = harness.results[slew][load]
                            prop_value = (result['prop_in_out'] @ u_s).convert(settings.units.time.prefixed_unit).value
                            prop_values.append(f'{prop_value:7f}')
                            tran_value = (result['trans_out'] @ u_s).convert(settings.units.time.prefixed_unit).value
                            tran_values.append(f'{tran_value:7f}')
                    template = TableTemplate()
                    template.name = f'delay_template_{len(index_1)}x{len(index_2)}'
                    template.variables = ['input_net_transition', 'total_output_net_capacitance']
                    delay_timing.add_table(f'cell_{direction}', template, prop_values, index_1, index_2)
                    delay_timing.add_table(f'{direction}_transition', template, tran_values, index_1, index_2)
                self.cell[out_port.name].timings.append(delay_timing)

            # Display plots
            if 'io' in self.plots:
                [self.plot_io(settings, harness) for harness in harnesses]
            if 'delay' in self.plots:
                [self.cell[out_pin.name].plot_delay(settings, self.cell.name) for out_pin in self.out_ports]
            if 'energy' in self.plots:
                print("Energy plotting not yet supported") # TODO: Add correct energy measurement procedure
            if plt.get_figlabels():
                plt.tight_layout()
                plt.show()

        return self.cell

    def _run_delay(self, settings, harness: CombinationalHarness, slew, load, trial_name):
        if not settings.quiet:
            print(f'Running {trial_name} with slew={slew*settings.units.time}, load={load*settings.units.capacitance}')
        harness.results[str(slew)][str(load)] = self._run_delay_trial(settings, harness, slew, load)

    def _run_delay_trial(self, settings, harness: CombinationalHarness, slew, load):
        """Run delay measurement for a single trial"""
        # Set up parameters
        data_slew = slew * settings.units.time
        t_start = data_slew
        t_end = t_start + data_slew
        t_simend = 10000 * data_slew
        vdd = settings.vdd.voltage * settings.units.voltage
        vss = settings.vss.voltage * settings.units.voltage

        # Initialize circuit
        circuit = Circuit(f'{self.cell.name}_delay')
        self._include_models(circuit)
        circuit.include(self.netlist)
        (v_start, v_end) = (vss, vdd) if harness.in_direction == 'rise' else (vdd, vss)
        pwl_values = [(0, v_start), (t_start, v_start), (t_end, v_end), (t_simend, v_end)]
        circuit.PieceWiseLinearVoltageSource('in', 'vin', circuit.gnd, values=pwl_values)
        circuit.V('high', 'vhigh', circuit.gnd, vdd)
        circuit.V('low', 'vlow', circuit.gnd, vss)
        circuit.V('dd_dyn', 'vdd_dyn', circuit.gnd, vdd)
        circuit.V('ss_dyn', 'vss_dyn', circuit.gnd, vss)
        circuit.V('o_cap', 'vout', 'wout', circuit.gnd)
        circuit.C('0', 'wout', 'vss_dyn', load * settings.units.capacitance)

        # Initialize device under test subcircuit and wire up ports
        ports = self.definition().upper().split()[1:]
        subcircuit_name = ports.pop(0)
        connections = []
        for port in ports:
            if port == harness.target_in_port.pin.name:
                connections.append('vin')
            elif port == harness.target_out_port.pin.name:
                connections.append('vout')
            elif port == settings.vdd.name.upper():
                connections.append('vdd_dyn')
            elif port == settings.vss.name.upper():
                connections.append('vss_dyn')
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
        if len(connections) is not len(ports):
            raise ValueError(f'Failed to match all ports identified in definition "{self.definition().strip()}"')
        circuit.X('dut', subcircuit_name, *connections)

        # Initialize simulation
        simulator = Simulator.factory(simulator=settings.simulator)
        simulation = simulator.simulation(
            circuit,
            temperature=settings.temperature,
            nominal_temperature=settings.temperature
        )
        simulation.options('autostop', 'nopage', 'nomod', post=1, ingold=2, trtol=1)

        # Measure delay
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
        simulation.measure(
            'tran', 'prop_in_out',
            f'trig v(vin) val={pct_vdd(v_prop_start)} {harness.in_direction}=1',
            f'targ v(vout) val={pct_vdd(v_prop_end)} {harness.out_direction}=1',
            run=False
        )
        simulation.measure(
            'tran', 'trans_out',
            f'trig v(vout) val={pct_vdd(v_trans_start)} {harness.out_direction}=1',
            f'targ v(vout) val={pct_vdd(v_trans_end)} {harness.out_direction}=1',
            run=False
        )

        # Log simulation
        # Path should be debug_dir/cell_name/delay/arc/slew/load/
        if settings.debug:
            debug_path = settings.debug_dir / self.cell.name / 'delay' / harness.debug_path / \
                         f'slew_{slew}' / f'load_{load}'
            debug_path.mkdir(parents=True, exist_ok=True)
            with open(debug_path/'delay.sp', 'w') as spice_file:
                spice_file.write(str(simulation))

        # Run transient analysis
        # TODO: May need to add probes before running?
        step_time = min(self.sim_timestep*settings.units.time, t_simend/1000)
        return simulation.transient(step_time=step_time, end_time=t_simend)

    def plot_io(self, settings, harness):
        """Plot I/O voltages vs time"""
        # TODO: Look for ways to generate fewer plots here - maybe a creative 3D plot
        figures = []
        # Group data by slew rate so that inputs are the same
        for slew in self.in_slews:
            # Generate plots for Vin and Vout
            figure, (ax_i, ax_o) = plt.subplots(2,
                sharex=True,
                height_ratios=[3, 7],
                label=f'{self.cell.name} | {harness.arc_str()} | {str(slew*settings.units.time)}'
            )
            volt_units = str(settings.units.voltage.prefixed_unit)
            time_units = str(settings.units.time.prefixed_unit)
            ax_i.set(
                ylabel=f'Vin (pin {harness.target_in_port.pin.name}) [{volt_units}]',
                title='I/O Voltages vs. Time'
            )
            ax_o.set(
                ylabel=f'Vout (pin {harness.target_out_port.pin.name}) [{volt_units}]',
                xlabel=f'Time [{time_units}]'
            )
            for load in self.out_loads:
                analysis = harness.results[str(slew)][str(load)]
                ax_o.plot(analysis.time / settings.units.time, analysis.vout, label=f'Fanout={load*settings.units.capacitance}')
            ax_o.legend()
            ax_i.plot(analysis.time / settings.units.time, analysis.vin)

            # Add lines indicating logic levels and timing
            for ax in [ax_i, ax_o]:
                ax.grid()
                for level in [settings.logic_threshold_low, settings.logic_threshold_high]:
                    ax.axhline(level*settings.vdd.voltage, color='0.5', linestyle='--')
                for t in [slew, 2*slew]:
                    ax.axvline(float(t), color='r', linestyle=':')

            figures.append(figure)
        return figures
