from characterizer.LogicCell import LogicCell, SequentialCell

class Harness:
    """Characterization parameters for one path through a cell
    
    A Harness defines characterization parameters from one input to one
    output of a standard cell circuit."""

    def __init__(self, target_cell: LogicCell, target_in_port: str, target_out_port: str, in_direction: str, out_direction: str, stable_in_port_states: list = []) -> None:
        self._target_in_port = target_in_port   # This pin will change while other inputs will be held stable
        self._stable_in_ports = []              # Pin names to hold stable
        self._stable_in_port_states = []        # States for stable pins
        self._target_out_port = target_out_port # This output will be measured for an expected result
        self._nontarget_out_ports = []          # Output pins we aren't checking

        # Set stable_in_ports
        for port in target_cell.in_ports:
            if not port == self.target_in_port:
                self._stable_in_ports.append(port)
        for state in stable_in_port_states:
            self._stable_in_port_states.append(int(state))
        if len(self.stable_in_port_states) < len(self.stable_in_ports):
            raise ValueError(f'Too few states provided for stable_in_port_states! Exactly {str(len(self.stable_in_ports))} states required for cell {target_cell.name}')

        # Set nontarget_out_ports
        for port in target_cell.out_ports:
            if not port == self.target_out_port:
                self._nontarget_out_ports.append(port)

        # Used for lib file generation
        self.in_direction = in_direction        # rise or fall 
        self.out_direction = out_direction      # rise or fall

    @property
    def target_in_port(self) -> str:
        return self._target_in_port

    @property
    def stable_in_ports(self) -> list:
        return self._stable_in_ports

    @property
    def stable_in_port_states(self) -> list:
        return self._stable_in_port_states

    @property
    def target_out_port(self) -> str:
        return self._target_out_port

    @property
    def nontarget_out_ports(self) -> list:
        return self._nontarget_out_ports

    @property
    def in_direction(self) -> str:
        return self._in_direction

    @in_direction.setter
    def in_direction(self, value: str):
        if value is not None:
            if isinstance(value, str):
                if value == "rise":
                    self._in_direction = str(value)
                elif value == "fall":
                    self._in_direction = str(value)
                else:
                    raise ValueError(f'Harness input direction must be "rise" or "fall", not {value}')
            else:
                raise TypeError(f'Invalid type for harness input direction: {type(value)}')
        else:
            raise ValueError(f'Invalid value for harness input direction: {value}')

    @property
    def target_inport_val(self) -> str:
        if self.in_direction == 'rise':
            return '01'
        elif self.in_direction == 'fall':
            return '10'

    @property
    def out_direction(self) -> str:
        return self._out_direction

    @out_direction.setter
    def out_direction(self, value: str):
        if value is not None:
            if isinstance(value, str):
                if value == "rise":
                    self._out_direction = str(value)
                elif value == "fall":
                    self._out_direction = str(value)
                else:
                    raise ValueError(f'Harness output direction must be "rise" or "fall", not {value}')
            else:
                raise TypeError(f'Invalid type for harness output direction: {type(value)}')
        else:
            raise ValueError(f'Invalid value for harness output direction: {value}')

    @property
    def target_outport_val(self) -> str:
        if self.out_direction == 'rise':
            return '01'
        elif self.out_direction == 'fall':
            return '10'

    @property
    def direction_prop(self) -> str:
        return f'cell_{self.out_direction}'

    @property
    def direction_tran(self) -> str:
        return f'{self.out_direction}_transition'

    @property
    def direction_power(self) -> str:
        return f'{self.out_direction}_power'


class CombinationalHarness (Harness):
    def __init__(self, target_cell: LogicCell, target_in_port: str, target_out_port: str, in_direction: str, out_direction: str, stable_in_port_states: list = [], timing_sense: str = 'non_unate') -> None:
        super().__init__(target_cell, target_in_port, target_out_port, in_direction, out_direction)

        # Used for lib file generation
        self.timing_sense = timing_sense    # Describes the relationship b/t target input and target output

    @property
    def timing_type(self) -> str:
        return "combinational"

    @property
    def timing_sense(self) -> str:
        return self._timing_sense

    @timing_sense.setter
    def timing_sense(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f'Invalid type for harness timing_sense: {type(value)}')
        else:
            if value == 'pos' or value == 'positive_unate':
                self._timing_sense = 'positive_unate'
            elif value == 'neg' or value == 'negative_unate':
                self._timing_sense = 'negative_unate'
            elif value == 'non' or value == 'non_unate':
                self._timing_sense = 'non_unate'
            else:
                raise ValueError(f'Invalid value for harness timing_sense: {value}')


class SequentialHarness (Harness):
    def __init__(self, target_cell: SequentialCell, target_in_port: str, target_out_port: str, in_direction: str, out_direction: str, stable_in_port_states: list = []) -> None:
        super().__init__(target_cell, target_in_port, target_out_port, in_direction, out_direction)
        self.clock = target_cell.clock  # Clock pin
        self.set = target_cell.set      # Set pin (optional)
        self.reset = target_cell.reset  # Reset pin (optional)