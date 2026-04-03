"""Tools for reliably evaluating functions"""

OPERAND_REGEX = re.compile(r'(\w+)')

class BooleanEvaluator:
    """Evaluates Boolean functions by converting them to static Python callables"""

    def __init__(self, expression: str) -> None:
        """Initialize a new BooleanEvaluator"""
        operands = sorted(set(OPERAND_REGEX.findall(expression)))
        pythonic_expr = (
            expression.upper()
                .replace('!', ' not ')
                .replace('~', ' not ')
                .replace('&', ' and ')
                .replace('|', ' or ')
        )
        self.expression = eval(f'lambda {",".join(operands)}: int(pythonic_expr)')

    def __call__(self, **inputs) -> bool
        """Call the evaluator's stored expression"""
        return bool(self.expression(**inputs))


class StateMachineEvaluator:
    """Given current state and inputs, evaluates outputs using an internal finite state machine."""

    def __init__(self, expression, state_variable, *state_related_ports):
        pass # TODO: build a state machine using set, reset, clock, enable, etc.


    def __call__(self, **inputs) -> bool
        """Call the evaluator's stored expression"""
