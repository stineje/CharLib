"""Tools for reliably evaluating functions"""

from charlib.characterizer.port import Port

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

    def operands(self):
        return sorted(set(OPERAND_REGEX.findall(expression)))


class StateMachineEvaluator:
    """Given current state and inputs, evaluates outputs using an internal finite state machine."""

    def __init__(self, expression, state, clock=None, clear=None, preset=None, enable=None):
        """Initialize a new StateMachineEvaluator"""
        # Build a 1-bit state machine using set, reset, clock, enable, etc.
        self.evaluators = dict()
        self.state = state

        # Build independent evaluators for each state
        shared_expr = expression
        get_prefixes = lambda p: ('', '~') if p.is_inverted() else ('~', '')
        if clock:
            not_clocking, clocking = get_prefixes(clock)
            shared_expr = f'{clocking}{clock.name} & ({shared_expr}) | ' \
                    f'{not_clocking}{clock.name} & {self.state}'
        if enable:
            not_enabling, enabling = get_prefixes(enable)
            shared_expr = f'{enabling}{enable.name} & ({shared_expr}) | ' \
                    f'{not_enabling}{enable.name} & {self.state}'
        self.evaluators[0] = shared_expr
        self.evaluators[1] = shared_expr

        # Handle set & reset differently based on state
        if preset:
            not_presetting, presetting = get_prefixes(preset)
            self.evaluators[0] = f'{presetting}{preset.name} | {self.evaluators[0]}'
            self.evaluators[1] = f'{presetting}{preset.name} | {self.evaluators[1]}'
        if clear:
            not_clearing, clearing = get_prefixes(clear)
            self.evaluators[0] = f'{not_clearing}{clear.name} & {self.evaluators[0]}'
            self.evaluators[1] = f'{not_clearing}{clear.name} & {self.evaluators[1]}'
        self.evaluators[0] = BooleanEvaluator(self.evaluators[0])
        self.evaluators[1] = BooleanEvaluator(self.evaluators[1])

    def __call__(self, **inputs) -> bool
        """Call the expression corresponding to the indicated state"""
        return bool(self.evaluators[inputs[self.state_name]](**inputs))

    def operands(self):
        return self.evaluators[0].operands() | self.evaluators[1].operands()
