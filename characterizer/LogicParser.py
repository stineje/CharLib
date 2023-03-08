# Token definitions 
T_NOT = 0
T_GROUP = 1
T_AND = 2
T_XOR = 3
T_OR = 4
T_OTHER = 5

RULES = lambda S : [
    [Token('~'), 'E'],
    [Token('('), 'E', Token(')')],
    ['N', 'O'],
    [S],
    [Token('&'), 'E'],
    [Token('^'), 'E'],
    [Token('|'), 'E'],
]

def parse_logic(expression: str) -> list:
    """Parse a logic string and return the result in reverse polish notation.
    
    This parser supports parentheses, NOT (~), AND (&), OR (|), and XOR (^) operations.
    The return value is a list of tokens in reverse polish notation.
    """
    return parse(lex(expression))

def parse(tokens: list) -> list:
    stack = ['E']
    reverse_polish_notation = []
    position = 0
    while stack:
        stack_token = stack.pop()
        if isinstance(stack_token, Token):
            # Pop resolved terminals
            if stack_token == tokens[position]:
                position += 1
            else:
                raise ValueError(f'Failed to parse logic string "{"".join([str(t) for t in tokens])}". Parsing failed at token "{tokens[position].symbol}" (position {position})')
        else:
            # Resolve rules using lookup table
            if stack_token == 'E':
                input_token = tokens[position]
                if input_token.type == T_NOT:
                    stack.extend(reversed(RULES('')[0]))
                elif input_token.type == T_GROUP:
                    stack.extend(reversed(RULES('')[1]))
                elif input_token.type == T_AND or input_token.type == T_XOR or input_token.type == T_OR:
                    raise ValueError(f'Unexpected token "{input_token.symbol}" encountered at position {position} in logic string "{"".join([str(t) for t in tokens])}"')
                else:
                    stack.extend(reversed(RULES('')[2]))
            elif stack_token == 'N':
                input_token = tokens[position]
                if input_token.type == T_NOT:
                    stack.extend(reversed(RULES('')[0]))
                elif input_token.type == T_GROUP:
                    stack.extend(reversed(RULES('')[1]))
                elif input_token.type == T_AND or input_token.type == T_XOR or input_token.type == T_OR:
                    raise ValueError(f'Unexpected token "{input_token.symbol}" encountered at position {position} in logic string "{"".join([str(t) for t in tokens])}"')
                else:
                    stack.extend(reversed(RULES(tokens[position])[3]))
            elif stack_token == 'O':
                try:
                    input_token = tokens[position]
                except IndexError:
                    input_token = Token('')
                if input_token.type == T_AND:
                    stack.extend(reversed(RULES('')[4]))
                elif input_token.type == T_XOR:
                    stack.extend(reversed(RULES('')[5]))
                elif input_token.type == T_OR:
                    stack.extend(reversed(RULES('')[6]))
                elif input_token.type == T_NOT or input_token.type == T_GROUP:
                    raise ValueError(f'Unexpected token "{input_token.symbol}" encountered at position {position} in logic string "{"".join([str(t) for t in tokens])}"')
        print(f'stack: {[s for s in reversed(stack)]}')
        print(f'input: {tokens[position:]}\n')
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
        self.symbol = symbol if not symbol == '(' else '()'
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
    assert parse(lex('~(A^B&C)')) == ['~', '()', '^', 'A', '&', 'B', 'C']
    assert parse(lex('_^B | potato')) == ['^', '_', '|', 'B', 'potato']
    assert parse(lex('~~~~A')) == ['~', '~', '~', '~', 'A']
    assert parse(lex('~(A&~C) ^ B')) == ['~', '()', '&', 'A', '~', 'C']
    tokens = lex('~&^|')
    try:
        parse(tokens) # We expect this to fail
    except ValueError:
        pass # Pass if we catch a ValueError