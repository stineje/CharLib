class Harness:
    """Characterization parameters for one path through a cell
    
    A Harness defines characterization parameters from one input to one
    output of a standard cell circuit."""

    def __init__(self, target_cell, target_in_port: str, target_out_port: str, direction: str) -> None:
        self._target_in_port = target_in_port   # This pin will change while other inputs will be held stable
        self._stable_in_ports = []              # Pin names to hold stable
        self._target_out_port = target_out_port # This output will be measured for an expected result
        self._nontarget_out_ports = []          # Output pins we aren't checking

        # Set stable_in_ports
        for port in target_cell.in_ports:
            if not port == self.target_in_port:
                self._stable_in_ports.append(port)

        # Set nontarget_out_ports
        for port in target_cell.out_ports:
            if not port == self.target_out_port:
                self._nontarget_out_ports.append(port)

        # Documentation
        self.direction = direction              # Rising or falling

        @property
        def timing_type(self) -> str:
            return "combinational"

        @property
        def target_in_port(self) -> str:
            return self._target_in_port

        @property
        def stable_in_ports(self) -> list:
            return self._stable_in_ports

        @property
        def target_out_port(self) -> str:
            return self._target_out_port

        @property
        def nontarget_out_ports(self) -> list:
            return self._nontarget_out_ports

        @property
        def direction(self) -> str:
            return self._direction

        @direction.setter
        def direction(self, value: str):
            if value is not None:
                if isinstance(value, str):
                    if value == "rise":
                        self._direction = str(value)
                    elif value == "fall":
                        self._direction = str(value)
                    else:
                        raise ValueError(f'Harness direction must be "rise" or "fall", not {value}')
                else:
                    raise TypeError(f'Invalid type for harness direction: {type(value)}')
            else:
                raise ValueError(f'Invalid value for harness direction: {value}')

        @property
        def direction_prop(self) -> str:
            return f'cell_{self.direction}'

        @property
        def direction_tran(self) -> str:
            return f'{self.direction}_transition'

        @property
        def direction_power(self) -> str:
            return f'{self.direction}_power'


class CombinationalHarness (Harness):
    def __init__(self, target_cell, target_in_port: str, target_out_port: str, direction: str, timing_sense: str = None) -> None:
        super().__init__(target_cell, target_in_port, target_out_port, direction)
        self.timing_sense = timing_sense    # Describes the relationship b/t target input and target output

    @property
    def timing_sense(self) -> str:
        return self._timing_sense

    @timing_sense.setter
    def timing_sense(self, value: str):
        if value is None:
            self._timing_sense = 'non_unate'
        elif not isinstance(value, str):
            raise TypeError(f'Invalid type for harness timing_sense: {type(value)}')
        else:
            if value == 'pos' or value == 'positive_unate':
                self._timing_sense = 'positive_unate'
            elif value == 'pos' or value == 'negative_unate':
                self._timing_sense = 'negative_unate'
            elif value == 'non' or value == 'non_unate':
                self._timing_sense = 'non_unate'
            else:
                raise ValueError(f'Invalid value for harness timing_sense: {value}')


class SequentialHarness (Harness):
    def __init__(self, target_cell, target_in_port: str, target_out_port: str, direction: str) -> None:
        super().__init__(target_cell, target_in_port, target_out_port, direction)
        self.clock = target_cell.clock
        self.set = target_cell.set
        self.reset = target_cell.reset