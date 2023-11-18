from functions import Function

if __name__ == '__main__':
    expressions = {
        'BUF': 'a',
        'INV': '~a',
        'AND2': 'a&b',
        'AND3': 'a&b&c',
        'AND4': 'a&b&c&d',
        'OR2': 'a|b',
        'OR3': 'a|b|c',
        'OR4': 'a|b|c|d',
        'XOR2': 'a^b',
        'XOR3': 'a^b^c',
        'XOR4': 'a^b^c^d',
        'NAND2': '~(a&b)',
        'NAND3': '~(a&b&c)',
        'NAND4': '~(a&b&c&d)',
        'NOR2': '~(a|b)',
        'NOR3': '~(a|b|c)',
        'NOR4': '~(a|b|c|d)',
        'XNOR2': '~(a^b)',
        'XNOR3': '~(a^b^c)',
        'XNOR4': '~(a^b^c^d)',
        'AOI21': '~((a&b)|c)',
        'AOI22': '~((a&b)|(c&d))',
        'OAI21': '~((a|b)&c)',
        'OAI22': '~((a|b)&(c|d))',
        'SEL2': '(a&(~s))|(b&s)',
    }
    document = ""
    for name, expr in expressions.items():
        func = Function(expr)
        document += func.to_yaml(name) + "\n"
    print(document)
