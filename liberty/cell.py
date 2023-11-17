"""This module contains data structures used to read and write liberty files"""

from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt

class Cell:
    """A single standard cell"""
    def __init__(self, name: str, area: int=0, **attrs) -> None:
        """Create a new cell

        :param name: cell name
        :param area: cell area
        :param **attrs: additional liberty attributes, specified as key-value pairs"""

        self._name = name.upper()
        self.area = area
        self._attrs = attrs
        self.flops = []
        self.pins = {}

    @classmethod
    def from_str(value: str):
        """Parse a cell from a liberty string"""
        pass # TODO

    @property
    def name(self) -> str:
        """Return cell name"""
        return self._name

    def __getitem__(self, key: str):
        """Return self[key]. Searches pins by name."""
        return self.pins[key.upper()]

    def add_ff(self, in_node: str, out_node: str, next_state: str, clock: str, **attrs):
        """Add a new flop to this cell's list of flops"""
        ff = Flop(in_node, out_node, next_state, clock)
        for attr, value in attrs:
            setattr(ff, attr, value)
        self.flops.append()

    def add_pin(self, name: str, direction=None, role='io'):
        """Add a new pin to this cell's list of pins"""
        name = name.upper()
        self.pins[name] = Pin(name, direction, role)

    @property
    def attributes(self) -> dict:
        """Return extra liberty attributes for this cell"""
        return self._attrs

    def add_attribute(self, key: str, value: str):
        """Add a new liberty attribute to this cell"""
        self._attrs[key] = str(value)

    def is_pad_cell(self):
        """Return `True` if this cell contains any pad pins."""
        return 'pad' in [pin.role for pin in self.pins.values()]

    def templates(self) -> list:
        """Generate templates for all lookup tables in this cell's pins"""
        templates = []
        for pin in self.pins.values():
            templates.extend(pin.templates())
        return list(set(templates))

    def __str__(self) -> str:
        """Return str(self)"""
        lib_str = [f'cell ({self.name}) {{']
        if 'BUF' in self.name.upper():
            lib_str.append('  cell_footprint : buf;')
        elif 'INV' in self.name.upper():
            lib_str.append('  cell_footprint : inv;')
        lib_str.append(f'  area : {self.area};')
        if self.is_pad_cell():
            lib_str.append('  pad_cell : true;')
        for key, value in self.attributes:
            lib_str.append(f'  {key} : {value};')
        for flop in self.flops:
            for line in str(flop).split('\n'):
                lib_str.append(f'  {line}')
        for pin in dict(sorted(self.pins.items())).values():
            for line in str(pin).split('\n'):
                lib_str.append(f'  {line}')
        lib_str.append('}')
        return '\n'.join(lib_str)


class Flop:
    """A single flip-flop internal to a standard cell"""
    def __init__(self, in_name, out_name, next_state, clock):
        self.in_name = in_name
        self.out_name = out_name
        self.next_state = next_state
        self.clocked_on = clock
        self.clear = ''
        self.preset = ''
        self.clear_preset_var1 = 'L'

    def __str__(self) -> str:
        """Return str(self)"""
        ff_str = [
            f'ff ({self.in_name}, {self.out_name}) {{',
            f'  next_state : "{self.next_state}";',
            f'  clocked_on : "{self.clocked_on}";',
        ]
        if self.clear:
            ff_str.append(f'  clear : "{self.clear}";')
        if self.preset:
            ff_str.append(f'  preset : "{self.preset}";')
        if self.clear_preset_var1:
            ff_str.append(f'  clear_preset_var1 : {self.clear_preset_var1};')
        ff_str.append('}')
        return '\n'.join(ff_str)


class Pin:
    """A single pin from a standard cell"""
    def __init__(self, name: str, direction: str|None=None, role: str='io') -> None:
        """Create a new Pin.

        :param name: pin name
        :param direction: (optional) pin direction
        :param role: (optional) pin role
        """
        self.capacitance = 0
        self.drive_current = 0
        self.rise_capacitance = 0
        self.fall_capacitance = 0
        self.max_capacitance = 0
        self.function = ''
        self.three_state = ''
        self.internal_power = []
        self.min_pulse_width_high = 0
        self.min_pulse_width_low = 0
        self.timings = []

        self._name = name.upper()
        if direction in ['input', 'output', None]:
            self._direction = direction
        else:
            raise ValueError('Pin direction must be one of ["input", "output", None]')
        if role in ['set', 'reset', 'clock', 'io', 'pad']:
            self._role = role
        else:
            raise ValueError('Pin role must be one of ["set", "reset", "clock", "io", "pad"]')

    @property
    def name(self) -> str:
        """Return pin name."""
        return self._name

    @property
    def direction(self) -> str:
        """Return pin direction."""
        return self._direction

    @property
    def role(self) -> str:
        """Return pin role. May be 'set', 'reset', 'clock', or 'io'."""
        return self._role

    def is_clk(self) -> bool:
        """Return `True` if the pin's role is `'clock'`"""
        return self.role == 'clock'

    def is_set(self) -> bool:
        """Return `True` if the pin's role is `'set'`"""
        return self.role == 'set'

    def is_reset(self) -> bool:
        """Return `True` if the pin's role is `'reset'`"""
        return self.role == 'reset'

    def is_io(self) -> bool:
        """Return `True` if the pin's role is `'io'`"""
        return self.role == 'io'

    def is_pad(self) -> bool:
        """Return `True` if the pin's role is `'pad'`"""
        return self.role == 'pad'

    def __eq__(self, other) -> bool:
        """Return `True` if name, role, and direction match.
        
        :param other: A pin to compare against self"""
        return self.name == other.name \
            and self.role == other.role \
                and self.direction == other.direction

    def __str__(self) -> str:
        """Return str(self)"""
        # Pin properties
        lib_str = [f'pin ({self.name}) {{']
        if self.is_pad():
            lib_str.append('  is_pad : true;')
        lib_str.append(f'  direction : {self.direction};')
        if self.is_pad() and self.drive_current:
            lib_str.append(f'  drive_current : {self.drive_current:7f};')
        lib_str.extend([
            f'  capacitance : {self.capacitance:7f};',
            f'  rise_capacitance : {self.rise_capacitance:7f};',
            f'  fall_capacitance : {self.fall_capacitance:7f};',
        ])
        if self.is_clk():
            lib_str.append('  clock : true;')
        if self.max_capacitance:
            lib_str.append(f'  max_capacitance : {self.max_capacitance:7f};')
        if self.function:
            lib_str.append(f'  function : "{self.function}";')
        if self.three_state:
            lib_str.append(f'  three_state : "{self.three_state}";')
        # Internal power
        for data in self.internal_power:
            for line in str(data).split('\n'):
                lib_str.append(f'  {line}')
        # min_pulse_width
        if self.role in ['clock', 'set', 'reset']:
            if self.min_pulse_width_high:
                lib_str.append(f'  min_pulse_width_high : {self.min_pulse_width_high};')
            if self.min_pulse_width_low:
                lib_str.append(f'  min_pulse_width_low : {self.min_pulse_width_low};')
        # Timing
        for data in self.timings:
            for line in str(data).split('\n'):
                lib_str.append(f'  {line}')
        lib_str.append('}')
        return '\n'.join(lib_str)

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f'Pin(name="{self.name}", direction="{self.direction}", role="{self.role}")'

    def plot_delay(self, settings, cell_name):
        """Plot propagation and transient delays for rise and fall cases

        Generate two plots: one for rise timing and one for fall timing. Both plots
        should display propagation and transient delay as a function of slew rate and
        capacitive load."""
        # Input pins may not have delay data to plot. Prevent plotting in these cases
        if self.direction == 'output':
            figs = []
            # Output pins have cell_{rise,fall} and {rise,fall}_transition
            for timing_data in self.timings:
                for direction in ['rise', 'fall']:
                    fig = plt.figure(
                        label=f'{cell_name} | {self.name} ({direction}) Timing | Related Pin: {timing_data.related_pin}'
                    )

                    prop_table = timing_data[f'cell_{direction}']
                    tran_table = timing_data[f'{direction}_transition']

                    ax, indices = prop_table.generate_axes(fig)
                    prop_surface = ax.plot_surface(*indices, np.asarray(prop_table.data()), edgecolor='red', cmap='inferno', alpha=0.3, label='Propagation Delay')
                    prop_surface._edgecolors2d = prop_surface._edgecolor3d # Workaround for legend. See https://stackoverflow.com/questions/54994600/pyplot-legend-poly3dcollection-object-has-no-attribute-edgecolors2d
                    prop_surface._facecolors2d = prop_surface._facecolor3d # Workaround for legend
                    tran_surface = ax.plot_surface(*indices, np.asarray(tran_table.data()), edgecolor='blue', cmap='viridis', alpha=0.3, label='Transient Delay')
                    tran_surface._edgecolors2d = tran_surface._edgecolor3d # Workaround for legend.
                    tran_surface._facecolors2d = tran_surface._facecolor3d # Workaround for legend
                    time_unit = str(settings.units.time.prefixed_unit)
                    cap_unit = str(settings.units.capacitance.prefixed_unit)
                    ax.set(
                        xlabel=f'Slew Rate [{time_unit}]',
                        ylabel=f'Fanout [{cap_unit}]',
                        zlabel=f'Delay [{time_unit}]',
                        title='Transient and Propagation Delays'
                    )
                    ax.legend()

                    figs.append(fig)
            return figs

    def plot_energy(self, settings):
        """Plot energy for rise and fall cases"""
        pass # TODO

    def templates(self) -> list:
        """Generate all lookup table templates required for this pin"""
        templates = []
        [templates.extend(timing.templates()) for timing in self.timings]
        [templates.extend(power.templates()) for power in self.internal_power]
        return list(set(templates))


class InternalPowerData:
    """Container for pin power tables"""
    def __init__(self, related_pin: str='') -> None:
        """Create a new InternalPowerData.

        Initialize a new blank InternalPowerData. fall_power and rise_power must be
        initialized using their corresponding set functions, set_fall_power_table and
        set_rise_power_table.

        :param related_pin: (optional) the related pin for the power data (if relevant)"""
        self._related_pin = related_pin
        self._rise_power = None
        self._fall_power = None

    @property
    def related_pin(self) -> str:
        """Return related pin name."""
        return self._related_pin

    @property
    def rise_power(self):
        """Return rise_power table."""
        return self._rise_power

    def set_rise_power_table(self, template: str, values: list, index_1: list, index_2: list):
        """Add rise_power table data"""
        self._rise_power = Table('rise_power', template, values, index_1, index_2)

    @property
    def fall_power(self):
        """Return fall_power table."""
        return self._fall_power

    def set_fall_power_table(self, template: str, values: list, index_1: list, index_2: list):
        """Set fall_power table data"""
        self._fall_power = Table('fall_power', template, values, index_1, index_2)

    def templates(self) -> list:
        return [table.template_str() for table in [self._rise_power, self._fall_power]]

    def __str__(self) -> str:
        """Return str(self)"""
        internal_power_str = ['internal_power () {']
        if self.related_pin:
            internal_power_str.append(f'  related_pin : "{self.related_pin}";')
        for line in str(self.rise_power).split('\n'):
            internal_power_str.append(f'  {line}')
        for line in str(self.fall_power).split('\n'):
            internal_power_str.append(f'  {line}')
        internal_power_str.append('}')
        return '\n'.join(internal_power_str)


class TimingData:
    """Container for pin timing data and tables"""
    def __init__(self, related_pin, timing_type='', **attrs) -> None:
        """Create a new TimingData"""
        self._related_pin = related_pin
        self._timing_type = timing_type
        self._attrs = attrs
        self._tables = {}

    @property
    def related_pin(self) -> str:
        """Return related pin name."""
        return self._related_pin

    @property
    def timing_type(self) -> str:
        """Return timing type"""
        return self._timing_type

    def add_table(self, name, template, values, index_1, index_2=None) -> None:
        """Add a new table to the timing data

        :param name: the table's name as it will appear in liberty syntax
        :param template: the table template to use
        :param values: a list of table values
        :param index_1: a list of table indexes for dimension 1
        :param index_2: (optional) a list of table indexes for dimension 2"""
        self._tables[name] = Table(name, template, values, index_1, index_2)

    @property
    def attributes(self) -> dict:
        """Get attributes on this timing data group"""
        return self._attrs

    def add_attribute(self, key, value):
        """Add a new attribute to this TimingData"""
        self._attrs[key] = value

    def templates(self) -> list:
        """Get table templates for this TimingData"""
        return [table.template_str() for table in self._tables.values()]

    def __getitem__(self, key):
        """Return self[key]. Searches tables by name."""
        return self._tables[key]

    def __str__(self) -> str:
        """Return str(self)."""
        timing_str = [
            'timing () {',
            f'  related_pin : "{self.related_pin}";',
        ]
        if self.timing_type:
            timing_str.append(f'  timing_type : {self.timing_type};')
        for key, value in self.attributes:
            timing_str.append(f'  {key} : {value};')
        for table in self._tables.values():
            for line in str(table).split('\n'):
                timing_str.append(f'  {line}')
        timing_str.append('}')
        return '\n'.join(timing_str)


@dataclass
class TableTemplate:
    """Template data for a Table"""
    name = 'delay_template'
    variables = ['input_net_transition']

    def __str__(self) -> str:
        """Return str(self)"""
        return self.name


class Table:
    """A Table contains tabular data as would be displayed in a liberty file."""
    def __init__(self, name: str, template: TableTemplate, values: list, index_1: list, index_2: list|None=None) -> None:
        """Create a new Table

        :param name: table name
        :param template: table template
        :param values: a list of values in the table
        :param index_1: indices used to lookup table values in dimension 1
        :param index_2: indices used to lookup table values in dimension 2 (if present)
        """
        self._name = name
        self._template = template
        self._index_1 = index_1
        self._index_2 = index_2

        if not len(values) == (len(index_1) if not self.is_2d() else len(index_1) * len(index_2)):
            raise ValueError('Incorrect number of values for supplied index_1/index_2')
        self._values = values

    @property
    def name(self) -> str:
        """Return table name"""
        return self._name

    @property
    def template(self) -> str:
        """Return table template data"""
        return self._template

    @property
    def values(self) -> list:
        """Return a list of values in the table"""
        return self._values

    @property
    def index_1(self) -> list:
        """Return indices used to lookup values in dimension 1"""
        return self._index_1

    @property
    def index_2(self) -> list:
        """Return indices used to lookup values in dimension 2"""
        return self._index_2

    def is_2d(self) -> bool:
        """Return `True` if the table has more than 1 row"""
        return bool(self.index_2)

    @property
    def shape(self):
        """Return the table shape (not including indices)."""
        return len(self.index_1) if not self.is_2d() else (len(self.index_1), len(self.index_2))

    def __str__(self) -> str:
        """Return str(self)"""
        table_str = [
            f'{self.name} ({self.template}) {{',
            f'  index_1 ("{", ".join(self.index_1)}");'
        ]
        if self.index_2:
            table_str.append(f'  index_2 ("{", ".join(self.index_2)}");')
        values = self.data().tolist()
        if self.is_2d():
            table_str.append('  values ( \\')
            rows = ', \\\n'.join([f'"{", ".join(group)}"' for group in values]).split('\n')
            for row in rows:
                table_str.append(f'    {row}')
            table_str[-1] += ');'
        else:
            table_str.append(f'  values ("{", ".join(values)}");')
        table_str.append('}')
        return '\n'.join(table_str)

    def data(self):
        """Return the table values reshaped according to the index lengths"""
        return np.reshape(self.values, self.shape)

    def generate_axes(self, figure):
        """Generate a set of axes appropriate for displaying this table's data"""
        to_float = lambda idx: [float(i) for i in idx]
        if self.is_2d():
            x_index = np.repeat(np.expand_dims(to_float(self.index_1), 1), len(self.index_2), 1)
            y_index = np.swapaxes(np.repeat(np.expand_dims(to_float(self.index_2), 1), len(self.index_1), 1), 0, 1)
            indices = [x_index, y_index]
            ax = figure.add_subplot(projection='3d')
            ax.set_proj_type('ortho')
        else:
            indices = to_float(self.index_1)
            ax = figure.add_subplot()

        return ax, indices

    def template_str(self):
        """Generate the template for this table"""
        template_str = [
            f'lu_table_template ({self.template.name}) {{',
            f'  variable_1 : {self.template.variables[0]};',
        ]
        if self.index_2:
            template_str.append(f'  variable_2 : {self.template.variables[1]};')
        template_str.append(f'  index_1 ("{", ".join(self.index_1)}");')
        if self.index_2:
            template_str.append(f'  index_2 ("{", ".join(self.index_2)}");')
        template_str.append('}')
        return '\n'.join(template_str)
        
