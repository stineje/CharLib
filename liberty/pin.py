"""This module contains tools for dealing with individual pins for a LogicCell"""

import numpy as np

class Pin:
    """A single pin from a standard cell"""
    def __init__(self, name: str, direction: str|None=None, role: str='io') -> None:
        """Create a new Pin.

        :param name: pin name
        :param direction: pin direction (must be 'input' or 'output' if specified)
        :param role: (optional) pin role (must be 'set', 'reset', 'clock', or 'io')
        """
        self.capacitance = 0
        self.rise_capacitance = 0
        self.fall_capacitance = 0
        self.max_capacitance = 0
        self.function = ''
        self._internal_power = {}
        self.min_pulse_width_high = 0
        self.min_pulse_width_low = 0
        self.timing = {}

        self._name = name
        if direction in ['input', 'output', None]:
            self._direction = direction
        else:
            raise ValueError('Pin direction must be one of ["input", "output", None]')
        if role in ['set', 'reset', 'clock', 'io']:
            self._role = role
        else:
            raise ValueError('Pin role must be one of ["set", "reset", "clock", "io"]')

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
        def __init__(self, related_pin) -> None:
            """Create a new TimingData"""
            self._related_pin = related_pin
            self.timing_type = ''
            self.timing_sense = ''
            self.when = ''
            self.sdf_cond = ''
            self._tables = {}

        @property
        def related_pin(self) -> str:
            """Return related pin name."""
            return self._related_pin

        def add_table(self, name, template, values, index_1, index_2=None) -> None:
            """Add a new table to the timing data

            :param name: the table's name as it will appear in liberty syntax
            :param template: the table template to use
            :param values: a list of table values
            :param index_1: a list of table indexes for dimension 1
            :param index_2: (optional) a list of table indexes for dimension 2"""
            self._tables[name] = Table(name, template, values, index_1, index_2)

        def __getitem__(self, key):
            """Return self[key]. Searches tables by name."""
            return self._tables[key]

        def __str__(self) -> str:
            """Return str(self)."""
            timing_str = [
                'timing () {',
                f'  related_pin = "{self.related_pin}";',
            ]
            if self.timing_type:
                timing_str.append(f'  timing_type : {self.timing_type};')
            if self.timing_sense:
                timing_str.append(f'  timing_sense : {self.timing_sense};')
            if self.when:
                timing_str.append(f'  when : "{self.when}";')
            if self.sdf_cond:
                timing_str.append(f'  sdf_cond : "{self.sdf_cond}";')
            for table in self._tables:
                for line in str(table).split('\n'):
                    timing_str.append(f'  {line}')
            timing_str.append('}')
            return '\n'.join(timing_str)

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

    def __eq__(self, other) -> bool:
        """Return `True` if name, role, and direction match.
        
        :param other: A pin to compare against self"""
        return self.name == other.name \
            and self.role == other.role \
                and self.direction == other.direction

    def __str__(self) -> str:
        """Return str(self)"""
        # Pin properties
        lib_str = [
            f'pin ({self.name}) {{',
            f'  direction : {self.direction};',
            f'  capacitance : {self.capacitance};',
            f'  rise_capacitance : {self.rise_capacitance};',
            f'  fall_capacitance : {self.fall_capacitance};',
        ]
        if self.is_clk():
            lib_str.append('  clock : true;')
        if self.max_capacitance:
            lib_str.append(f'  max_capacitance : {self.max_capacitance};')
        if self.function:
            lib_str.append(f'  function : "{self.function};"')
        # Internal power
        try:
            for data in self.internal_power.values():
                for line in str(data).split('\n'):
                    lib_str.append(f'  {line}')
        except AttributeError: # There's only one internal_power entry, not a dict
            for line in str(self.internal_power).split('\n'):
                lib_str.append(f'  {line}')
        # min_pulse_width
        if self.role in ['clock', 'set', 'reset']:
            if self.min_pulse_width_high:
                lib_str.append(f'  min_pulse_width_high : {self.min_pulse_width_high};')
            if self.min_pulse_width_low:
                lib_str.append(f'  min_pulse_width_low : {self.min_pulse_width_low};')
        # Timing
        for data in self.timing.values():
            for line in str(data).split('\n'):
                lib_str.append(f'  {line}')
        lib_str.append('}')
        return '\n'.join(lib_str)

    @property
    def internal_power(self) -> list|InternalPowerData:
        """Return internal_power entries"""
        return self._internal_power

    def add_internal_power(self, related_pin=None):
        """Add a new internal power entry

        Add an empty internal power entry to the Pin's list of internal power data. Internal power
        entries are indexed by related pin name. If there is no related pin name, instead set the
        internal power to a single InternalPowerData with no related pin.

        :param related_pin: (optional) related pin name for power information"""
        if not related_pin:
            if not self.internal_power:
                self._internal_power = Pin.InternalPowerData()
            else:
                raise ValueError('related_pin must be specified to add more than one internal_power entry to a pin')
        else:
            self._internal_power[related_pin] = Pin.InternalPowerData(related_pin)

    def add_timing(self, related_pin: str):
        """Add a new timing entry
        
        Add an empty timing entry to the Pin's list of timings. Timing entries are indexed by
        related pin name, e.g. `my_pin.timing['other_pin']`.
        
        :param related_pin: related pin name for the timing information"""
        self.timing[related_pin] = Pin.TimingData(related_pin)

class Table:
    """A Table contains tabular data as would be displayed in a liberty file."""
    def __init__(self, name: str, template: str, values: list, index_1: list, index_2: list|None=None) -> None:
        """Create a new Table

        :param name: table name
        :param template: table template name
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
        """Return table template name"""
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
    def shape(self) -> str:
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
        values = np.reshape(self.values, self.shape).tolist()
        print(values)
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
