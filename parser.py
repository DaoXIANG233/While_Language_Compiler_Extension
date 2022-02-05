import lexer
import ply.yacc as yacc
import sys

tokens = lexer.tokens

def p_id(p):
    '''variable : IDENTIFIER'''
    p[0] = ('Var', p[1])

def p_num(p):
    '''number : NUMBER'''
    p[0] = ('Num', p[1])

def p_str(p):
    '''string : STRING'''
    p[0] = ('Str', p[1])


def p_aexp(p):
    '''aexp : te AOPERATOR aexp'''
    if p[2] == '+' or p[2] == '-':
        p[0] = ('aexp', p[2], p[1], p[3])
def p_aexp_te(p):
    '''aexp : te'''
    p[0] = p[1]
def p_te(p):
    '''te : fa AOPERATOR te'''
    if p[2] == '*' or p[2] == '/' or p[2] == '%':
        p[0] = ('aexp', p[2], p[1], p[3])
def p_te_fa(p):
    '''te : fa'''
    p[0] = p[1]
def p_fa(p):
    '''fa : LPAREN aexp RPAREN'''
    p[0] = p[2]
def p_fa_basic(p):
    '''fa : variable
          | number'''
    p[0] = p[1]


def p_bexp(p):
    '''bexp : aexp BOPERATOR aexp'''
    if p[2] in ['==', '!=', '>', '<', '>=', '<=']:
        p[0] = ('bexp', p[2], p[1], p[3])
def p_bexp_nested(p):
    '''bexp : bexp BOPERATOR bexp'''
    if p[2] in ['&&', '||']:
        p[0] = ('bexp', p[2], p[1], p[3])
def p_bexp_basic(p):
    '''bexp : BKEYWORD'''
    p[0] = p[1]
def p_bexp_paren(p):
    '''bexp : LPAREN bexp RPAREN'''
    p[0] = p[2]

def p_statement_basic(p):
    '''stmt : stmt SEMICOLON'''
    p[0] = p[1]
def p_statement_skip(p):
    '''stmt : SKIP'''
    p[0] = p[1]
def p_statement_assign(p):
    '''stmt : variable ASSOPERATOR aexp'''
    p[0] = ('assign', p[1], p[3])
def p_statement_write_id(p):
    '''stmt : WRITE variable
            | WRITE LPAREN variable RPAREN'''
    if len(p) == 3:
        p[0] = ('writeId', p[2])
    else:
        p[0] = ('writeId', p[3])
def p_statement_write_str(p):
    '''stmt : WRITE string
            | WRITE number
            | WRITE LPAREN string RPAREN
            | WRITE LPAREN number RPAREN'''
    if len(p) == 3:
        p[0] = ('writeStr', p[2])
    else:
        p[0] = ('writeStr', p[3])
def p_statement_if(p):
    '''stmt : IF bexp THEN block ELSE block'''
    p[0] = ('if', p[2], p[4], p[6])
def p_statement_while(p):
    '''stmt : WHILE bexp DO block'''
    p[0] = ('while', p[2], p[4])
def p_statement_read(p):
    '''stmt : READ variable
            | READ LPAREN variable RPAREN'''
    if len(p) == 3:
        p[0] = ('read', p[2])
    else:
        p[0] = ('read', p[3])

def p_statements(p):
    '''stmts : stmt SEMICOLON stmts'''
    p[0] = [p[1]] + p[3]
def p_statements_lst(p):
    '''stmts : stmt'''
    p[0] = [p[1]]

def p_block(p):
    '''block : LBRACE stmts RBRACE'''
    p[0] = p[2]

def p_error(p):
    if not p:
        print("SYNTAX ERROR AT EOF")

whileParser = yacc.yacc(start='stmts')


def parse(data, debug=0):
    whileParser.error = 0
    p = whileParser.parse(data, debug=debug)
    if whileParser.error:
        return None
    return p


# Test the parser (depends on lexer). eg: python3 parser.py test/test.while 
if __name__ == '__main__':
    filename = sys.argv[1]
    file = open(filename)
    data = file.read()
    print("'While' language file:")
    print(data)
    file.close()
    print("AST generated:")
    p = parse(data)
    print(p)
