from PySpice import Unit

class UnitsSettings:
    def __init__(self, **kwargs) -> None:
        # Initialize using setters
        self.time = kwargs.get('time', 'ns')
        self.voltage = kwargs.get('voltage', 'V')
        self.current = kwargs.get('current', 'uA')
        self.resistance = kwargs.get('pulling_resistance', 'Ω')
        self.capacitance = kwargs.get('capacitive_load', 'pF')
        self.power = kwargs.get('leakage_power', 'nW')
        self.energy = kwargs.get('energy', 'fJ')
        # TODO: Add temperature

    def __str__(self) -> str:
        lines = []
        lines.append(f'Voltage unit:     {str(self.voltage)}')
        lines.append(f'Current unit:     {str(self.current)}')
        lines.append(f'Resistance unit:  {str(self.resistance)}')
        lines.append(f'Capacitance unit: {str(self.capacitance)}')
        lines.append(f'Time unit:        {str(self.time)}')
        lines.append(f'Energy unit:      {str(self.energy)}')
        lines.append(f'Power unit:       {str(self.power)}')
        return '\n'.join(lines)

    @property
    def voltage(self):
        return self._voltage

    @voltage.setter
    def voltage(self, value):
        # Valid symbols are "V" or "Volts"
        if value.lower().endswith('v'):
            prefix_str = value.removesuffix(value[-1])
        elif value.lower().endswith('volts'):
            prefix_str = value.removesuffix(value[-5:])
        else:
            raise ValueError(f'Invalid voltage unit: {value}')
        self._voltage = self._parse_unit(prefix_str, Unit.u_V)

    @property
    def capacitance(self):
        return self._capacitance

    @capacitance.setter
    def capacitance(self, value: str):
        # Valid symbols are "F" or "Farads"
        if value.lower().endswith('f'):
            prefix_str = value.removesuffix(value[-1])
        elif value.lower().endswith('farads'):
            prefix_str = value.removesuffix(value[-6:])
        else:
            raise ValueError(f'Invalid capacitance unit: {value}')
        self._capacitance = self._parse_unit(prefix_str, Unit.u_F)

    @property
    def resistance(self):
        return self._resistance

    @resistance.setter
    def resistance(self, value: str):
        # Valid symbols are "Ω" or "Ohms"
        if value.endswith('Ω'):
            prefix_str = value.removesuffix('Ω')
        elif value.lower().endswith('ohm'):
            prefix_str = value.removesuffix(value[-3:])
        elif value.lower().endswith('ohms'):
            prefix_str = value.removesuffix(value[-4:])
        else:
            raise ValueError(f'Invalid resistance unit: {value}')
        self._resistance = self._parse_unit(prefix_str, Unit.u_Ω)

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value: str):
        # Valid symbols are "A" or "Amps"
        if value.lower().endswith('a'):
            prefix_str = value.removesuffix(value[-1])
        elif value.lower().endswith('amp'):
            prefix_str = value.removesuffix(value[-3:])
        elif value.lower().endswith('amps'):
            prefix_str = value.removesuffix(value[-4:])
        else:
            raise ValueError(f'Invalid current unit: {value}')
        self._current = self._parse_unit(prefix_str, Unit.u_A)

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value: str):
        # Valid symbols are "s" or "seconds"
        if value.lower().endswith('seconds'):
            prefix_str = value.removesuffix(value[-7:])
        elif value.lower().endswith('s'):
            prefix_str = value.removesuffix(value[-1])
        else:
            raise ValueError(f'Invalid time unit: {value}')
        self._time = self._parse_unit(prefix_str, Unit.u_s)

    @property
    def power(self):
        return self._power

    @power.setter
    def power(self, value: str):
        # Valid symbols are "W" or "Watts"
        if value.lower().endswith('w'):
            prefix_str = value.removesuffix(value[-1])
        elif value.lower().endswith('watts'):
            prefix_str = value.removesuffix(value[-5:])
        else:
            raise ValueError(f'Invalid leakage power unit: {value}')
        self._power = self._parse_unit(prefix_str, Unit.u_W)

    @property
    def energy(self):
        return self._energy
    
    @energy.setter
    def energy(self, value: str):
        # Valid symbols are "J" or "Joules"
        if value.lower().endswith('j'):
            prefix_str = value.removesuffix(value[-1])
        elif value.lower().endswith('joules'):
            prefix_str = value.removesuffix(value[-6:])
        else:
            raise ValueError(f'Invalid energy unit: {value}')
        self._energy = self._parse_unit(prefix_str, Unit.u_J)

    def _parse_unit(self, prefix_str, unit: callable):
        """Convert a metric prefix to its associated exponent"""
        lookup_table = [
            # Prefix             callable
            (('yocto', 'y'),     -24),
            (('zepto', 'z'),     -21),
            (('atto', 'a'),      -18),
            (('femto', 'f'),     -15),
            (('pico', 'p'),      -12),
            (('nano', 'n'),       -9),
            (('micro', 'u', 'μ'), -6),
            (('milli', 'm'),      -3),
            ((''),                 0),
            (('kilo', 'k'),        3),
            (('mega', 'M'),        6),
            (('giga', 'G'),        9),
            (('tera', 'T'),       12),
            (('peta', 'P'),       15),
            (('exa', 'E'),        18),
            (('zetta', 'Z'),      21),
            (('yotta', 'Y'),      24)
        ]
        prefix_str = prefix_str.lower() if len(prefix_str) > 1 else prefix_str # Allow case-insensitive long prefixes
        for (prefixes, exponent) in lookup_table:
            if prefix_str in prefixes: return unit(10.0**exponent).canonise()
        raise ValueError(f'"{prefix_str}" is not a recognized metric prefix! Supported values are: {[prefixes for (prefixes,_) in lookup_table]}')
