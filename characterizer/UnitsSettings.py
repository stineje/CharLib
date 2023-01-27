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
        self.voltage = EngineeringUnit('V')
        self.capacitance = EngineeringUnit('F', 1e-12)
        self.resistance = EngineeringUnit('Ohm')
        self.current = EngineeringUnit('A', 1e-6)
        self.time = EngineeringUnit('s', 1e-9)
        self.leakage_power = EngineeringUnit('W', 1e-9)
        self.energy = EngineeringUnit('J', 1e-12)