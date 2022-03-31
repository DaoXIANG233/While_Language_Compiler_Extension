import lexer
import ply.yacc as yacc
import sys

tokens = lexer.tokens

def esc(file):
    return file.replace("\\\\", "\\5C").replace("\\\"", "\\22").replace("\\n", "\\0A").replace("\\t", "\\09")

def p_id(p):
    '''variable : IDENTIFIER'''
    p[0] = ('Var', p[1])

def p_num(p):
    '''number : NUMBER'''
    p[0] = ('Num', p[1])

def p_fnum(p):
    '''number : FNUMBER'''
    p[0] = ('FNum', p[1])

def p_bnum(p):
    '''number : bool'''
    p[0] = p[1]

def p_str(p):
    '''string : STRING'''
    p[0] = ('Str', p[1][1:-1])

def p_bool(p):
    '''bool : BKEYWORD'''
    if p[1] == "true":
        p[0] = ("Num", 1)
    else:
        p[0] = ("Num", 0)

def p_lst(p):
    '''list : lstel lstconnect list
            | lstel'''
    if (4 == len(p)):
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]
def p_lst_lstel(p):
    '''lstel : aexp
             | bool
             | string
             | array'''
    p[0] = p[1]
def p_lst_lstconnect(p):
    '''lstconnect : COMMA'''
    p[0] = p[1]

def p_array(p):
    '''array : LBRACKET list RBRACKET'''
    p[0] = ('array', p[2])

def p_aexp(p):
    '''aexp : aexp PLUS te
            | aexp MINUS te'''
    p[0] = ('aexp', p[2], p[1], p[3])
def p_aexp_te(p):
    '''aexp : te'''
    p[0] = p[1]
def p_te(p):
    '''te : te TIMES fa
          | te DIVIDE fa
          | te REMAIN fa'''
    p[0] = ('aexp', p[2], p[1], p[3])
def p_te_fa(p):
    '''te : fa'''
    p[0] = p[1]
def p_fa(p):
    '''fa : LPAREN aexp RPAREN'''
    p[0] = p[2]
def p_fa_basic(p):
    '''fa : variable
          | number
          | call'''
    p[0] = p[1]
def p_fa_basic_neg(p):
    '''fa : MINUS fa'''
    p[0] = ('Neg', p[2])


def p_bexp(p):
    '''bexp : bexp LBOPERATOR bc'''
    p[0] = ('bexp', p[2], p[1], p[3])
def p_bexp_bc(p):
    '''bexp : bc'''
    p[0] = p[1]
def p_bc(p):
    '''bc : bn BCOPERATOR bn'''
    p[0] = ('bexp', p[2], p[1], p[3])
def p_bc_ab(p):
    '''bc : bn'''
    p[0] = p[1]
def p_bn(p):
    '''bn : BNOPERATOR ab'''
    p[0] = ('not', p[2])
def p_bn_bc(p):
    '''bn : ab'''
    p[0] = p[1]
def p_ab(p):
    '''ab : aexp ABOPERATOR aexp'''
    p[0] = ('bexp', p[2], p[1], p[3])
def p_ab_aexp(p):
    '''ab : aexp
          | bool'''
    p[0] = p[1]
def p_ab_paren(p):
    '''ab : LPAREN bexp RPAREN'''
    p[0] = p[2]

def p_lambda(p):
    '''lambda : list LAMBDAOPERATOR block'''
    p[0] = ('lambda', p[1], p[3], None)
    
# def p_bexp_paren(p):
#     '''bexp : LPAREN bexp RPAREN'''
#     p[0] = p[2]
# def p_bexp_ab(p):
#     '''bexp : ab
#             | bc
#             | bool'''
#     p[0] = p[1]
# def p_ab(p):
#     '''ab : aexp ABOPERATOR aexp'''
#     p[0] = ('bexp', p[2], p[1], p[3])
# def p_bc(p):
#     '''bc : aexp BCOPERATOR aexp
#           | bool BCOPERATOR aexp
#           | aexp BCOPERATOR bool'''
#     p[0] = ('bexp', p[2], p[1], p[3])


# def p_ab_paren(p):
#     '''ab : LPAREN ab RPAREN'''
#     p[0] = p[2]
# def p_ab_basic(p):
#     '''ab : bool'''
#     p[0] = p[1]


# def p_bexp(p):
# def p_bexp_nested(p):
#     '''bexp : bexp LBOPERATOR bexp'''
#     p[0] = ('bexp', p[2], p[1], p[3])
# def p_bexp_basic(p):
#     '''bexp : bool'''
#     p[0] = p[1]
# def p_bexp_paren(p):
#     '''bexp : LPAREN bexp RPAREN'''
#     p[0] = p[2]

def p_statement_basic(p):
    '''stmt : stmt SEMICOLON'''
    p[0] = p[1]
def p_statement_skip(p):
    '''stmt : SKIP'''
    p[0] = ('skip', None)

def p_statement_assign_values(p):
    '''value : aexp
             | bexp
             | string
             | array'''
    p[0] = p[1]
def p_statement_assign(p):
    '''stmt : variable ASSOPERATOR value'''
    p[0] = ('assign', p[1], p[3])

def p_call(p):
    '''call : IDENTIFIER LPAREN list RPAREN
            | IDENTIFIER LPAREN RPAREN'''
    if (5 == len(p)):
        p[0] = ('call', p[1], p[3])
    else:
        p[0] = ('call', p[1], [])
def p_statement_call(p):
    '''stmt : call'''
    p[0] = p[1]
def p_statement_value(p):
    '''stmt : value'''
    p[0] = p[1]

def p_statement_write(p):
    '''stmt : WRITE aexp
            | WRITE string
            | WRITE LPAREN aexp RPAREN
            | WRITE LPAREN string RPAREN'''
    if len(p) == 3:
        p[0] = ('write', p[2])
    else:
        p[0] = ('write', p[3])

def p_statement_writeln(p):
    '''stmt : WRITELN aexp
            | WRITELN string
            | WRITELN LPAREN aexp RPAREN
            | WRITELN LPAREN string RPAREN'''
    if len(p) == 3:
        p[0] = ('writeln', p[2])
    else:
        p[0] = ('writeln', p[3])

def p_statement_if(p):
    '''stmt : IF bexp THEN block ELSE block'''
    p[0] = ('if', p[2], p[4], p[6])
def p_statement_while(p):
    '''stmt : WHILE bexp DO block'''
    p[0] = ('while', p[2], p[4])

def p_statement_read(p):
    '''stmt : READ list
            | READ LPAREN list RPAREN'''
    if len(p) == 3:
        p[0] = ('read', p[2])
    else:
        p[0] = ('read', p[3])
        
def p_statement_import(p):
    '''stmt : IMPORT IDENTIFIER'''
    p[0] = ('import', p[2])
def p_statement_gassign(p):
    '''stmt : GLOBAL variable ASSOPERATOR number'''
    p[0] = ('gassign', p[2], p[4])

def p_statement_then(p):
    '''stmt : block DOT THEN LPAREN lambda RPAREN'''
    p[0] = ('then', p[1], p[5])
def p_statement_then_import(p):
    '''stmt : block DOT THEN LPAREN IDENTIFIER RPAREN'''
    p[0] = ('then', p[1], [('call', p[5], [])])

def p_statements(p):
    '''stmts : stmt SEMICOLON stmts'''
    p[0] = [p[1]] + p[3]
def p_statements_lst(p):
    '''stmts : stmt'''
    p[0] = [p[1]]

def p_block(p):
    '''block : LBRACE stmts RBRACE'''
    p[0] = p[2]
def p_block_single(p):
    '''block : stmt'''
    p[0] = [p[1]]

def p_error(p):
    if not p:
        raise Exception(f"SYNTAX ERROR AT EOF")
    raise Exception(f"SYNTAX ERROR AT: {p}")

whileParser = yacc.yacc(start='stmts')


def parse(data, debug=0):
    data = esc(data)
    whileParser.error = 0
    p = whileParser.parse(data, debug=debug)
    if whileParser.error:
        raise Exception("SYNTAX ERROR")
    return p


# Test the parser (depends on lexer). eg: python3 parser.py test/test.while 
if __name__ == '__main__':
    filename = sys.argv[1]
    file = open(filename)
    data = file.read()
    print("'While' language file:")
    print(data)
    file.close()
    data = esc(data)
    print("AST generated:")
    p = parse(data)
    print(p)
