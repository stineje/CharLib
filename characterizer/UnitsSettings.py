class EngineeringUnit:
    def __init__(self, symbol, magnitude = 1) -> None:
        self.symbol = symbol
        self.magnitude = magnitude

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, value: str) -> None:
        if value is not None and len(value) > 0:
            self._symbol = value

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
                elif value == 'μ':
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
                

    def __repr__(self) -> str:
        # Turn magnitude into a metric prefix
        mag_repr = None
        if self.magnitude == 1e30:
            mag_repr = 'Q'
        elif self.magnitude == 1e27:
            mag_repr = 'R'
        elif self.magnitude == 1e24:
            mag_repr = 'Y'
        elif self.magnitude == 1e21:
            mag_repr = 'Z'
        elif self.magnitude == 1e18:
            mag_repr = 'E'
        elif self.magnitude == 1e15:
            mag_repr = 'P'
        elif self.magnitude == 1e12:
            mag_repr = 'T'
        elif self.magnitude == 1e9:
            mag_repr = 'G'
        elif self.magnitude == 1e6:
            mag_repr = 'M'
        elif self.magnitude == 1e3:
            mag_repr = 'k'
        elif self.magnitude == 1e-3:
            mag_repr = 'm'
        elif self.magnitude == 1e-6:
            mag_repr = 'μ'
        elif self.magnitude == 1e-9:
            mag_repr = 'n'
        elif self.magnitude == 1e-12:
            mag_repr = 'p'
        elif self.magnitude == 1e-15:
            mag_repr = 'f'
        elif self.magnitude == 1e-18:
            mag_repr = 'a'
        elif self.magnitude == 1e-21:
            mag_repr = 'z'
        elif self.magnitude == 1e-24:
            mag_repr = 'y'
        elif self.magnitude == 1e-27:
            mag_repr = 'r'
        elif self.magnitude == 1e-30:
            mag_repr = 'q'

        if mag_repr is not None:
            return f'{mag_repr}{self.symbol}'
        elif self.magnitude == 1:
            return self.symbol
        else: # Handle the case where magnitude is not 1e3N
            return f'{self.symbol} x {self.magnitude}'


class UnitsSettings:
    def __init__(self) -> None:
        self._voltage = EngineeringUnit('V')
        self._capacitance = EngineeringUnit('F', 1e-12)
        self._resistance = EngineeringUnit('Ω')
        self._current = EngineeringUnit('A', 1e-6)
        self._time = EngineeringUnit('s', 1e-9)
        self._leakage_power = EngineeringUnit('W', 1e-9)
        self._energy = EngineeringUnit('J', 1e-12)

    @property
    def voltage(self):
        return self._voltage

    @voltage.setter
    def voltage(self, value: str):
        # Valid symbols are "V" or "Volts"
        if value.lower().endswith('v'):
            if value.lower() == 'v': # Case A: no SI prefix
                self._voltage.symbol = 'V'
                self._voltage.magnitude = 1
            else: # Case B: SI prefix present
                self._voltage.symbol = value[-1]
                self._voltage.magnitude = value[:-1]
        elif value.lower().endswith('volts'):
            if value.lower() == 'volts': # Case A: no SI prefix
                self._voltage.symbol = value
                self._voltage.magnitude = 1
            else: # Case B: SI prefix present
                self._voltage.symbol = value[-5:]
                self._voltage.magnitude = value[:-5]
        else:
            raise ValueError(f'Invalid voltage unit: {value}')

    @property
    def capacitance(self):
        return self._capacitance

    @capacitance.setter
    def capacitance(self, value: str):
        # Valid symbols are "F" or "Farads"
        if value.lower().endswith('f'):
            if value.lower() == 'f':
                self._capacitance.symbol = 'F'
                self._capacitance.magnitude = 1
            else:
                self._capacitance.symbol = value[-1]
                self._capacitance.magnitude = value[:-1]
        elif value.lower().endswith('farads'):
            if value.lower() == 'farads':
                self._capacitance.symbol = value
                self._capacitance.magnitude = 1
            else:
                self._capacitance.symbol = value[-6:]
                self._capacitance.magnitude = value[:-6]
        else:
            raise ValueError(f'Invalid capacitance unit: {value}')
    
    @property
    def resistance(self):
        return self._resistance

    @resistance.setter
    def resistance(self, value: str):
        # Valid symbols are "Ω" or "Ohms"
        if value.endswith('Ω'):
            if value == 'Ω':
                self._resistance.symbol = 'Ω'
                self._resistance.magnitude = 1
            else:
                self._resistance.symbol = value[-1]
                self._resistance.magnitude = value[:-1]
        elif value.lower().endswith('ohms') or value.lower().endswith('ohm'):
            if value.lower() == 'ohms' or value.lower() == 'ohm':
                self._resistance.symbol = value
                self._resistance.magnitude = 1
            else:
                self._resistance.symbol = value[-4:]
                self._resistance.magnitude = value[:-4]
        else:
            raise ValueError(f'Invalid resistance unit: {value}')
    
    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value: str):
        # Valid symbols are "A" or "Amps"
        if value.lower().endswith('a'):
            if value.lower() == 'a':
                self._current.symbol = 'A'
                self._current.magnitude = 1
            else:
                self._current.symbol = value[-1]
                self._current.magnitude = value[:-1]
        elif value.lower().endswith('amps'):
            if value.lower() == 'amps':
                self._current.symbol = value
                self._current.magnitude = 1
            else:
                self._current.symbol = value[-4:]
                self._current.magnitude = value[:-4]
        else:
            raise ValueError(f'Invalid current unit: {value}')
    
    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value: str):
        # Valid symbols are "s" or "seconds"
        if value.lower().endswith('seconds'):
            if value.lower() == 'seconds':
                self._time.symbol = value
                self._time.magnitude = 1
            else:
                self._time.symbol = value[-7]
                self._time.magnitude = value[:-7]
        elif value.lower().endswith('s'):
            if value.lower() == 's':
                self._time.symbol = value
                self._time.magnitude = 1
            else:
                self._time.symbol = value[-1]
                self._time.magnitude = value[:-1]
        else:
            raise ValueError(f'Invalid time unit: {value}')
    
    @property
    def leakage_power(self):
        return self._leakage_power
    
    @leakage_power.setter
    def leakage_power(self, value: str):
        # Valid symbols are "W" or "Watts"
        if value.lower().endswith('w'):
            if value.lower() == 'w':
                self._leakage_power.symbol = 'W'
                self._leakage_power.magnitude = 1
            else:
                self._leakage_power.symbol = value[-1]
                self._leakage_power.magnitude = value[:-1]
        elif value.lower().endswith('watts'):
            if value.lower() == 'watts':
                self._leakage_power.symbol = value
                self._leakage_power.magnitude = 1
            else:
                self._leakage_power.symbol = value[-5:]
                self._leakage_power.magnitude = value[:-5]
        else:
            raise ValueError(f'Invalid leakage power unit: {value}')
    
    @property
    def energy(self):
        return self._energy
    
    @energy.setter
    def energy(self, value: str):
        # Valid symbols are "J" or "Joules"
        if value.lower().endswith('j'):
            if value.lower() == 'j':
                self._energy.symbol = 'J'
                self._energy.magnitude = 1
            else:
                self._energy.symbol = value[-1]
                self._energy.magnitude = value[:-1]
        elif value.lower().endswith('joules'):
            if value.lower() == 'joules':
                self._energy.symbol = value
                self._energy.magnitude = 1
            else:
                self._energy.symbol = value[-6:]
                self._energy.magnitude = value[:-6]
        else:
            raise ValueError(f'Invalid energy unit: {value}')