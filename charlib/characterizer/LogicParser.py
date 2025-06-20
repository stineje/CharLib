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
        elif value == '&':
            self._type = T_AND
        elif value == '^':
            self._type = T_XOR
        elif value == '~^':
            self._type = T_XNOR
        elif value == '|':
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
    [S],                            # 0: E -> [A-z,0-9,_]*
    [Token('('), 'E', Token(')')],  # 1: E -> (E)
    ['U', 'E'],                     # 2: E -> UE
    ['E', 'B', 'E'],                # 3: E -> EBE
    [Token(S)],                     # 4: U -> ((~)|(!)) or B -> (\|)|((~\^)|(\^~)|(\^))|(&)
]

def _get_rule(stack_token, input_sequence) -> int:
    """Look up a rule by the current stack token and input sequence"""
    # 3 If the sequence contains any B not in grouping symbols
    #   | On Stack: | Condition:
    # --|-----------|
    #   | E | U | B |
    # --|---|---|---|------------
    #   | 3 |   |   | Binary operator in input sequence (not within matched grouping symbols)
    # R | 2 |   |   | Input sequence starts with unary operator ('~' or '!')
    # u | 1 |   |   | Input sequence starts with grouping symbol
    # l | 0 |   |   | Input sequence contains no operators
    # e |   | 4 |   | Input sequence contains a unary operator
    #   |   |   | 4 | Input sequence contains a binary operator
    rule = -1 # Default to invalid rule
    if stack_token == 'E':
        op_mask = [token.is_binary_operator for token in input_sequence]
        if any(op_mask):
            # TODO: Figure out how to tell if the binary op is within grouping symbols
            # Idea:
            # 1. Split sequence on the leftmost lowest-precedence binary op we haven't tried yet.
            # 2. Check if left side has matched grouping symbols. If not, try the next binary op (if any)
            #    - Note we don't need to check the right side for matched grouping symbols; it must if the left side does
            for op_types in [(Token('|')), (Token('^~'), Token('~^')), (Token('&'))]:
                print([op in op_types for op in input_sequence[op_mask]])
        elif input_sequence[0] == Token('~'):
            rule = 2
        elif input_sequence[0] == Token('('):
            rule = 1
        else:
            rule = 0
    elif stack_token == 'U' and input_sequence[0] == Token('~'):
        rule = 4
    elif stack_token == 'B' and input_sequence[0].is_binary_operator:
        rule = 4


def _parse(tokens: list) -> list:
    stack = ['E']
    position = 0
    rule_sequence = []
    while stack:
        stack_token = stack.pop()
        if isinstance(stack_token, Token):
            # Pop resolved terminals
            input_token = tokens[position]
            if stack_token == input_token:
                position += 1
            else:
                raise ValueError(f'Failed to parse logic string "{"".join([str(t) for t in tokens])}". Parsing failed at token "{input_token.symbol}" (position {position})')
        else:
            # Resolve rules using lookup table
            try:
                input_token = tokens[position]
            except IndexError:
                input_token = Token('') # Empty token of type T_OTHER
            rule = _get_rule(stack_token, input_token)
            try:
                stack.extend(reversed(RULES(input_token)[rule]))
            except IndexError: # Error due to nonexistent rule
                raise ValueError(f'Failed to parse logic string "{"".join([str(t) for t in tokens])}". Parsing failed at position {position}')
            rule_sequence.append(rule)

    # Now that we know the production rules, produce an AST in prefix format
    syntax_tree = []
    named_tokens = [n for n in tokens if n.type == T_OTHER]
    for rule in rule_sequence:
        print(rule)
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
        elif c in ['!', '(', ')', '|', '&']:
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
    l = _lex(expression)
    print(l)
    p = _parse(l)
    print(p)
    # return _parse(_lex(expression))
    return p

def _resolve_unates(syntax_tree: list, target: str):
    """Determine the 'unateness' of the function with respect to the target input."""
    op = syntax_tree.pop(0)
    if op == '~':
        unate_l = -1
        unate_r = None
    elif op == '&':
        unate_l = 1
        unate_r = 1
    elif str(op) in ['|', '^', '~^', '^~']:
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
    # If run as main, test parser
    assert parse_logic('~(A^B&C)') == ['~', '^', 'A', '&', 'B', 'C']
    assert parse_logic('_^B | potato') == ['^', '_', '|', 'B', 'potato']
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
    print(parse_logic('(~(~A&C)) ^ B')) # Should give ['^', '~', '&', '~', 'A', 'C', 'B']
    assert parse_logic('(~(~A&C)) ^ B') == ['^', '~', '&', '~', 'A', 'C', 'B']
    print(generate_test_vectors('~A', ['A']))
