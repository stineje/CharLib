class EngineeringUnit:
    def __init__(self, symbol, magnitude = 1) -> None:
        self.symbol = symbol
        self.magnitude = magnitude

    # TODO: Use a dict or similar structure to map prefixes to magnitudes instead of these awful if/else blocks

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, value: str) -> None:
        if value is not None and len(value) > 0:
            self._symbol = value

    def get_metric_prefix(self) -> str:
        """Converts magnitude into a metric prefix"""
        if self.magnitude == 1e30:
            return 'Q'
        elif self.magnitude == 1e27:
            return 'R'
        elif self.magnitude == 1e24:
            return 'Y'
        elif self.magnitude == 1e21:
            return 'Z'
        elif self.magnitude == 1e18:
            return 'E'
        elif self.magnitude == 1e15:
            return 'P'
        elif self.magnitude == 1e12:
            return 'T'
        elif self.magnitude == 1e9:
            return 'G'
        elif self.magnitude == 1e6:
            return 'M'
        elif self.magnitude == 1e3:
            return 'k'
        elif self.magnitude == 1e-3:
            return 'm'
        elif self.magnitude == 1e-6:
            return 'u'
        elif self.magnitude == 1e-9:
            return 'n'
        elif self.magnitude == 1e-12:
            return 'p'
        elif self.magnitude == 1e-15:
            return 'f'
        elif self.magnitude == 1e-18:
            return 'a'
        elif self.magnitude == 1e-21:
            return 'z'
        elif self.magnitude == 1e-24:
            return 'y'
        elif self.magnitude == 1e-27:
            return 'r'
        elif self.magnitude == 1e-30:
            return 'q'
        else:
            return None

    @property
    def magnitude(self):
        return self._magnitude

    @magnitude.setter
    def magnitude(self, value) -> None:
        if value is not None:
            if isinstance(value, float) or value == 1:
                # TODO: Add checks to make sure value is a multiple of 10^3n
                self._magnitude = value
            elif isinstance(value, str):
                if value == 'Q':
                    self.magnitude = 1e30
                elif value == 'R':
                    self.magnitude = 1e27
                elif value == 'Y':
                    self.magnitude = 1e24
                elif value == 'Z':
                    self.magnitude = 1e21
                elif value == 'E':
                    self.magnitude = 1e18
                elif value == 'P':
                    self.magnitude = 1e15
                elif value == 'T':
                    self.magnitude = 1e12
                elif value == 'G':
                    self.magnitude = 1e9
                elif value == 'M':
                    self.magnitude = 1e6
                elif value == 'k':
                    self.magnitude = 1e3
                elif value == 'm':
                    self.magnitude = 1e-3
                elif value == 'u':
                    self.magnitude = 1e-6
                elif value == 'n':
                    self.magnitude = 1e-9
                elif value == 'p':
                    self.magnitude = 1e-12
                elif value == 'f':
                    self.magnitude = 1e-15
                elif value == 'a':
                    self.magnitude = 1e-18
                elif value == 'z':
                    self.magnitude = 1e-21
                elif value == 'y':
                    self.magnitude = 1e-24
                elif value == 'r':
                    self.magnitude = 1e-27
                elif value == 'q':
                    self.magnitude = 1e-30
                else:
                    raise ValueError("EngineeringUnit.magnitude accepts only SI units which correspond to values of 10^3N. See https://www.nist.gov/pml/owm/metric-si-prefixes")
            else:
                raise TypeError("EngineeringUnit.magnitude must be assigned as a float mulitple of 10 (such as 1e3) or as an SI prefix")
        else:
            raise TypeError("EngineeringUnit.magnitude must be assigned as an integer or SI prefix")
                

    def __str__(self) -> str:
        # Turn magnitude into a metric prefix
        mag_repr = self.get_metric_prefix()
        if mag_repr is not None:
            return f'{mag_repr}{self.symbol}'
        elif self.magnitude == 1:
            return self.symbol
        else: # Handle the case where magnitude is not 1e3N
            return f'{self.symbol} x {self.magnitude}'

    def __repr__(self) -> str:
        return f'EngineeringUnit({self.symbol}, {self.magnitude})'


class UnitsSettings:
    def __init__(self, **kwargs) -> None:
        # Initialize using setters
        self.voltage = kwargs.get('voltage', 'V')
        self.capacitance = kwargs.get('capacitance', 'pF')
        self.resistance = kwargs.get('resistance', 'Ω')
        self.current = kwargs.get('current', 'uA')
        self.time = kwargs.get('time', 'ns')
        self.power = kwargs.get('power', 'nW')
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
        if isinstance(value, str):
            if value.lower().endswith('v'):
                if value.lower() == 'v': # Case A: no SI prefix
                    self._voltage = EngineeringUnit('V')
                else: # Case B: SI prefix present
                    self._voltage = EngineeringUnit(value[-1], value[:-1])
            elif value.lower().endswith('volts'):
                if value.lower() == 'volts': # Case A: no SI prefix
                    self._voltage = EngineeringUnit(value)
                else: # Case B: SI prefix present
                    self._voltage = EngineeringUnit(value[-5:], value[:-5])
            else:
                raise ValueError(f'Invalid voltage unit: {value}')
        elif isinstance(value, EngineeringUnit):
            if value.symbol.lower() in ['v', 'volts']:
                self._voltage = value

    @property
    def capacitance(self):
        return self._capacitance

    @capacitance.setter
    def capacitance(self, value):
        # Valid symbols are "F" or "Farads"
        if isinstance(value, str):
            if value.lower().endswith('f'):
                if value.lower() == 'f':
                    self._capacitance = EngineeringUnit('F')
                else:
                    self._capacitance = EngineeringUnit(value[-1], value[:-1])
            elif value.lower().endswith('farads'):
                if value.lower() == 'farads':
                    self._capacitance = EngineeringUnit(value)
                else:
                    self.capacitance = EngineeringUnit(value[-6:], value[:-6])
            else:
                raise ValueError(f'Invalid capacitance unit: {value}')
        elif isinstance(value, EngineeringUnit):
            if value.symbol.lower() in ['f', 'farads']:
                self._capacitance = value
    
    @property
    def resistance(self):
        return self._resistance

    @resistance.setter
    def resistance(self, value):
        # Valid symbols are "Ω" or "Ohms"
        if isinstance(value, str):
            if value.endswith('Ω'):
                if value == 'Ω':
                    self._resistance = EngineeringUnit('Ω')
                else:
                    self._resistance = EngineeringUnit(value[-1], value[:-1])
            elif value.lower().endswith('ohms') or value.lower().endswith('ohm'):
                if value.lower() == 'ohms' or value.lower() == 'ohm':
                    self._resistance = EngineeringUnit(value)
                else:
                    self._resistance = EngineeringUnit(value[-3:], value[:-3])
            else:
                raise ValueError(f'Invalid resistance unit: {value}')
        elif isinstance(value, EngineeringUnit):
            if value.symbol == 'Ω' or value.symbol.lower() in ['ohm', 'ohms']:
                self._resistance = value
    
    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        # Valid symbols are "A" or "Amps"
        if isinstance(value, str):
            if value.lower().endswith('a'):
                if value.lower() == 'a':
                    self._current = EngineeringUnit('A')
                else:
                    self._current = EngineeringUnit(value[-1], value[:-1])
            elif value.lower().endswith('amps'):
                if value.lower() == 'amps':
                    self._current = EngineeringUnit(value)
                else:
                    self._current = EngineeringUnit(value[-4:], value[:-4])
            else:
                raise ValueError(f'Invalid current unit: {value}')
        elif isinstance(value, EngineeringUnit):
            if value.symbol.lower() in ['a', 'amps']:
                self._current = value
    
    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        # Valid symbols are "s" or "seconds"
        if isinstance(value, str):
            if value.lower().endswith('seconds'):
                if value.lower() == 'seconds':
                    self._time = EngineeringUnit(value)
                else:
                    self._time = EngineeringUnit(value[-7], value[:-7])
            elif value.lower().endswith('s'):
                if value.lower() == 's':
                    self._time = EngineeringUnit(value)
                else:
                    self._time = EngineeringUnit(value[-1], value[:-1])
            else:
                raise ValueError(f'Invalid time unit: {value}')
        elif isinstance(value, EngineeringUnit):
            if value.symbol.lower() in ['s', 'seconds']:
                self._time = value
    
    @property
    def power(self):
        return self._power
    
    @power.setter
    def power(self, value):
        # Valid symbols are "W" or "Watts"
        if isinstance(value, str):
            if value.lower().endswith('w'):
                if value.lower() == 'w':
                    self._power = EngineeringUnit(value)
                else:
                    self._power = EngineeringUnit(value[-1], value[:-1])
            elif value.lower().endswith('watts'):
                if value.lower() == 'watts':
                    self._power = EngineeringUnit(value)
                else:
                    self._power = EngineeringUnit(value[-5:], value[:-5])
            else:
                raise ValueError(f'Invalid leakage power unit: {value}')
        elif isinstance(value, EngineeringUnit):
            if value.symbol.lower() in ['w', 'watts']:
                self._power = value
    
    @property
    def energy(self):
        return self._energy
    
    @energy.setter
    def energy(self, value):
        # Valid symbols are "J" or "Joules"
        if isinstance(value, str):
            if value.lower().endswith('j'):
                if value.lower() == 'j':
                    self._energy = EngineeringUnit(value)
                else:
                    self._energy = EngineeringUnit(value[-1], value[:-1])
            elif value.lower().endswith('joules'):
                if value.lower() == 'joules':
                    self._energy = EngineeringUnit(value)
                else:
                    self._energy = EngineeringUnit(value[-6:], value[:-6])
            else:
                raise ValueError(f'Invalid energy unit: {value}')
        elif isinstance(value, EngineeringUnit):
            if value.symbol.lower() in ['j', 'joules']:
                self._energy = value