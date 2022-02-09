import parser
import sys
from nis import match

counter = -1

def Fresh(x):
    global counter
    counter += 1
    return x + "_" + str(counter)

varEnv = {}

def CPS(stmt, f):
    match stmt[0]:
        case "Var":
            ty = varEnv.get(stmt[1], "undef")
            return f(("kvar", stmt[1], ty))
        case "Num":
            return f(("knum", stmt[1]))
        case "Str":
            return f(("kstr", stmt[1]))
        case "Bool":
            return f(("kbool", stmt[1]))
        case "aexp":
            z = Fresh("tmp")
            return CPS(stmt[2], lambda y1 : CPS(stmt[3], lambda y2 : ("klet", z, ("kop", stmt[1], y1, y2), f(("kvar", z)))))
        case "bexp":
            z = Fresh("tmp")
            return CPS(stmt[2], lambda y1 : CPS(stmt[3], lambda y2 : ("klet", z, ("kop", stmt[1], y1, y2), f(("kbool", z)))))
        case "call":
            def aux(args, vs):
                if (0 == len(args)):
                    return f(("kcall", stmt[1], vs))
                else:
                    return CPS(args[0], lambda y : aux(args[1:], vs + [y]))
            return aux(stmt[2], [])
        # case "while":
        #     a
        case "if":
            bExp = stmt[1]
            blIf = stmt[2]
            blEl = stmt[3]
            z = Fresh("tmp")
            return CPS(bExp[2], lambda y1 : CPS(bExp[3], lambda y2 : ("klet", z, ("kop", bExp[1], y1, y2), ("kif", z, CPSB(blIf, f), CPSB(blEl, f)))))
        case _:
            return ("unknown")




def CPSB(bl, f):
    if (1 == len(bl)):
        return CPS(bl[0], f)
    else : 
        any = Fresh("any")
        return CPS(bl[0], lambda v : ("klet", any, v, CPSB(bl[1:], f)))

bl1 = [('call', 'write', [('Str', '"Input a number "')]), ('call', 'read', [('Var', 'n')]), ('call', 'write', [('Str', '"Yes"')])]
print(CPSB(bl1, lambda x : ("kreturn", x)))

bl2 = [('bexp', '==', ('Num', 2), ('Num', 3)), ('bexp', '||', ('Bool', 'true'), ('Bool', 'false')), ('bexp', '!=', ('Num', 2), ('Num', 1))]
print(CPSB(bl2, lambda x : ("kreturn", x)))

prelude = """

declare i32 @printf(i8*, ...)

@.str = private constant [4 x i8] c"%d\\0A\\00"
@.char = private constant [3 x i8] c"%c\\00"

@.str_nl = private constant [2 x i8] c"\\0A\\00"
@.str_star = private constant [2 x i8] c"*\\00"
@.str_space = private constant [2 x i8] c" \\00"

define void @new_line() #0 {
  %t0 = getelementptr [2 x i8], [2 x i8]* @.str_nl, i32 0, i32 0
  %1 = call i32 (i8*, ...) @printf(i8* %t0)
  ret void
}

define void @print_star() #0 {
  %t0 = getelementptr [2 x i8], [2 x i8]* @.str_star, i32 0, i32 0
  %1 = call i32 (i8*, ...) @printf(i8* %t0)
  ret void
}

define void @print_space() #0 {
  %t0 = getelementptr [2 x i8], [2 x i8]* @.str_space, i32 0, i32 0
  %1 = call i32 (i8*, ...) @printf(i8* %t0)
  ret void
}

define void @skip() #0 {
  ret void
}

define i32 @printInt(i32 %x) {
   %t0 = getelementptr [4 x i8], [4 x i8]* @.str, i32 0, i32 0
   call i32 (i8*, ...) @printf(i8* %t0, i32 %x) 
   ret i32 %x
}

define void @printChar(i32 %x) {
   %t0 = getelementptr [3 x i8], [3 x i8]* @.char, i32 0, i32 0
   call i32 (i8*, ...) @printf(i8* %t0, i32 %x) 
   ret void
}

"""

if __name__ == '__main__':
    filename = sys.argv[1]
    file = open(filename)
    data = file.read()
    print("'While' language file:")
    print(data)
    file.close()
    print("AST generated:")
    p = parser.parse(data)
    print(p)
