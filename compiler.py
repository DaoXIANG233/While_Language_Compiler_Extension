import parser
import sys

counter = -1

def Fresh(x):
    global counter
    counter += 1
    return x + "_" + str(counter)

def format_bexp(x):
    match x[0]:
        case "bexp":
            if x[1] in ['&&', '||']:
                left = format_bexp(x[2])
                right = format_bexp(x[3])
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
        case _:
            return x

# def format_aexp(x):
#     match x[0]:
#         # case "bexp":
#         #     if x[1] in ['&&', '||']:
#         #         left = format_aexp(x[2])
#         #         right = format_aexp(x[3])
#         #         return ("fbexp", x[1], left, right)
#         #     else:
#         #         return ("faexp", x[1], x[2], x[3])
#         case "aexp":
#             return ("faexp", x[1], x[2], x[3])
#         case "Neg":
#             if x[1][0] in ["Num", "FNum"]:
#                 return CPS(x[1], lambda y : f(('kneg', y)))
#             else:
#                 return ("faexp", "-", ("Num", 0), x[1])
#         case "Var":
#             return ("faexp", "+", x, ("Num", 0))
#         case "Num":
#             return ("faexp", "+", x, ("Num", 0))
#         case "FNum":
#             return ("faexp", "+", x, ("Num", 0))
#         case _:
#             return x

def get_type(e):
    match e[0]:
        case "knum":
            return e[2]
        case "kvar":
            return e[2]
        case "kneg":
            return get_type(e[1])
        case "kop":
            ty1 = get_type(e[2])
            ty2 = get_type(e[3])
            if ty1 == "double" or ty2 == "double":
                return "double"
            else:
                return "i32"
        case "kload":
            return get_type(e[1])
        case _:
            return "i32"

varEnv = {}
alloca = []

def CPS(stmt, f):
    match stmt[0]:
        case "Var":
            ty = varEnv.get(stmt[1], "undef")
            return f(("kvar", stmt[1], ty))
        case "Num":
            return f(("knum", stmt[1], "i32"))
        case "FNum":
            return f(("knum", stmt[1], "double"))
        case "Str":
            return f(("kstr", stmt[1]))
        case "Neg":
            if stmt[1][0] in ["Num", "FNum"]:
                return CPS(stmt[1], lambda y : f(('kneg', y)))
            else:
                return CPS(("aexp", "-", ("Num", 0), stmt[1]), f)
        case "aexp":
            z = Fresh("tmp")
            return CPS(stmt[2], lambda y1 : CPS(stmt[3], lambda y2 : ("klet", z, ("kop", stmt[1], y1, y2), f(("kvar", z, get_type(("kop", stmt[1], y1, y2)))))))
        case "bexp":
            stmt = format_bexp(stmt)
            z = Fresh("tmp")
            return CPS(stmt[2], lambda y1 : CPS(stmt[3], lambda y2 : ("klet", z, ("kop", stmt[1], y1, y2), f(("kvar", z, get_type(("kop", stmt[1], y1, y2)))))))
        case "fbexp":
            z = Fresh("tmp")
            return CPS(stmt[2], lambda y1 : CPS(stmt[3], lambda y2 : ("klet", z, ("kop", stmt[1], y1, y2), f(("kvar", z, get_type(("kop", stmt[1], y1, y2)))))))
        case "call":
            def aux(args, vs):
                if (0 == len(args)):
                    return f(("kcall", stmt[1], vs))
                else:
                    return CPS(args[0], lambda y : aux(args[1:], vs + [y]))
            return aux(stmt[2], [])
        case "assign":
            if stmt[1][0] != "Var":
                raise Exception("assigning error")
            else:
                def kassign(a, b):
                    ty = get_type(b)
                    varEnv[a[1]] = ty
                    v = (a[0], a[1], ty)
                    return ("kass", v, b, f(v))
                
                if (varEnv.get(stmt[1][1]) != None) and (stmt[1][1] not in alloca):
                    alloca.append(stmt[1][1])

                return CPS(stmt[1], lambda y1 : CPS(stmt[2], lambda y2 : kassign(y1, y2)))

        case "while":
            reg = ("knone", None)
            def registerLast(x):
                nonlocal reg
                reg = x
                return ("knone", None)
            cond = format_bexp(stmt[1])
            bl = stmt[2]
            entryWhile = Fresh("while_loop")
            condWhile = Fresh("while_cond")
            bodyWhile = Fresh("while_body")
            endWhile = Fresh("while_end")
            z = Fresh("tmp")
            return CPS(cond[2], lambda y1 : CPS(cond[3], lambda y2 : ("kwhile", z, ( "klet", z, ("kop", cond[1], y1, y2), ("knone", None)), CPSB(bl, lambda x : registerLast(x)), f(reg), (entryWhile, condWhile, bodyWhile, endWhile))))

        case "if":
            ifReg = ("knone", None)
            elseReg = ("knone", None)
            def registerIf(x):
                nonlocal ifReg
                ifRet = Fresh("ifRet")
                ifReg = ("kvar", ifRet, get_type(x))
                return ("kass", ifReg, x, ("knone", None))
            def registerElse(x):
                nonlocal elseReg
                elseRet = Fresh("elseRet")
                elseReg = ("kvar", elseRet, get_type(x))
                return ("kass", elseReg, x, ("knone", None))

            bExp = format_bexp(stmt[1])
            blIf = stmt[2]
            blEl = stmt[3]
            z = Fresh("tmp")
            phi = Fresh("tmp")
            ifLabel = Fresh("if_branch")
            elseLabel = Fresh("else_branch")
            endLabel = Fresh("if_end")
            return CPS(bExp[2], lambda y1 : CPS(bExp[3], lambda y2 : ("klet", z, ("kop", bExp[1], y1, y2), ("kif", z, CPSB(blIf, lambda x1 : registerIf(x1)), CPSB(blEl, lambda x2 : registerElse(x2)), ("klet", phi, ("kphi", (ifReg, ifLabel), (elseReg, elseLabel), get_type(ifReg)), f(("kvar", phi, get_type(ifReg)))), (ifLabel, elseLabel, endLabel)))))
        case _:
            return ("unknown")


def CPSB(bl, f):
    if (1 == len(bl)):
        return CPS(bl[0], f)
    else:
        # any = Fresh("any")
        # return CPS(bl[0], lambda v : ("klet", any, v, CPSB(bl[1:], f)))
        return CPS(bl[0], lambda v : CPSB(bl[1:], f))

# bl1 = [('call', 'write', [('Str', '"Input a number "')]), ('call', 'read', [('Var', 'n')]), ('call', 'write', [('Str', '"Yes"')])]
# print(CPSB(bl1, lambda x : ("kreturn", x)))

# bl2 = [('assign', ('Var', 'n'), ('Num', 1))]
# print(CPSB(bl2, lambda x : ("kreturn", x)))

# bl3 = [('assign', ('Var', 'n'), ('FNum', 1.0))]
# print(CPSB(bl3, lambda x : ("kreturn", x)))

# bl4 = [('assign', ('Var', 'n'), ('aexp', '/', ('Var', 'n'), ('Num', 2)))]
# print(CPSB(bl4, lambda x : ("kreturn", x)))

# bl5 = [('assign', ('Var', 'n'), ('bexp', '&&', ('Var', 'n'), ('FNum', 2.0)))]
# print(CPSB(bl5, lambda x : ("kreturn", x)))

#TODO: format ast to include lambda, global variables, imports.
# def format_ast(ast):
#     def extract_lambda():
#         return

kExps = ["klet", "kreturn", "kass", "kif", "kload", "kwhile", "knone"]
kVals = ["knum", "kvar", "kneg", "kop", "kphi"]

def format_klang(k):
    def load_var(e):
        def extract_vars(kval, vars = []):
            match kval[0]:
                case "knum":
                    return (vars, kval)
                case "kvar":
                    if kval[1] in alloca:
                        tmp = Fresh("tmp")
                        return (vars + [(kval, tmp)], ("kvar", tmp, kval[2]))
                    else:
                        return (vars, kval)
                case "kneg":
                    return extract_vars(kval[1], vars)
                case "kop":
                    left = extract_vars(kval[2], vars)
                    right = extract_vars(kval[3], vars)
                    return  (left[0]+right[0], ("kop", kval[1], left[1], right[1])) 
                case "kphi":
                    br1 = extract_vars(kval[1][0], vars)
                    br2 = extract_vars(kval[2][0], vars)
                    return (br1[0]+br2[0], ("kphi", (br1[1], kval[1][1]), (br2[1], kval[2][1]), kval[3]))
                    # return (vars, kval)
                case _:
                    return (vars, kval)
        match e[0]:
            case "klet":
                (vars, newKval) = extract_vars(e[2])
                rest = load_var(e[3])
                e = ("klet", e[1], newKval, rest)
                for i in vars:
                    e = ("kload", i[1], i[0], e)
                return e
            case "kreturn":
                (vars, newKval) = extract_vars(e[1])
                e = ("kreturn", newKval)
                for i in vars:
                    e = ("kload", i[1], i[0], e)
                return e
            case "kass":
                (vars, newKval) = extract_vars(e[2])
                rest = load_var(e[3])
                e = ("kass", e[1], newKval, rest)
                for i in vars:
                    e = ("kload", i[1], i[0], e)
                return e
            case "kif":
                return ("kif", e[1], load_var(e[2]), load_var(e[3]), load_var(e[4]), e[5])
            case "kload":
                return(e[0], e[1], e[2], load_var(e[3]))
            case "kwhile":
                cond = load_var(e[2])
                body = load_var(e[3])
                rest = load_var(e[4])
                return ("kwhile", e[1], cond, body, rest, e[5])
            case "knone":
                return e

    def manage_branches(e):
        # kExps = ["klet", "kreturn", "kass", "kif", "kload", "kwhile", "knone"]
        def last_branch(ke):
            match ke[0]:
                case "klet":
                    last = last_branch(ke[3])
                case "kass":
                    last = last_branch(ke[3])
                case "kif":
                    last = ke[5][-1]
                case "kload":
                    last = last_branch(ke[3])
                case "kwhile":
                    last = ke[5][-1]
                case _:
                    last = None
            return last
        match e[0]:
            case "klet":
                return ("klet", e[1], e[2], manage_branches(e[3]))
            case "kass":
                return ("kass", e[1], e[2], manage_branches(e[3]))
            case "kif":
                oldPhi = e[4][2]
                ifLast = last_branch(e[2]) or oldPhi[1][1]
                elseLast = last_branch(e[3]) or oldPhi[2][1]
                newPhi = ("kphi", (oldPhi[1][0], ifLast), (oldPhi[2][0], elseLast), oldPhi[3])
                return ("kif", e[1], manage_branches(e[2]), manage_branches(e[3]),("klet", e[4][1], newPhi, e[4][3]), e[5])
            case "kload":
                return ("kload", e[1], e[2], manage_branches(e[3]))
            case "kwhile":
                return ("kwhile", e[1], e[2], manage_branches(e[3]), manage_branches(e[4]), e[5])
            case _:
                return e
    
    k = load_var(k)
    k = manage_branches(k)
    return k

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
            ty = get_type(v)
            if ty == "double":
                return f"{compile_fop(v[1])} {compile_val(v[2])}, {compile_val(v[3])}"
            else:
                return f"{compile_op(v[1])} {compile_val(v[2])}, {compile_val(v[3])}"
        case "kphi":
                return f"phi {v[3]} [ {compile_val(v[1][0])}, %{v[1][1]} ], [ {compile_val(v[2][0])}, %{v[2][1]} ]"
        # case "kcall":
        case _:
            return "unknown kval"

# def compile_val(v: KVal) : String = v match {
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
            ty = get_type(e[1])
            return i(f"ret {ty} {compile_val(e[1])}")
        case "klet":
            return i(f"%{e[1]} = {compile_val(e[2])}") + compile_exp(e[3])
        case "kass":
            if e[1][1] in alloca:
                return i(f"store {get_type(e[2])} {compile_val(e[2])}, {e[1][2]}* %{e[1][1]}, align 4") + compile_exp(e[3])
            else:
                eTmp = ("kop", "+", e[2], ("knum", 0, "i32"))
                return i(f"%{e[1][1]} = {compile_val(eTmp)}") + compile_exp(e[3])
        case "kload":
            return i(f"%{e[1]} = load {e[2][2]}, {e[2][2]}* %{e[2][1]}, align 4") + compile_exp(e[3])
        case "kif":
            ifBr = e[5][0]
            elseBr = e[5][1]
            end = e[5][2]
            return i(f"br i1 %{e[1]}, label %{ifBr}, label %{elseBr}") + l(f"\n{ifBr}") + compile_exp(e[2]) + i(f"br label %{end}") + l(f"\n{elseBr}") + compile_exp(e[3]) + i(f"br label %{end}") + l(f"\n{end}") + compile_exp(e[4])
        case "kwhile":
            entry = e[5][0]
            cond = e[5][1]
            body = e[5][2]
            end = e[5][3]
            return i(f"br label %{entry}") + l(f"\n{entry}") + i(f"br label %{cond}") + l(f"\n{cond}") + compile_exp(e[2]) + i(f"br i1 %{e[1]}, label %{body}, label %{end}") + l(f"\n{body}") + compile_exp(e[3]) + i(f"br label %{cond}") + l(f"\n{end}") + compile_exp(e[4])
        case "knone":
            return ""


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

def compile_alloca():
    s = ""
    for a in alloca:
        s = s + i(f"%{a} = alloca {varEnv.get(a)}, align 4")
    return s

def compile_decl(d):
    match d[0]:
        case "dAssign":
            return d
        case "dDef":
            return d
        case "dMain":
            cpsb = CPSB(d[1], lambda x : ("kreturn", ("knum", 0, "i32")))
            cpsb = format_klang(cpsb)
            print("after format_klang:")
            print(cpsb)
            # cpsb = CPSB(d[1], lambda x : ("kreturn", x))
            s = m("define i32 @main() {") + compile_alloca() + compile_exp(cpsb) + m("}\n")
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
    progll = '\n'.join(list(map(compile_decl, prog)))
    # return prelude + "\n" + progll
    return progll

if __name__ == '__main__':
    filename = sys.argv[1]
    file = open(filename)
    data = file.read()
    print("\n'While' language file:")
    print(data)
    file.close()
    print("\nAST generated:")
    p = parser.parse(data)
    print(p)
    print("\nCPSB:")
    # print(CPSB(p, lambda x : ("kreturn", x)))
    print(CPSB(p, lambda x : ("kreturn", ("knum", 0, "i32"))))
    varEnv = {}
    alloca = []
    print("\nLLVM: ")
    ll = compile(p)
    print(ll)
