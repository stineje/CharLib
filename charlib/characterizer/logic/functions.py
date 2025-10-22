"""Maps logic functions to truth tables and test vectors."""

import re

class Function:
    """Provides function evaluation and mapping faculties"""
    def __init__(self, expression: str, test_vectors: list=[]) -> None:
        """Initialize a new Function"""
        self.expression = expression.replace('!','~').upper()
        self.stored_test_vectors = test_vectors

    @property
    def operands(self) -> list:
        """Return a list of operand names"""
        return sorted(set(re.findall(r'(\w+)', self.expression)))

    def eval(self, **inputs) -> bool:
        """Evaluate this function for the given inputs"""
        operands = self.operands
        if not len(inputs) == len(operands):
            raise ValueError(f'Expected {len(operands)} inputs for function {self.expression}, got {len(inputs)}')
        f = eval(f'lambda {",".join(operands)}: int({self.expression.replace("~", " not ").replace("&", " and ").replace("|", " or ")})')
        return f(**inputs)

    def truth_table(self) -> list:
        """Return a truth table for this function"""
        table = []
        length = len(self.operands)
        for n in range(2**length):
            input_vector = [int(c) for c in f'{n:0{length}b}']
            result = self.eval(**dict(zip(self.operands, input_vector)))
            table.append([input_vector, result])
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
        return self.expression.replace('~', '!')

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
            row = table.pop(0) # Get top row of table
            # Compare to each later row with a differing output
            for compared_row in [r for r in table if not r[1] == row[1]]:
                # Check if input differs by only one pin
                delta_row = []
                delta_count = 0
                for i, j in zip(row[0], compared_row[0]):
                    if i == j:
                        delta_row.append(str(i))
                    else:
                        delta_row.append(f'{i}{j}')
                        delta_count += 1
                if delta_count == 1:
                    # Add the output to the new test vector
                    delta_row.append(f'{row[1]}{compared_row[1]}')
                    test_vectors.append(delta_row)
                    # Append a second copy with each element reversed
                    test_vectors.append([s[::-1] for s in delta_row])
        self.stored_test_vectors = test_vectors
        return test_vectors


class StateFunction(Function):
    """A Function with internal state"""
    def __init__(self, expression: str, state_name: str, clock=None, enable=None,
                 preset=None, clear=None):
        """Initialize a function with internal recurrence and optional state-related inputs.

        :param expression:
        :param state_name:
        :param clock:
        :param enable:
        :param preset:
        :param clear:
        """
        self.base_expression = str(expression)

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
        return self.base_expression.replace('~', '!')


def generate_yml():
    """Generates a YAML map of the registered expressions"""
    document = ""
    for name, expr in registered_expressions.items():
        func = Function(expr)
        document += func.to_yaml(name) + "\n"
    print(document)
