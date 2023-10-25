"""Models liberty library groups"""

from liberty.UnitsSettings import UnitsSettings

# TODO: wire loads, operating conditions, power supplies

class Library:
    """Models a library, which groups cells and their common properties"""

    def __init__(self, name, **attrs):
        """Create a new Library"""
        self.name = name
        self._attrs = attrs
        self.cells = {}

        # General attributes
        self.filename = attrs.get('filename', f'{name}.lib')
        self.technology = 'cmos'
        self.delay_model = 'table_lookup'
        self.bus_naming_style = attrs.get('bus_naming_style', '%s-%d')

        # Delay and Slew attributes
        self.input_threshold_pct_rise = attrs.get('input_threshold_pct_rise', 50)
        self.input_threshold_pct_fall = attrs.get('input_threshold_pct_fall', 50)
        self.output_threshold_pct_rise = attrs.get('output_threshold_pct_rise', 50)
        self.output_threshold_pct_fall = attrs.get('output_threshold_pct_fall', 50)
        self.slew_upper_threshold_pct_rise = attrs.get('slew_upper_threshold_pct_rise', 80)
        self.slew_lower_threshold_pct_rise = attrs.get('slew_lower_threshold_pct_rise', 20)
        self.slew_upper_threshold_pct_fall = attrs.get('slew_upper_threshold_pct_fall', 80)
        self.slew_lower_threshold_pct_fall = attrs.get('slew_lower_threshold_pct_fall', 20)

        # Units
        units = attrs.get('units', {})
        unit_keys = [
            'time',
            'voltage',
            'current',
            'pulling_resistance',
            'capacitive_load',
            'leakage_power',
            'energy',
        ]
        for unit_key in unit_keys:
            if f'{unit_key}_unit' in attrs:
                units[unit_key] = attrs[f'{unit_key}_unit']
        self.units = UnitsSettings(**units)

    @property
    def time_unit(self):
        """Return self.units.time"""
        return self.units.time

    @property
    def voltage_unit(self):
        """Returns self.units.voltage"""
        return self.units.voltage

    @property
    def current_unit(self):
        """Returns self.units.current"""
        return self.units.current

    @property
    def pulling_resistance_unit(self):
        """Returns self.units.resistance"""
        return self.units.resistance

    @property
    def capacitive_load_unit(self):
        """Returns self.units.capacitance"""
        return self.units.capacitance

    @property
    def leakage_power_unit(self):
        """Returns self.units.power"""
        return self.units.power

    def __getitem__(self, key: str):
        """Returns self[key]. Searches cells by name."""
        return self.cells[key]

    @property
    def attributes(self) -> dict:
        """Return extra attributes on this library"""

    def add_attribute(self, key: str, value: str):
        """Add a new liberty attribute to this cell"""
        self._attrs[key] = str(value)

    def __str__(self) -> str:
        """Return str(self)"""
        lib_str = [
            f'library ({self.name}) {{',
            f'  technology : ({self.technology});',
            f'  delay_model : {self.delay_model};',
            f'  bus_naming_style : "{self.bus_naming_style}";',
            f'  slew_upper_threshold_pct_rise : {self.slew_upper_threshold_pct_rise};',
            f'  slew_lower_threshold_pct_rise : {self.slew_lower_threshold_pct_rise};',
            f'  slew_upper_threshold_pct_fall : {self.slew_upper_threshold_pct_fall};',
            f'  slew_lower_threshold_pct_fall : {self.slew_lower_threshold_pct_fall};',
            f'  input_threshold_pct_rise : {self.input_threshold_pct_rise};',
            f'  input_threshold_pct_fall : {self.input_threshold_pct_fall};',
            f'  output_threshold_pct_rise : {self.output_threshold_pct_rise};',
            f'  output_threshold_pct_fall : {self.output_threshold_pct_fall};',
        ]
