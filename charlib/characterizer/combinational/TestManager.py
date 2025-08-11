"""Test orchestration for combinational cells"""

import matplotlib.pyplot as plt

from PySpice import Circuit, Simulator
from PySpice.Unit import *

from charlib.characterizer.combinational.Harness import CombinationalHarness
from charlib.characterizer.procedures.Procedure import Procedure
from charlib.characterizer.procedures.PinCapacitance import ac_sweep as measure_input_capacitance
from charlib.characterizer.procedures.CombinationalDelay import measure_tran_prop as measure_delays
from charlib.characterizer.Harness import filter_harnesses_by_ports, find_harness_by_arc
from charlib.characterizer.TestManager import TestManager
from charlib.liberty.cell import Cell, Pin, TimingData, TableTemplate

class CombinationalTestManager(TestManager):
    """Manage test harnesses for a combinational cell"""

    def _measure_pin_cap(self, pin_name: str, settings):
        input_capacitance = measure_input_capacitance(self, settings, pin_name) @ u_F
        return (pin_name, input_capacitance.convert(settings.units.capacitance.prefixed_unit).value)

    def _measure_delays(self, out_port: str, settings):
        harnesses = [measure_delays(self, settings, out_port, tv) for tv in out_port.function.test_vectors]
        for in_port in self.in_ports:
            delay_timing = TimingData(in_port.name)
            for direction in ['rise', 'fall']:
                arc_harnesses = [harness for harness in filter_harnesses_by_ports(harnesses, in_port, out_port) if harness.out_direction == direction]
                # Find the worst-case harness for each arc. This is known to be overly pessimistic.
                # FIXME: To improve accuracy, take a weighted average of arcs based on traversal likelihood.
                worst_case_harness = arc_harnesses[0]
                for harness in arc_harnesses:
                    if worst_case_harness.sum_propagation_delay() < harness.sum_propagation_delay():
                        worst_case_harness = harness
                delay_timing.merge(worst_case_harness.to_timingdata(settings.units.time.prefixed_unit))
            return (out_port.name, delay_timing)

    def setup_measurements(self, settings):
        """Construct an ordered list of measurement procedures for later execution."""
        measurements = [Procedure(self._measure_pin_cap, pin.name, settings) for pin in self.in_ports]
        measurements += [Procedure(self._measure_delays, pin, settings) for pin in self.out_ports]
        return measurements

    def characterize(self, settings):
        """Characterize a combinational cell"""
        # Measure input capacitance for all input pins
        for pin in self.in_ports:
            input_capacitance = measure_input_capacitance(self, settings, pin.name) @ u_F
            self.cell[pin.name].capacitance = input_capacitance.convert(settings.units.capacitance.prefixed_unit).value

        # Run delay simulation for all test vectors of each function
        for out_port in self.out_ports:
            unsorted_harnesses = []
            for test_vector in out_port.function.test_vectors:
                unsorted_harnesses.append(measure_delays(self, settings, out_port, test_vector))

            # Find and store the critical path rise and fall harnesses for each i/o path
            for in_port in self.in_ports:
                delay_timing = TimingData(in_port.name)
                for direction in ['rise', 'fall']:
                    # Iterate over harnesses that match output, input, and direction
                    matching_harnesses = [harness for harness in filter_harnesses_by_ports(unsorted_harnesses, in_port, out_port) if harness.out_direction == direction]
                    worst_case_harness = matching_harnesses[0]
                    for harness in matching_harnesses:
                        # FIXME: Currently we compare by average prop delay. Consider alternative strategies
                        if worst_case_harness.sum_propagation_delay() < harness.sum_propagation_delay():
                            worst_case_harness = harness # This harness is worse
                    if 'io' in self.plots:
                        self.plot_io(settings, worst_case_harness)
                    delay_timing.merge(harness.to_timingdata(settings.units.time.prefixed_unit))
                self.cell[out_port.name].timings.append(delay_timing)
            if 'delay' in self.plots:
                self.cell[out_port.name].plot_delay(settings, self.cell.name)

        # Show plots
        if plt.get_figlabels():
            plt.tight_layout()
            plt.show()

        return self.cell

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
