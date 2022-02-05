
import sys
import ply.lex as lex

# ---------------Lexing------------------
# t_KEYWORD = r'skip|while|do|if|then|else|read|write|for|to'
keywords = { 'skip' : 'SKIP',
            'while' : 'WHILE',
            'do' : 'DO',
            'if' : 'IF',
            'then' : 'THEN',
            'else' : 'ELSE',
            'read' : 'READ',
            'write': 'WRITE',
            'for' : 'FOR',
            'to' : 'TO'}
t_BKEYWORD = r'true|false' # Boolean keywords
# t_OPERATOR = r'\+|-|\*|%|/|==|!=|>|<|<=|>=|:=|&&|\|\|'
t_AOPERATOR = r'\+|-|\*|%|/' # Arithmetic operators
t_BOPERATOR = r'==|!=|>|<|<=|>=|&&|\|\|' # Boolean operators
t_ASSOPERATOR = r':=' # Assign
operators = ['AOPERATOR', 'BOPERATOR', 'ASSOPERATOR']
# t_LETTER = r'[a-zA-Z]'
# t_SYMBOL = r'[a-zA-Z._><=;,\\:]'
def t_WHITESPACE(t):
    r'[ \n\t\r]+'
    pass
# t_DIGIT = r'[0-9]'
def t_NUMBER(t):
    r'[0-9]|[1-9][0-9]+'
    t.value = int(t.value)
    return t
t_STRING = r'\"[a-zA-Z._><=;,\\: \n\t\r0-9]*\"'
t_SEMICOLON = r';'
# t_PARENTHESIS = r'{|}|\(|\)'
t_LBRACE = r'{'
t_RBRACE = r'}'
t_LPAREN = r'\('
t_RPAREN = r'\)'
parens = ['LBRACE', 'RBRACE', 'LPAREN', 'RPAREN']
def t_IDENTIFIER(t):
    r'[a-zA-Z][_a-zA-Z0-9]*'
    t.type = keywords.get(t.value,'IDENTIFIER')    # Check for reserved words
    return t
def t_COMMENT(t):
    r'//[a-zA-Z._><=;,\\: \n\t\r0-9]*\n'
    pass

tokens = ['BKEYWORD', 'IDENTIFIER', 'NUMBER', 'SEMICOLON', 'STRING',  'WHITESPACE', 'COMMENT'] + list(keywords.values()) + parens + operators

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lex.lex(debug=False)

# # customize tokens
# def tokenize(filename):
#     lexer = lex.lex()
#     file = open(filename)
#     data = file.read()
#     file.close()
#     lexer.input(data)
#     tokens = []
#     while True:
#         tok = lexer.token()
#         if not tok: 
#             break      # No more input
#         tokens = tokens + [(tok.type, tok.value)]
#     return tokens


# Test the lexer file independently. eg: python3 lexer.py test/collatz.while 
if __name__ == '__main__':
    print(tokens)
    lexer = lex.lex()
    filename = sys.argv[1]
    file = open(filename)
    data = file.read()
    file.close()
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok: 
            break      # No more input
        print(tok.type, tok.value, tok.lineno, tok.lexpos)
 