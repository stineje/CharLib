"""Encapsulates a cell's external interfaces"""

from enum import StrEnum, Flag

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
