"""Maps logic functions to test vectors."""

class Function:
    """Provides function evaluation and mapping faculties"""
    def __init__(self, expression: str, test_vectors: list=[]) -> None:
        """Initialize a new Function"""
        self.expression = expression
        self.stored_test_vectors = test_vectors

    @property
    def operands(self) -> list:
        return list(set([char for char in self.expression if char.isalnum()]))

    def eval(self, *inputs) -> bool:
        """Evaluate this function for the given inputs"""
        # Search expression for single-character operands
        operands = self.operands
        if not len(inputs) == len(operands):
            raise ValueError(f'Expected {len(operands)} inputs for function {self.expression}, got {len(inputs)}')
        f = eval(f'lambda {",".join(operands)}: int({self.expression.replace("~", " not ")})')
        return f(*inputs)

    def truth_table(self) -> list:
        """Return a truth table for this function"""
        table = []
        length = len(self.operands)
        for n in range(2**length):
            input_vector = [int(c) for c in f'{n:0{length}b}']
            result = self.eval(*input_vector)
            table.append([input_vector, result])
        return table

    def __eq__(self, other) -> bool:
        """Compare two functions by checking that their truth tables are the same."""
        result = False
        try:
            result = self.truth_table() == other.truth_table()
        except AttributeError:
            # other is probably not a Function object; assume it's a str expression instead
            func = Function({'expression': other, 'test_vectors': []})
            result = self == func # Recurse
        return result

    def __str__(self) -> str:
        """Return str(self)"""
        return self.expression

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
        # TODO: Make this more efficient
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
        return test_vectors
