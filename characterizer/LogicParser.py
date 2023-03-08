def parse(tokens: list) -> dict:
    """Parses simple boolean logic expressions.
    
    EBNF:
    E -> '(' E ')'
    E -> '~' E
    E -> E '&' E
    E -> E '^' E
    E -> E '|' E
    E -> S
    S -> [A-Z,a-z,0-9,_]*

    The result is a dictonary which describes the abstract syntax tree.
    """
    RULES = lambda S : [
        [Token('('), 'E', Token(')')],
        [Token('~'), 'E'],
        [S, Token('&'), 'E'],
        [S, Token('^'), 'E'],
        [S, Token('|'), 'E'],
        [S]
    ]
    ast = {}
    stack = ['E']
    position = 0
    while stack:
        stack_token = stack.pop()
        if isinstance(stack_token, Token):
            # Handle terminals
            if stack_token == tokens[position]:
                position += 1
            else:
                print('Parsing failed!')
        else:
            # Resolve rules
            rule = tokens[position].rule
            if rule == 5:
                # Look ahead 1 to see if there is an operator
                try:
                    if 1 < tokens[position+1].rule < rule:
                        rule = tokens[position+1].rule
                except IndexError:
                    pass
            stack.extend(reversed(RULES(tokens[position])[rule]))
        print(f'stack: {[i for i in reversed(stack)]}')
        print(f'input: {tokens[position:]}')

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
    def __init__(self, name: str) -> None:
        self.name = name
        self.rule = name

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f'Token("{self.name}")'
    
    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self.name == other.name
    
    @property
    def rule(self) -> int:
        return self._rule

    @rule.setter
    def rule(self, value: str):
        if value == '(':
            self._rule = 0
        elif value == '~':
            self._rule = 1
        elif value == '&':
            self._rule = 2
        elif value == '^':
            self._rule = 3
        elif value == '|':
            self._rule = 4
        else:
            self._rule = 5

if __name__ == '__main__':
    # If run as main, test parser
    print(parse(lex('~(A^B&C)')))
    print(parse(lex('A^B | potato')))
    print(parse(lex('~~~~A')))
    print(parse(lex('~(A&~C) ^ B')))