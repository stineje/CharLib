"""Models liberty library groups"""

from charlib.liberty.UnitsSettings import UnitsSettings

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

        # Nominal operating conditions
        self.nom_process = attrs.get('nom_process', 1)
        self.nom_voltage = attrs.get('nom_voltage', 3.3)
        self.nom_temperature = attrs.get('nom_temperature', 25)

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

    def add_cell(self, cell) -> None:
        """Add a cell to the library"""
        self.cells[cell.name] = cell

    def templates(self) -> list:
        templates = []
        for cell in self.cells.values():
            templates.extend(cell.templates())
        return list(set(templates))

    def __str__(self) -> str:
        """Return str(self)"""
        spice_unit = lambda unit : unit.prefixed_unit.str_spice()
        lib_str = [
            f'library ({self.name}) {{',
            f'  technology : {self.technology};',
            f'  delay_model : {self.delay_model};',
            f'  bus_naming_style : "{self.bus_naming_style}";',
            '\n  /* Units */',
            f'  time_unit : "1{spice_unit(self.units.time)}";',
            f'  voltage_unit : "1{spice_unit(self.units.voltage)}";',
            f'  current_unit : "1{spice_unit(self.units.current)}";',
            f'  pulling_resistance_unit : "1{spice_unit(self.units.resistance)}";',
            f'  leakage_power_unit : "1{spice_unit(self.units.power)}";',
            f'  capacitive_load_unit : "1{spice_unit(self.units.capacitance)}";',
            '\n  /* Slew characteristics */',
            f'  slew_upper_threshold_pct_rise : {self.slew_upper_threshold_pct_rise};',
            f'  slew_lower_threshold_pct_rise : {self.slew_lower_threshold_pct_rise};',
            f'  slew_upper_threshold_pct_fall : {self.slew_upper_threshold_pct_fall};',
            f'  slew_lower_threshold_pct_fall : {self.slew_lower_threshold_pct_fall};',
            f'  input_threshold_pct_rise : {self.input_threshold_pct_rise};',
            f'  input_threshold_pct_fall : {self.input_threshold_pct_fall};',
            f'  output_threshold_pct_rise : {self.output_threshold_pct_rise};',
            f'  output_threshold_pct_fall : {self.output_threshold_pct_fall};',
            '\n  /* Operating Conditions */',
            f'  nom_process : {self.nom_process};',
            f'  nom_voltage : {self.nom_voltage};',
            f'  nom_temperature : {self.nom_temperature};',
        ]
        # TODO: Display wire loads, operating conditions, and power supplies

        # Display templates from cells
        lib_str.append('\n  /* Table Templates */')
        for template in self.templates():
            for line in template.split('\n'):
                lib_str.append(f'  {line}')

        # Display cells
        for name, cell in self.cells.items():
            lib_str.append(f'\n  /* {name} */')
            for line in str(cell).split('\n'):
                lib_str.append(f'  {line}')
        
        lib_str.append('}')
        return '\n'.join(lib_str)
