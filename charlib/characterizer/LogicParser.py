# Token definitions 
T_NOT = 0
T_GROUP = 1
T_GROUP_END = 2
T_AND = 3
T_XOR = 4
T_OR = 5
T_OTHER = 6

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
        elif value == '|':
            self._type = T_OR
        else:
            self._type = T_OTHER

# Rules
RULES = lambda S : [
    [Token('~'), 'E', 'O'],             # 0: E -> ~EO
    [Token('('), 'E', Token(')'), 'O'], # 1: E -> (E)O
    [S, 'O'],                           # 2: E -> [A-z,0-9,_]*O
    [Token('&'), 'E', 'O'],             # 3: O -> &EO
    [Token('^'), 'E', 'O'],             # 4: O -> ^EO
    [Token('|'), 'E', 'O'],             # 5: O -> |EO
    [],                                 # 6: O -> null
]

def _get_rule(stack_token, input_token) -> int:
    """Look up a rule by the current stack token and input token"""
    # The left column is the current stack token and the top row is the
    # current input token. The cell selected by these two tokens is the
    # rule we will use to resolve the stack token. Empty cells should
    # result in errors.
    # |     | '~' | '(' | '&' | '^' | '|' | anything else |
    # | --- | --- | --- | --- | --- | --- | ------------- |
    # | 'E' |  0  |  1  |     |     |     |       2       |
    # | 'O' |     |     |  3  |  4  |  5  |       6       |
    rule = 999 # Default to invalid rule
    if stack_token == 'E':
        if input_token.type == T_NOT:
            rule = 0
        elif input_token.type == T_GROUP:
            rule = 1
        elif input_token.type == T_OTHER:
            rule = 2
    elif stack_token == 'O':
        if input_token.type == T_AND:
            rule = 3
        elif input_token.type == T_XOR:
            rule = 4
        elif input_token.type == T_OR:
            rule = 5
        elif input_token.type == T_OTHER or input_token.type == T_GROUP_END:
            rule = 6
    return rule

def _parse(tokens: list) -> list:
    stack = ['O', 'E']
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
        if rule == 0:
            syntax_tree.extend(['O', '~'])
        elif rule == 1:
            syntax_tree.append('O')
        elif rule == 2:
            syntax_tree.extend(['O', named_tokens.pop(0).symbol])
        elif rule == 3:
            last_O_index = -1 - [t for t in reversed(syntax_tree)].index('O')
            syntax_tree.insert(last_O_index+1, '&')
        elif rule == 4:
            last_O_index = -1 - [t for t in reversed(syntax_tree)].index('O')
            syntax_tree.insert(last_O_index+1, '^')
        elif rule == 5:
            last_O_index = -1 - [t for t in reversed(syntax_tree)].index('O')
            syntax_tree.insert(last_O_index+1, '|')
        elif rule == 6:
            try:
                last_O_index = -1 - [t for t in reversed(syntax_tree)].index('O')
                syntax_tree.pop(last_O_index)
            except ValueError:
                pass # We don't add O as aggressively in tree generation, so it's ok if it isn't present
    return syntax_tree

def _lex(expression: str) -> list:
    """Convert a simple boolean logic expression into tokens"""
    tokens = []
    temp = ''
    for c in ''.join(expression.split()):
        if c in ['~', '!', '(', ')', '|', '&', '^']:
            if temp:
                tokens.append(Token(temp))
                temp = ''
            tokens.append(Token(c))
        elif c.isalnum() or c == '_':
            temp += c
        else:
            raise ValueError(f'Invalid character in boolean expression: {c}')
    if temp:
        tokens.append(Token(temp))
    return tokens

def parse_logic(expression: str) -> list:
    """Parse a logic string and return the result in Polish prefix notation.
    
    This parser supports parentheses, NOT (~), AND (&), OR (|), and XOR (^) operations.
    The return value is a list of tokens in Polish prefix notation.

    Note that this parser does not currently support operator precedence. If you want
    operations to happen in a particular order, make sure to use parentheses. 
    """
    return _parse(_lex(expression))

def _resolve_unates(syntax_tree: list, target: str):
    op = syntax_tree.pop(0)
    if op == '~':
        unate_l = -1
        unate_r = None
    elif op == '&':
        unate_l = 1
        unate_r = 1
    elif op == '|' or op == '^':
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
    print(generate_test_vectors('~A', ['A']))