"""Maps logic functions to truth tables and test vectors."""

import re

class Function:
    OUT = '__output' # key for function outputs in test vectors and truth tables

    """Provides function evaluation and mapping faculties"""
    def __init__(self, expression: str, test_vectors: list=[]) -> None:
        """Initialize a new Function"""
        self.expression = expression.replace('!','~').upper()
        self.stored_test_vectors = test_vectors

    @property
    def pythonic_expression(self) -> str:
        """Return a python-executable version of the function's expression"""
        py_expr = (
            self.expression
                .replace('~', ' not ')
                .replace('&', ' and ')
                .replace('|', ' or ')
        )
        return py_expr

    @property
    def operands(self) -> list:
        """Return a list of operand names"""
        return sorted(set(re.findall(r'(\w+)', self.expression)))

    def eval(self, **inputs) -> bool:
        """Evaluate this function for the given inputs"""
        operands = self.operands
        if not len(inputs) == len(operands):
            raise ValueError(f'Expected {len(operands)} inputs for function {self.expression}, got {len(inputs)}')
        callable_expr = eval(f'lambda {",".join(operands)}: int({self.pythonic_expression})')
        return callable_expr(**inputs)

    def truth_table(self) -> list:
        """Return a truth table for this function"""
        table = []
        length = len(self.operands)
        for n in range(2**length):
            result = dict(zip(self.operands, [int(c) for c in f'{n:0{length}b}']))
            result[self.OUT] = self.eval(**result)
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
        return self.expression

    def __repr__(self) -> str:
        """Return repr(self)"""
        return f'Function("{self.expression}", {self.test_vectors})'

    def to_yaml(self, name) -> str:
        """Convert to a YAML-formatted string"""
        func_str = [
            f'{name}:',
            f'    expression: {self.expression}',
            '    test_vectors:'
        ]
        for tv in self.test_vectors:
            func_str.append(f'        - {tv}')
        return '\n'.join(func_str)

    @property
    def test_vectors(self) -> list:
        """Generate test vectors, or return stored configuration."""
        if self.stored_test_vectors: # If assigned and not empty, use stored
            return self.stored_test_vectors
        # The basic idea here is to use the truth tables we already have to generate test vectors.
        # Look at each row one at a time, and compare it to all lower rows in the truth table which
        # have a different output.
        # If a row differs only by a single input and the output, then we can use that delta for a
        # test vector.
        test_vectors = []
        table = self.truth_table()
        while table:
            top_row = table.pop(0) # Get top row of table
            # Compare to each later row with a differing output
            for compared_row in [cr for cr in table if not cr[self.OUT] == top_row[self.OUT]]:
                # Check if input differs by only one pin
                deltas = {}
                for pin in top_row.keys():
                    if top_row[pin] == compared_row[pin]:
                        deltas[pin] = str(top_row[pin])
                    else:
                        deltas[pin] = f'{top_row[pin]}{compared_row[pin]}'
                if len(''.join(deltas.values())) == len(top_row) + 2:
                    # Add both the test vector and its reverse
                    test_vectors.append(deltas)
                    test_vectors.append({pin: state[::-1] for pin, state in deltas.items()})
        self.stored_test_vectors = test_vectors
        return test_vectors


class StateFunction(Function):
    """A Function with internal state"""
    def __init__(self, expression: str, state_name: str, clock=None, enable=None,
                 preset=None, clear=None):
        """Initialize a function with internal recurrence and optional state-related inputs.

        :param expression: A boolean expression describing how this output changes state.
        :param state_name: The name of the state storage element for this output.
        :param clock: The Cell.Pin with the clock role (if any).
        :param enable: The Cell.Pin with the enable role (if any).
        :param preset: The Cell.Pin with the set/preset role (if any).
        :param clear: The Cell.Pin with the clear/reset role (if any).
        """
        self.base_expression = expression
        self.state_variable = state_name

        # Add each state-related input cumulatively, if present
        if clock:
            (clock_prefix, not_clock_prefix) = ('~', '') if clock.is_inverted() else ('', '~')
            expression = f'{clock_prefix}{clock.name} & ({expression}) | ' \
                         f'{not_clock_prefix}{clock.name} & {state_name}'
        if enable:
            (enable_prefix, not_enable_prefix) = ('~', '') if enable.is_inverted() else ('', '~')
            expression = f'{enable_prefix}{enable.name} & ({expression}) | ' \
                         f'{not_enable_prefix}{enable.name} & {state_name}'
        if preset:
            preset_prefix = '~' if preset.is_inverted() else ''
            expression = f'{preset_prefix}{preset.name} | ({expression})'
        if clear:
            not_clear_prefix = '' if clear.is_inverted() else '~'
            expression = f'{not_clear_prefix}{clear.name} & ({expression})'
        super().__init__(expression)

    def __str__(self) -> str:
        """Return str(self)"""
        return str(self.base_expression)

    @property
    def test_vectors(self) -> list:
        """Generate valid test vectors, accounting for internal state"""
        # Remove all TVs where internal state does not match output initial state
        return [t for t in super().test_vectors if t[self.state_variable] == t[self.OUT][0]]



def generate_yml(expressions):
    """Generates a YAML map of the registered expressions"""
    document = ""
    for expr in expressions:
        func = Function(expr)
        document += func.to_yaml(expr) + "\n"
    print(document)
