from characterizer.LogicCell import LogicCell, SequentialCell

class Harness:
    """Characterization parameters for one path through a cell
    
    A Harness defines characterization parameters from one input to one
    output of a standard cell circuit."""

    def __init__(self, target_cell: LogicCell, test_vector: list) -> None:
        self._stable_in_ports = []              # input pins to hold stable
        self._stable_in_port_states = []        # states for stable pins
        self._nontarget_out_ports = []          # output pins that we aren't specifically evaluating
        self._nontarget_out_port_states = []    # states for nontarget outputs
        
        # Parse inputs from test vector
        # Test vector should be formatted like [in1, ..., inN, out1, ..., outM]
        print(test_vector)
        num_inputs = len(target_cell.in_ports)
        num_outputs = len(target_cell.out_ports)
        input_test_vector = test_vector[0:num_inputs]
        print(input_test_vector)
        output_test_vector = test_vector[num_inputs:num_inputs+num_outputs]
        print(output_test_vector)
        state_to_direction = lambda s: 'rise' if s == '01' else 'fall' if s == '10' else s

        # Get inputs from test vector
        print("Input")
        for in_port, state in zip(target_cell.in_ports, input_test_vector):
            if len(state) > 1:
                self._target_in_port = in_port
                self.in_direction = state_to_direction(state)
            else:
                self._stable_in_ports.append(in_port)
                self._stable_in_port_states.append(state)
        if not self._target_in_port:
            raise ValueError(f'Unable to parse target input port from test vector {test_vector}')

        # Get outputs from test vector
        for out_port, state in zip(target_cell.out_ports, output_test_vector):
            if len(state) > 1:
                self._target_out_port = out_port
                self.out_direction = state_to_direction(state)
            else:
                self._nontarget_out_ports.append(out_port)
                self._nontarget_out_port_states.append(state)
        if not self._target_out_port:
            raise ValueError(f'Unable to parse target output port from test vector {test_vector}')

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
    def __init__(self, target_cell: LogicCell, test_vector, timing_sense: str = 'non_unate') -> None:
        super().__init__(target_cell, test_vector)

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
    def __init__(self, target_cell: SequentialCell, test_vector) -> None:
        super().__init__(target_cell, test_vector)
        self.clock = target_cell.clock  # Clock pin
        self.set = target_cell.set      # Set pin (optional)
        self.reset = target_cell.reset  # Reset pin (optional)

        # TODO