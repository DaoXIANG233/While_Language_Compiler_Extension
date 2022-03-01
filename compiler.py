import parser
import sys

counter = -1

def Fresh(x):
    global counter
    counter += 1
    return x + "_" + str(counter)

def formatBexp(x):
    match x[0]:
        case "bexp":
            if x[1] in ['&&', '||']:
                left = formatBexp(x[2])
                right = formatBexp(x[3])
                return ("fbexp", x[1], left, right)
            else:
                return ("fbexp", x[1], x[2], x[3])
        case "aexp":
            return ("fbexp", ">", x, ("Num", 0))
        case "Var":
            return ("fbexp", ">", x, ("Num", 0))
        case "Num":
            return ("fbexp", ">", x, ("Num", 0))
        case "FNum":
            return ("fbexp", ">", x, ("Num", 0))
        # case "Bool":
        #     if 'true' == x[1]:
        #         return ("fbexp", ">", ("Num", 1), ("Num", 0))
        #     elif 'false' == x[1]:
        #         return ("fbexp", ">", ("Num", 0), ("Num", 0))
        #     else:
        #         return x
        case _:
            return x

varEnv = {}

def CPS(stmt, f):
    match stmt[0]:
        case "Var":
            ty = varEnv.get(stmt[1], "undef")
            return f(("kvar", stmt[1], ty))
        case "Num":
            return f(("knum", stmt[1], "int"))
        case "FNum":
            return f(("knum", stmt[1], "float"))
        case "Str":
            return f(("kstr", stmt[1]))
        case "Neg":
            if stmt[1][0] in ["Num", "FNum"]:
                return CPS(stmt[1], lambda y : f(('kneg', y)))
            else:
                return CPS(("aexp", "-", ("Num", 0), stmt[1]), f)
        case "aexp":
            z = Fresh("tmp")
            return CPS(stmt[2], lambda y1 : CPS(stmt[3], lambda y2 : ("klet", z, ("kop", stmt[1], y1, y2), f(("kvar", z)))))
        case "bexp":
            stmt = formatBexp(stmt)
            z = Fresh("tmp")
            return CPS(stmt[2], lambda y1 : CPS(stmt[3], lambda y2 : ("klet", z, ("kop", stmt[1], y1, y2), f(("kvar", z)))))
        case "fbexp":
            z = Fresh("tmp")
            return CPS(stmt[2], lambda y1 : CPS(stmt[3], lambda y2 : ("klet", z, ("kop", stmt[1], y1, y2), f(("kvar", z)))))
        case "call":
            def aux(args, vs):
                if (0 == len(args)):
                    return f(("kcall", stmt[1], vs))
                else:
                    return CPS(args[0], lambda y : aux(args[1:], vs + [y]))
            return aux(stmt[2], [])
        # TODO: assign
        # case "assign":
        #     if stmt[1][0] != "Var":
        #         raise Exception("assigning error")
        #     return CPS(stmt[2], lambda y : ("kass", stmt[1], y))
        # TODO: case "while":  
        case "if":
            bExp = formatBexp(stmt[1])
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

# bl2 = [('bexp', '==', ('Num', 2), ('Num', 3)), ('bexp', '||', ('Bool', 'true'), ('Bool', 'false')), ('bexp', '!=', ('Num', 2), ('Num', 1))]
# print(CPSB(bl2, lambda x : ("kreturn", x)))

# bl3 = [('bexp', '&&', ('Bool', 'true'), ('Var', 'n'))]
# print(CPSB(bl3, lambda x : ("kreturn", x)))

# bl4 = [('if', ('Bool', 'true'), [('assign', ('Var', 'n'), ('aexp', '/', ('Var', 'n'), ('Num', 2)))], [('assign', ('Var', 'n'), ('aexp', '+', ('aexp', '*', ('Num', 3), ('Var', 'n')), ('Num', 1)))])]
# print(CPSB(bl4, lambda x : ("kreturn", x)))

# bl5 = [('if', ('bexp', '&&', ('Bool', 'true'), ('bexp', '||', ('Num', 1), ('Var', 'n'))), [('assign', ('Var', 'n'), ('aexp', '/', ('Var', 'n'), ('Num', 2)))], [('assign', ('Var', 'n'), ('aexp', '+', ('aexp', '*', ('Num', 3), ('Var', 'n')), ('Num', 1)))])]
# print(CPSB(bl5, lambda x : ("kreturn", x)))


# String interpolations
def i(str):
    return "    " + str + "\n"
def l(str):
    return str + ":\n"
def m(str):
    return str + "\n"

def compile_op(op):
    match op:
        case "+":
            return "add i32 "
        case "*":
            return "mul i32 "
        case "-":
            return "sub i32 "
        case "/":
            return "sdiv i32 "
        case "%":
            return "srem i32 "
        case "==":
            return "icmp eq i32 "
        case "!=":
            return "icmp ne i32 "
        case "<=":
            return "icmp sle i32 "
        case "<":
            return "icmp slt i32 "
        case ">=":
            return "icmp sge i32 "
        case ">":
            return "icmp sgt i32 "
        case "&&":
            return "and i1"
        case "||":
            return "or i1"

def compile_fop(op):
    match op:
        case "+":
            return "fadd double "
        case "*":
            return "fmul double "
        case "-":
            return "fsub double "
        case "/":
            return "fdiv double "
        case "%":
            return "frem double "
        case "==":
            return "fcmp oeq double "
        case "!=":
            return "fcmp one double "
        case "<=":
            return "fcmp ole double "
        case "<":
            return "fcmp olt double " 
        case ">=":
            return "fcmp oge double "
        case ">":
            return "fcmp ogt double " 
        case "&&":
            return "and i1"
        case "||":
            return "or i1"

def compile_val(v):
    match v[0]:
        case "knum":
            return f"{v[1]}"
        case "kvar":
            return f"%{v[1]}"
        case "kneg":
            return f"-{compile_val(v[1])}"
        case "kop":
            return f"{compile_op(v[1])} {compile_val(v[2])}, {compile_val(v[3])}"
        # case "kcall":
        case _:
            return "unknown kval"

# def compile_val(v: KVal) : String = v match {
#   case KNum(i) => s"$i"
#   case KDNum(d) => s"$d"
#   case KNeg(x) => s"-${compile_val(x)}"
#   case KVar(s, ty) => s"%$s"
#   case Kop(op, x1, x2, ty) => {
#       if (ty == "double") {
#         s"${compile_dop(op)} ${compile_val(x1)}, ${compile_val(x2)}"
#       } else {
#         s"${compile_op(op)} ${compile_val(x1)}, ${compile_val(x2)}"
#       }
      
#     }
#   case KCall(x1, args) => 
#     val funType = globalFuns.getOrElse(x1, (List(), "void"))
#     if (funType._2 == "void"){
#       i"call void @$x1 (${funType._1.zip(args.map(compile_val)).map(t => t._1 ++ " " ++ t._2).mkString(", ")})"
#     } else {
#       s"call ${funType._2} @$x1 (${funType._1.zip(args.map(compile_val)).map(t => t._1 ++ " " ++ t._2).mkString(", ")})"
#     }
# }

def compile_exp(e):
    match e[0]:
        case "kreturn":
            return i("ret void")
        case "klet":
            return i(f"%{e[1]} = {compile_val(e[2])}") + compile_exp(e[3])
        case "kif":
            ifBr = Fresh("if_branch")
            elseBr = Fresh("else_branch")
            return i(f"br i1 %{e[1]}, label %{ifBr}, label %{elseBr}") + l(f"\n{ifBr}") + compile_exp(e[2]) + l(f"\n{elseBr}") + compile_exp(e[3])


# // compile K expressions
# def compile_exp(a: KExp) : String = a match {
#   case KReturn(v) =>{
#       val kValTup1 = compile_env(v)
#       if (kValTup1._3 == "void") {
#         kValTup1._1 ++
#         compile_val(kValTup1._2) ++
#         i"ret void"
#       } else v match {
#         case KCall(name, args) => {
#           val z = Fresh("tmp")
#           compile_exp(KLet(z, KCall(name, args), KReturn(KVar(z))))
#         }
#         case _ => kValTup1._1 ++ i"ret ${kValTup1._3} ${compile_val(kValTup1._2)}"
#       }
#     }
#   case KLet(x: String, v: KVal, e: KExp) => {
#       val kValTup1 = compile_env(v)
#       varEnv += (x -> kValTup1._3)
#       if (kValTup1._3 == "void") {
#         kValTup1._1 ++
#         compile_val(kValTup1._2) ++ 
#         compile_exp(e)
#       } else {
#         kValTup1._1 ++
#         i"%$x = ${compile_val(kValTup1._2)}" ++ compile_exp(e)
#       }
#     }
#   case KIf(x, bl1, bl2) => {
#     val if_br = Fresh("if_branch")
#     val else_br = Fresh("else_branch")
#     i"br i1 %$x, label %$if_br, label %$else_br" ++
#     l"\n$if_br" ++
#     compile_exp(bl1) ++
#     l"\n$else_br" ++ 
#     compile_exp(bl2)
#   }
# }

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

preludeMain = "define i32 @main() {"

def compileDecl(d):
    match d[0]:
        case "dAssign":
            return d
        case "dDef":
            return d
        case "dMain":
            s = m("define i32 @main() {") + compile_exp(CPSB(d[1], lambda x : ("kreturn", ("knum", 0, "int")))) + m("}\n")
            return s

# def compile_decl(d: Decl) : String = d match {
#   case Assign(name, ty, value) => {
#     globalVals += (name -> type_change(ty))
#     varEnv += (name -> type_change(ty))
#     m"@$name = global ${type_change(ty)} ${compile_val(KTrans(value))} \n"
#   }
#   case Def(name, args, ret, body) => {
#     globalFuns += (name -> (args.map(d => type_change(d.t)), type_change(ret)))
#     args.map(d => (d.s -> type_change(d.t))).foreach(e => varEnv += e)
#     m"define ${type_change(ret)} @$name (${args.map(d => s"${type_change(d.t)} %${d.s}").mkString(", ")}) {" ++
#     compile_exp(CPSB(body)(KReturn)) ++
#     m"}\n"
#   }
#   case Main(body) => {
#     m"define i32 @main() {" ++
#     compile_exp(CPSB(body)(v => KLet("last", v, KReturn(KNum(0))))) ++
#     m"}\n"
#   }
# }

def compile(ast):
    prog = [("dMain", ast)]
    progll = '\n'.join(list(map(compileDecl, prog)))
    # return prelude + "\n" + progll
    return progll

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
    print("CPSB:")
    print(CPSB(p, lambda x : ("kreturn", ("knum", 0, "int"))))
    ll = compile(p)
    print(ll)
