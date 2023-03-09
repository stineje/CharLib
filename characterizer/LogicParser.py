# Token definitions 
T_NOT = 0
T_GROUP = 1
T_GROUP_END = 2
T_AND = 3
T_XOR = 4
T_OR = 5
T_OTHER = 6

# Rules
RULES = lambda S : [
    [Token('~'), 'E'],              # 0: E -> ~E
    [Token('('), 'E', Token(')')],  # 1: E -> (E)
    [S, 'O'],                       # 2: E -> [A-z,0-9,_]*O
    [Token('&'), 'E'],              # 3: O -> &E
    [Token('^'), 'E'],              # 4: O -> ^E
    [Token('|'), 'E'],              # 5: O -> |E
    [],                             # 6: O -> null
]

def get_rule(stack_token, input_token) -> int:
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

def parse_logic(expression: str) -> list:
    """Parse a logic string and return the result in reverse polish notation.
    
    This parser supports parentheses, NOT (~), AND (&), OR (|), and XOR (^) operations.
    The return value is a list of tokens in reverse polish notation.
    """
    return parse(lex(expression))

def parse(tokens: list) -> list:
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
            rule = get_rule(stack_token, input_token)
            try:
                stack.extend(reversed(RULES(input_token)[rule]))
            except IndexError: # Error due to nonexistent rule
                raise ValueError(f'Failed to parse logic string "{"".join([str(t) for t in tokens])}". Parsing failed at position {position}')
            rule_sequence.append(rule)
        print(f'stack: {stack}')
        print(f'inpup: {tokens[position:]}')
    print(f'rules: {rule_sequence}')
    
    # Now that we know the production rules, produce an AST in RPN format
    reverse_polish_notation = []
    named_tokens = [n for n in tokens if n.type == T_OTHER]
    for rule in rule_sequence:
        if rule == 0:
            reverse_polish_notation.append('~')
        elif rule == 1:
            reverse_polish_notation.append('()')
        elif rule == 2:
            reverse_polish_notation.extend(['O', named_tokens.pop(0).symbol])
        elif rule == 3:
            reverse_polish_notation.append('&')
        elif rule == 4:
            reverse_polish_notation.append('^')
        elif rule == 5:
            reverse_polish_notation.append('|')
        elif rule == 6:
            last_O_index = -1 - [t for t in reversed(reverse_polish_notation)].index('O')
            reverse_polish_notation.pop(last_O_index)
        print(f'rpn:   {reverse_polish_notation}')
    return reverse_polish_notation

def lex(expression: str) -> list:
    """Lexes a simple boolean logic expression into tokens"""
    tokens = []
    temp = ''
    for c in ''.join(expression.split()):
        if c in ['~', '(', ')', '|', '&', '^']:
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

class Token:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol # if not symbol == '(' else '()'
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
        if value == '~':
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

if __name__ == '__main__':
    # If run as main, test parser
    parse_logic('~(A&~C) ^ B')
    # assert parse_logic('~(A^B&C)') == ['~', '()', '^', 'A', '&', 'B', 'C']
    # assert parse_logic('_^B | potato') == ['^', '_', '|', 'B', 'potato']
    # assert parse_logic('~~~~A') == ['~', '~', '~', '~', 'A']
    # assert parse_logic('~(A&~C) ^ B') == ['^', '~', '()', '&', 'A', '~', 'C', 'B']
    # assert parse_logic('A&B&C&D&E&F&G&H&I&J&K') == ['&', 'A', '&', 'B', '&', 'C', '&', 'D', '&', 'E', '&', 'F', '&', 'G', '&', 'H', '&', 'I', '&', 'J', 'K']
    # tokens = lex('~&^|')
    # assert tokens == [Token('~'), Token('&'), Token('^'), Token('|')]
    # try:
    #     parse(tokens) # We expect this to fail
    # except ValueError:
    #     pass # Pass if we catch a ValueError