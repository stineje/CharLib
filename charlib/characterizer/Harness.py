from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from PySpice.Unit import *

from charlib.liberty.cell import Pin

@dataclass
class PinTestBinding:
    """Associates a pin to test data, such as state"""
    pin: Pin
    state: str = '0'

    @property
    def direction(self) -> str:
        """Return pin state change direction (if applicable)"""
        if self.state.startswith(('01', 'z1')):
            return 'rise'
        elif self.state.startswith(('10', 'z0')):
            return 'fall'
        else:
            return None

    def __str__(self) -> str:
        return f'{self.pin.name}{self.state}'


class Harness:
    """Characterization parameters for one path through a cell.

    The primary purpose of a Harness is to map pins to states. At simulation time this serves as a
    "wiring harness", telling the TestManager how to wire up the cell for a particular test."""

    def __init__(self, test_manager, pin_state_map: dict) -> None:
        """Create a new Harness"""

        # Parse pin state mapping and set up PinTestBindings
        self._stable_in_ports = []
        self._nontarget_ports = []
        for pin in test_manager.cell.pins.values():
            if pin.name in pin_state_map:
                # Add to targeted or stable ports
                state = pin_state_map[pin.name]
                if state == 'ignore':
                    continue
                binding = PinTestBinding(pin, state)
                if len(state) > 1:
                    if pin.direction == 'input':
                        self._target_in_port = binding
                    elif pin.direction == 'output':
                        self._target_out_port = binding
                else:
                    if pin.direction == 'input':
                        self._stable_in_ports.append(binding)
            else:
                # Add to nontargeted ports
                self._nontarget_ports.append(PinTestBinding(pin))

        # Initialize results from test input slopes and loads
        self.results = {}
        for slew in test_manager.in_slews:
            self.results[str(slew)] = {}
            for load in test_manager.out_loads:
                self.results[str(slew)][str(load)] = {}

    def __str__(self) -> str:
        """Return str(self)"""
        lines = [f'Arc Under Test: {self.arc_str()}']
        if self.stable_in_ports:
            lines.append('    Stable Input Ports:')
            for in_port in self.stable_in_ports:
                lines.append(f'        {in_port.pin.name}: {in_port.state}')
        if self.nontarget_ports:
            lines.append('    Nontarget Ports:')
            for out_port in self.nontarget_ports:
                lines.append(f'        {out_port.pin.name}: {out_port.state}')
        # TODO: Display results if available
        return '\n'.join(lines)

    def short_str(self):
        """Create an abbreviated string for the test vector represented by this harness"""
        harness_str = f'{self.target_in_port.pin.name}={self.target_in_port.state}'
        for in_port in self.stable_in_ports:
            harness_str += f' {in_port.pin.name}={in_port.state}'
        harness_str += f' {self.target_out_port.pin.name}={self.target_out_port.state}'
        for out_port in self.nontarget_ports:
            harness_str += f' {out_port.pin.name}={out_port.state}'
        return harness_str

    def arc_str(self):
        """Return a string representing the test arc"""
        return f'{self.target_in_port.pin.name} ({self.in_direction}) to {self.target_out_port.pin.name} ({self.out_direction})'

    @property
    def target_in_port(self) -> str:
        """Return target input port"""
        return self._target_in_port

    @property
    def stable_in_ports(self) -> list:
        """Return list of stable input ports"""
        return self._stable_in_ports

    @property
    def target_out_port(self) -> str:
        """Return target output ports"""
        return self._target_out_port

    @property
    def nontarget_ports(self) -> list:
        """Return list of nontarget ports"""
        return self._nontarget_ports

    @property
    def in_direction(self) -> str:
        """Return target_in_port.direction"""
        return self.target_in_port.direction

    @property
    def out_direction(self) -> str:
        """Return target_out_port.direction"""
        return self.target_out_port.direction

    @property
    def debug_path(self) -> str:
        """Return folder names for debug results related to this harness."""
        arc_dir = f'{self.target_in_port}_to_{self.target_out_port}'
        stable_dir = '_'.join([str(pin) for pin in self.stable_in_ports])
        return f'{arc_dir}/{stable_dir}'

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

# Utilities for working with Harnesses
def filter_harnesses_by_ports(harness_list: list, in_port, out_port) -> list:
    """Finds harnesses in harness_list which target in_port and out_port"""
    return [harness for harness in harness_list
            if harness.target_in_port.pin == in_port
            and harness.target_out_port.pin == out_port]

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
