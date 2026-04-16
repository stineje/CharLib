"""Tools for reliably evaluating functions"""

import re
from charlib.characterizer.port import Port

OPERAND_REGEX = re.compile(r'(\w+)')

class BooleanEvaluator:
    """Evaluates Boolean functions by converting them to static Python callables"""

    def __init__(self, expression: str) -> None:
        """Initialize a new BooleanEvaluator"""
        self.raw_expression = expression
        self.expression = (
            expression.upper()
                .replace('!', ' not ')
                .replace('~', ' not ')
                .replace('&', ' and ')
                .replace('|', ' or ')
        )

    def __call__(self, **inputs) -> bool:
        """Call the evaluator's stored expression"""
        evaluator = eval(f'lambda {",".join(self.operands)}: {self.expression}')
        return evaluator(**inputs)

    @property
    def operands(self):
        return sorted(set(OPERAND_REGEX.findall(self.raw_expression)))

    def __str__(self):
        return self.raw_expression

    def __repr__(self):
        return f'BooleanEvaluator({self.expression})'


class StateMachineEvaluator:
    """Given current state and inputs, evaluates outputs using an internal pseudo-FSM."""

    def __init__(self, expression, preset=None, clear=None, preset_state=1, clear_state=0):
        """Initialize a new StateMachineEvaluator

        :param expression: A string containing a Boolean expression for the next state.
        :param preset: A Pin object that sets the state to preset_state when asserted.
        :param clear: A Pin object that sets the state to clear_state when asserted.
        """
        self.expression = BooleanEvaluator(expression)
        self.preset = preset
        self.preset_state = preset_state
        self.clear = clear
        self.clear_state = clear_state

    def __call__(self, **inputs) -> bool:
        """Compute the next state based on the inputs"""
        # FIXME: clear/preset priority order varies for different cells, and should be user-configurable
        if self.clear and self.clear.is_asserted(inputs.pop(self.clear.name)):
            return self.clear_state
        elif self.preset and self.preset.is_asserted(inputs.pop(self.preset.name)):
            return self.preset_state
        else:
            return self.expression(**inputs)

    @property
    def operands(self):
        operands = set(self.expression.operands)
        if self.preset:
            operands.add(self.preset.name)
        if self.clear:
            operands.add(self.clear.name)
        return sorted(operands)

    def __repr__(self):
        return f'StateMachineEvaluator({str(self.expression)}, ' \
                f'preset={self.preset}, clear={self.clear}, ' \
                f'preset_state={self.preset_state}, clear_state={self.clear_state})'
