"""Maps logic functions to test vectors"""

class Function:
    """Provides function evaluation and mapping faculties"""
    def __init__(self, func_dict: dict) -> None:
        """Initialize a new Function"""
        self.expression = func_dict['expression']
        self.test_vectors = func_dict['test_vectors']

    def eval(self, *inputs) -> bool:
        """Evaluate this function for the given inputs"""
        # Search expression for single-character operands
        operands = [char for char in self.expression if char.isalnum()]
        f = eval(f'lambda {",".join(operands)}: int({self.expression.replace("~", " not ")})')
        return f(*inputs)
