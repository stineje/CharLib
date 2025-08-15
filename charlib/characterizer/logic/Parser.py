# Global Token definitions
T_NOT = 0
T_GROUP = 1
T_GROUP_END = 2
T_AND = 3
T_XOR = 4
T_XNOR = 5
T_OR = 6
T_OTHER = 7

class Token:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol if not symbol == '!' else '~'
        self.type = symbol

    def __str__(self) -> str:
        return self.symbol

    def __repr__(self) -> str:
        return f'Token("{self.symbol}")'

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self.symbol == other.symbol

    @property
    def type(self) -> int:
        return self._type

    @type.setter
    def type(self, value: str):
        if value == '~' or value == '!':
            self._type = T_NOT
        elif value == '(':
            self._type = T_GROUP
        elif value == ')':
            self._type = T_GROUP_END
        elif value == '&' or value == '*':
            self._type = T_AND
        elif value == '^':
            self._type = T_XOR
        elif value == '~^':
            self._type = T_XNOR
        elif value == '|' or value == '+':
            self._type = T_OR
        else:
            self._type = T_OTHER

    @property
    def is_binary_operator(self) -> bool:
        return self.type in range(T_AND, T_OR+1)

# Rules
# E = expression
# U = unary operator
# B = binary operator
RULES = lambda S : [
    [S],                            # 0: E -> [A-z,0-9,_]* OR U -> ((~)|(!)) OR B -> (\|)|((~\^)|(\^~)|(\^))|(&)
    [Token('('), 'E', Token(')')],  # 1: E -> (E)
    ['U', 'E'],                     # 2: E -> UE
    ['E', 'B', 'E'],                # 3: E -> EBE
]

def _get_rule(stack_token, input_sequence) -> (int, int):
    """Look up a rule by the current stack token and input sequence"""
    # 3 If the sequence contains any B not in grouping symbols
    #   | On Stack: | Condition:
    # --|-----------|
    #   | E | U | B |
    # --|---|---|---|------------
    # R | 3 |   |   | Binary operator in input sequence (not within matched grouping symbols)
    # u | 2 |   |   | Input sequence starts with unary operator ('~' or '!')
    # l | 1 |   |   | Input sequence starts with grouping symbol
    # e | 0 | 0 | 0 | Input sequence contains a terminal
    if not input_sequence:
        raise ValueError('Unable to determine rule for empty sequence!')
    if stack_token == 'E':
        if any([token.is_binary_operator for token in input_sequence]):
            try:
                op_index = _find_least_precedent_binary_operator(input_sequence)
                return (3, op_index)
            except ValueError:
                # If we didn't return, either there is a syntax error OR all operators are within
                # parentheses. Check other conditions
                pass
        if input_sequence[0] == Token('~'):
            return (2, None)
        elif input_sequence[0] == Token('('):
            return (1, None)
        else:
            return (0, None)
    elif stack_token == 'U' and input_sequence[0] == Token('~'):
        return (0, None)
    elif stack_token == 'B' and input_sequence[0].is_binary_operator:
        return (0, None)
    else:
        # Syntax error
        raise ValueError() # TODO: check error type, add a decent message

def _has_matching_parentheses(tokens: list) -> bool:
    # Check if the list of tokens has matching grouping symbols
    unmatched_parentheses = 0
    for token in tokens:
        if token.type == T_GROUP:
            unmatched_parentheses += 1
        elif token.type == T_GROUP_END:
            unmatched_parentheses -= 1
    return unmatched_parentheses == 0

def _find_least_precedent_binary_operator(tokens: list) -> int:
    # Locate the least precedent binary operator in the list (outside of grouping symbols) and return its index
    for op_types in [[T_OR], [T_XOR, T_XNOR], [T_AND]]:
        matching_ops = [op.type in op_types for op in tokens]
        for matching_op in matching_ops: # FIXME: There's probably a way to do this more simply with e.g. enumerate
            if matching_op:
                op_index = matching_ops.index(matching_op)
                if _has_matching_parentheses(tokens[:op_index]):
                    return op_index
                else:
                    matching_ops[op_index] = False # Move on to the next matching op, if any
        # If we didn't return on this iteration, check the next group of op_types
    raise ValueError('No binary operators outside of grouping symbols')

def _parse(tokens: list) -> list:
    # Parse a list of lexed tokens and return an abstract syntax tree
    stack = ['E']
    position = 0
    syntax_tree = []

    while stack:
        stack_token = stack.pop()

        if isinstance(stack_token, Token): # Pop resolved terminals
            if stack_token == tokens[position] or stack_token.type == T_GROUP_END:
                if stack_token.type == T_OTHER or stack_token.type == T_NOT:
                    syntax_tree.append(stack_token.symbol)
                position += 1
            else:
                raise ValueError(f'Parsing failed: token "{tokens[position]}" did not match stack token "{stack_token}" at position {position}')
        else: # Resolve rules by lookup
            (rule, op_index) = _get_rule(stack_token, tokens[position:])
            if op_index is not None:
                # Immediately append the operation to the syntax tree
                syntax_tree.append(tokens[position+op_index].symbol)
                # Split binary operations and parse left & right separately
                syntax_tree.extend(_parse(tokens[position:position+op_index]))
                syntax_tree.extend(_parse(tokens[position+op_index+1:]))
            else:
                stack.extend(reversed(RULES(tokens[position])[rule]))

    return syntax_tree


def _lex(expression: str) -> list:
    """Convert a simple boolean logic expression into tokens"""
    tokens = []
    temp = ''
    for c in ''.join(expression.split()):
        if c == '~':
            if temp:
                tokens.append(Token(temp))
                temp = ''
            temp += c
        elif c == '^':
            if temp == '~':
                temp += c
                tokens.append(Token(temp))
                temp = ''
            else:
                if temp:
                    tokens.append(Token(temp))
                    temp = ''
                tokens.append(Token(c))
        elif c in ['!', '(', ')', '|', '&', '+', '*']:
            if temp:
                tokens.append(Token(temp))
                temp = ''
            tokens.append(Token(c))
        elif c.isalnum() or c == '_':
            if temp == '~':
                tokens.append(Token(temp))
                temp = ''
            temp += c
        else:
            raise ValueError(f'Invalid character in boolean expression: {c}')
    if temp:
        tokens.append(Token(temp))
    return tokens

def parse_logic(expression: str) -> list:
    """Parse a logic string and return the result in Polish prefix notation.

    This parser supports the following standard SystemVerilog operations:
        - Grouping symbols: (, )
        - Unary negation: ~, !
        - Bitwise binary operations: &, ^, ~^, |

    The return value is a list of tokens in Polish prefix notation.
    """
    return _parse(_lex(expression))

def _resolve_unates(syntax_tree: list, target: str):
    """Determine the 'unateness' of the function with respect to the target input."""
    op = syntax_tree.pop(0)
    if op == '~':
        unate_l = -1
        unate_r = None
    elif op == '&' or op == '*':
        unate_l = 1
        unate_r = 1
    elif str(op) in ['|', '+', '^', '~^']:
        # can't determine these yet - have to check which side contains the target
        unate_l = 0
        unate_r = 0
    else:
        return syntax_tree, {op: 1} # Return symbol
    # Resolve left side
    syntax_tree, unates = _resolve_unates(syntax_tree, target)
    # Check for target in left side
    if unate_l == 0 and target in unates:
        unate_l = 1
    else:
        unate_l = -1
    for k,u in unates.items():
        unates[k] = unate_l * u
    # Resolve right side
    if unate_r is not None:
        syntax_tree, unates_r = _resolve_unates(syntax_tree, target)
        # Check for target in right side
        if unate_r == 0 and target in unates_r:
            unate_r = 1
        else:
            unate_r = -1
        for k,u in unates_r.items():
            unates[k] = unate_r * u
    return syntax_tree, unates

def generate_test_vectors(expression: str, inputs: list) -> list:
    # This method doesn't work correctly for some expressions, and will be revisited and fixed later.
    # Might be fixed now, since the parser has been entirely rewritten. Needs more testing.
    test_vectors = []
    for target_port in inputs:
        # Generate two test vectors for each input: one rising, one falling
        for state in ['01', '10']:
            input_vector = []
            for port in inputs:
                # Get unates for each variable
                _, unates = _resolve_unates(parse_logic(expression), target_port)
                # Make sure we don't have any unexpected ports
                for k in unates.keys():
                    if k not in inputs:
                        raise ValueError(f'Unexpected port name {k} encountered during test vector generation')
                # Use unates to determine port states
                if port is target_port:
                    input_vector.append(state)
                    output_state = state if unates[port] > 0 else state[::-1]
                else:
                    input_vector.append(str(int(unates[port] > 0)))
            test_vectors.append([output_state, input_vector])
    return test_vectors


if __name__ == '__main__':
    # If run as main, test lexer & parser
    assert _lex('A&B') == [Token('A'), Token('&'), Token('B')]
    assert _lex('C^~D') == [Token('C'), Token('^'), Token('~'), Token('D')]
    assert _lex('E~^F') == [Token('E'), Token('~^'), Token('F')]
    assert _lex('apples|bananas') == [Token('apples'), Token('|'), Token('bananas')]
    assert parse_logic('~(A^B&C)') == ['~', '^', 'A', '&', 'B', 'C']
    assert parse_logic('_^B | potato') == ['|', '^', '_', 'B', 'potato']
    assert parse_logic('~~~~A') == ['~', '~', '~', '~', 'A']
    assert parse_logic('(~(A&~C)) ^ B') == ['^', '~', '&', 'A', '~', 'C', 'B']
    assert parse_logic('A&B&C&D&E&F&G&H&I&J&K') == ['&', 'A', '&', 'B', '&', 'C', '&', 'D', '&', 'E', '&', 'F', '&', 'G', '&', 'H', '&', 'I', '&', 'J', 'K']
    tokens = _lex('~&^|')
    assert tokens == [Token('~'), Token('&'), Token('^'), Token('|')]
    try:
        _parse(tokens) # We expect this to fail
        raise AssertionError # This line should never be executed
    except ValueError:
        pass # Pass if we catch a ValueError
    assert parse_logic('b&a&a') == ['&', 'b', '&', 'a', 'a']
    assert parse_logic('(C&(A^B))|(A&B)') == ['|','&','C','^','A','B','&','A','B']
    assert parse_logic('(~(~A&C)) ^ B') == ['^', '~', '&', '~', 'A', 'C', 'B']
    assert parse_logic('a&b|c&d') == ['|', '&', 'a', 'b', '&', 'c', 'd']
    assert parse_logic('a&b^c&d') == ['^', '&', 'a', 'b', '&', 'c', 'd']
    assert parse_logic('a^b|c^d') == ['|', '^', 'a', 'b', '^', 'c', 'd']
    assert parse_logic('a|b^c|d') == ['|', 'a', '|', '^', 'b', 'c', 'd']
    assert parse_logic('a&(b|c)&d') == ['&', 'a', '&', '|', 'b', 'c', 'd']

    # Test TV generation
    assert generate_test_vectors('~A', ['A']) == [['10', ['01']], ['01', ['10']]]
