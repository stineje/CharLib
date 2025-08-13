"""Test orchestration for combinational cells"""

import matplotlib.pyplot as plt

from PySpice.Unit import *

from charlib.characterizer.combinational.Harness import CombinationalHarness
from charlib.characterizer.procedures.PinCapacitance import ac_sweep as measure_input_capacitance
from charlib.characterizer.procedures.CombinationalDelay import measure_delays_for_arc
from charlib.characterizer.Harness import filter_harnesses_by_ports, find_harness_by_arc
from charlib.characterizer.TestManager import TestManager
from charlib.liberty.cell import Cell, Pin, TimingData, TableTemplate

class CombinationalTestManager(TestManager):
    """Manage test harnesses for a combinational cell"""

    def characterize(self, settings):
        """Characterize a combinational cell"""

        # Input capacitance measurements
        def measure_pin_cap(in_port):
            input_capacitance = measure_input_capacitance(self, settings, in_port.name) @ u_F
            return input_capacitance.convert(settings.units.capacitance.prefixed_unit).value

        #  Delay measurements
        def measure_delays(out_port):
            harnesses = [measure_delays_for_arc(self, settings, out_port, tv) for tv in out_port.function.test_vectors]
            timings = []
            for in_port in self.in_ports:
                delay_timing = TimingData(in_port.name)
                for direction in ['rise', 'fall']:
                    arc_harnesses = [harness for harness in filter_harnesses_by_ports(harnesses, in_port, out_port) if harness.out_direction == direction]
                    # Find the worst-case harness for each arc. This is known to be overly pessimistic.
                    # FIXME: To improve accuracy, take a weighted average of arcs based on traversal likelihood.
                    # FIXME: Should all harnesses be written to file, with `when` conditions?
                    worst_case_harness = arc_harnesses[0]
                    for harness in arc_harnesses:
                        if worst_case_harness.sum_propagation_delay() < harness.sum_propagation_delay():
                            worst_case_harness = harness
                    if 'io' in self.plots:
                        self.plot_io(settings, worst_case_harness)
                    delay_timing.merge(worst_case_harness.to_timingdata(settings.units.time.prefixed_unit))
                timings.append(delay_timing)
            if 'delay' in self.plots:
                self.cell[out_port.name].plot_delay(settings, self.cell.name)
            return timings

        # TODO: Consider dispatching jobs to other threads rather than executing them sequentially here
        for pin in self.in_ports:
            self.cell[pin.name].capacitance = measure_pin_cap(pin)
        for pin in self.out_ports:
            self.cell[pin.name].timings.extend(measure_delays(pin))

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
