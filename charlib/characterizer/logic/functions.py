"""Maps logic functions to truth tables and test vectors."""

import re

from charlib.characterizer.port import Port

OPERAND_REGEX = re.compile(r'(\w+)')

class Function:
    """Provides function evaluation and mapping faculties"""
    def __init__(self, output: str, expression: str, *ports, state=None) -> None:
        """Initialize a new Function

        :param output: The output Port object that this function !esents.
        :param expression: A verilog-style boolean expression computing the output from inputs.
        :param ports: Input Port objects relevant to this function.
        :param state: (optional) The name of the internal state element related to this function.
        """
        # Sanity checks
        if output.direction is Port.Direction.IN:
            raise ValueError(f'Port {output.name} is not an output!')

        # Initialize defaults
        self.output_key = output.name
        self.is_output_inverting = output.is_inverted()
        self.expression = expression.replace('!','~').upper()
        self.state = state
        self.functional_expression = self.expression
        self.ports = dict()
        self.clock = None
        self.clear = None
        self.preset = None
        self.enable = None
        self._cached_test_vectors = list()

        # Save ports which appear in the expression (or are relevant to state)
        # TODO: Handle multiple clocks/sets/resets/enables
        for port in ports:
            match (bool(state), port.role):
                case (True, Port.Role.CLOCK):
                    self.ports[port.name] = self.clock = port
                case (True, Port.Role.CLEAR):
                    self.ports[port.name] = self.clear = port
                case (True, Port.Role.PRESET):
                    self.ports[port.name] = self.preset = port
                case (True, Port.Role.ENABLE):
                    self.ports[port.name] = self.enable = port5
                case _:
                    if port.name in self.operands:
                        self.ports[port.name] = port

        # Modify the functional expression based on state-related roles
        if state:
            get_prefixes = lambda p: ('', '~') if p.is_inverted() else ('~', '')
            expr = self.functional_expression
            if self.clock:
                not_clocking, clocking = get_prefixes(self.clock)
                expr = f'{clocking}{self.clock.name} & ({expr}) |' \
                        f'{not_clocking}{self.clock.name} & {self.state}'
            if self.enable:
                not_enabling, enabling = get_prefixes(self.enable)
                expr = f'{enabling}{self.enable.name} & ({expr}) |' \
                        f'{not_enabling}{self.enable.name} & {self.state}'
            if self.preset:
                not_presetting, presetting = get_prefixes(self.preset)
                if self.is_output_inverting:
                    expr = f'{not_presetting}{self.preset.name} & ({expr})'
                else:
                    expr = f'{presetting}{self.preset.name} | ({expr})'
            if self.clear:
                not_clearing, clearing = get_prefixes(self.clear)
                if self.is_output_inverting:
                    expr = f'{clearing}{self.clear.name} | ({expr})'
                else:
                    expr = f'{not_clearing}{self.clear.name} & ({expr})'
            self.functional_expression = expr

    @property
    def pythonic_expression(self) -> str:
        """Return a python-executable version of the function's expression"""
        py_expr = (
            self.functional_expression
                .replace('~', ' not ')
                .replace('&', ' and ')
                .replace('|', ' or ')
        )
        return py_expr

    @property
    def operands(self) -> list:
        """Return a list of operand names"""
        return sorted(set(OPERAND_REGEX.findall(self.functional_expression)))

    def eval(self, **inputs) -> bool:
        """Evaluate this function for the given inputs"""
        operands = self.operands
        if not len(inputs) == len(operands):
            raise ValueError(f'Expected {len(operands)} inputs for function {self.expression}, got {len(inputs)}')
        callable_expr = eval(f'lambda {",".join(operands)}: int({self.pythonic_expression})')
        return callable_expr(**inputs)

    def truth_table(self) -> list:
        """Return a truth table for this function.

        Truth table values should be interpreted according to the trigger type of the corresponding
        pin. For example, a 1 on the input pin of an inverter implies a static high voltage,
        whereas a 1 on the clock pin of a DFF implies a positive clock edge."""
        table = []
        length = len(self.operands)
        for n in range(2**length):
            result = dict(zip(self.operands, [int(c) for c in f'{n:0{length}b}']))
            result[self.output_key] = self.eval(**result)
            table.append(result)
        return table

    def __eq__(self, other) -> bool:
        """Compare two functions by checking that their truth tables are the same."""
        result = False
        try:
            result = self.truth_table() == other.truth_table()
        except AttributeError:
            # other is probably not a Function object; assume it's a str expression instead
            result = self == Function(other) # Recurse
        return result

    def __str__(self) -> str:
        """Return str(self)"""
        return f'{self.output_key} = {self.expression}'

    @property
    def test_vectors(self) -> list:
        """Return a list of test vectors: conditions which cause a change in the function's output.

        Each test vector consists of a dictionary with pin names for keys and pin states for
        values.

        Test vectors are generated by comparing each row in the truth table to subsequent rows. Any
        pair of rows for which the output differs and only a single input pin differs can be used
        to build a candidate test vector. An additional validation step takes place for cells with
        state: candidates whose initial state does not match the stored internal state are
        discarded, as are any candidates which simultaneously assert both set and reset.

        After generating candidates, test vectors are interpreted based on input trigger types.
        Edge-triggered pin states are interpreted as 0 (fall) -> 10 or 1 (rise) -> 01.

        Because test vector generation is a relatively slow process, test vectors are cached and
        reused after being generated the first time. To regenerate test vectors, clear the
        _cached_test_vectors list attribute.
        """
        # If assigned and not empty, use stored
        if self._cached_test_vectors:
            return self._cached_test_vectors

        # Otherwise generate new test vector candidates
        candidates = []
        table = self.truth_table()
        while table:
            top_row = table.pop(0) # Get top row of table
            # Compare to each later row with a differing output
            for compared_row in [cr for cr in table if not cr[self.output_key] == top_row[self.output_key]]:
                # Check if input differs by only one pin
                deltas = {}
                for pin in top_row.keys():
                    if top_row[pin] == compared_row[pin]:
                        deltas[pin] = str(top_row[pin])
                    else:
                        deltas[pin] = f'{top_row[pin]}{compared_row[pin]}'
                if len(''.join(deltas.values())) == len(top_row) + 2:
                    # Add both the test vector and its reverse
                    candidates.append(deltas)
                    candidates.append({pin: state[::-1] for pin, state in deltas.items()})

        # TODO: Validate & intepret test vector candidates based on state & triggers
        test_vectors = candidates
        self._cached_test_vectors = test_vectors
        return test_vectors

#     def _validate_triggers(self, test_vector) -> bool:
#         """Check that this test vector triggers at least one of the StateFunction's trigger pins.
#
#         This method returns True if at least one pin triggers.
#         """
#         return any([pin_has_active_trigger(pin, test_vector) for pin in self.trigger_pins])
#
#     def _validate_set_reset(self, test_vector) -> bool:
#         """Check that this test vector does not simultaneously assert clear and preset"""
#         preset_asserted = False
#         clear_asserted = False
#         for pin in [p for p in self.trigger_pins if pin_has_active_trigger(p, test_vector)]:
#             if pin.role == Port.Role.CLEAR:
#                 clear_asserted = True
#             elif pin.role == Port.Role.PRESET:
#                 preset_asserted = True
#         return not (clear_asserted and preset_asserted)
#
#
#     @property
#     def test_vectors(self) -> list:
#         """Generate valid test vectors, accounting for internal state"""
#         # Remove all vectorss where internal state does not match output initial state
#         tvs = [t for t in super().test_vectors if t[self.state_variable] == t[self.output_key][0]]
#         # Remove any vectors where no trigger is active, or where set & reset contend
#         tvs = [t for t in tvs if self._validate_triggers(t) and self._validate_set_reset(t)]
#         # TODO: Figure out what to do for cases where level-triggered set/reset are deasserted while clock=1
#         return tvs

def pin_has_active_trigger(pin, test_vector) -> bool:
    """Check whether pin has an activated trigger in test_vector.

    :param pin: A Cell.Pin object to check for active triggers in the test vector.
    :param test_vector: A dict of pin-state mappings generated by Function.test_vectors.

    Pins trigger under different conditions depending on their trigger type:
    - Port.Trigger.LEVEL triggers on 1 (or 0 if inverting). May also occur during rise/fall.
    - Port.Trigger.EDGE triggers only on rise (or fall if inverting).
    """
    match pin.trigger, pin.inversion, test_vector[pin.name]:
        case (Port.Trigger.LEVEL, False, state):
            return '1' in state # active-high trigger
        case (Port.Trigger.LEVEL, True, state):
            return '0' in state # active-low trigger
        case (Port.Trigger.EDGE, False, '01'):
            return True # rising posedge trigger
        case (Port.Trigger.EDGE, True, '10'):
            return True # falling negedge trigger
        case _:
            return False
