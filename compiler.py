# python3 compiler.py test/test.while
# lli -march=arm64 testll/test2.ll 

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
    # kVals = ["knum", "kvar", "kneg", "kop", "kphi"]
    match e[0]:
        case "knum":
            return e[2]
        case "kvar":
            return e[2]
        case "kstr":
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
        case "kphi":
            return e[3]
        case "kcall":
            return e[3]
        case "kcast":
            return e[3]
        case "kvoid":
            return "void"
        case "kundef":
            return e[2]
        case "karr":
            # l = len(e[1])
            # if l < 1:
            #     return "[0 x i32]"
            
            # firstE = e[1][0]
            # if firstE[0] == "karr":
            #     largestE = (len(firstE[1]), get_type(firstE))
            # else:
            #     largestE = (1, get_type(firstE))

            # for i in e[1:]:
            #     # TODO: type check.
            #     # if get_type(i) != largestE[1]:
            #     #     raise Exception("array type error")

            #     if i[0] == "karr" and len(i[1]) > largestE[0]:
            #         largestE = (len(i[1]), get_type(i))
            # return f"[{l} x {largestE[1]}]"
            return e[2]
        case _:
            return "undef"

varEnv = {}     #element form {var name : var type}
strEnv = []     #element form (var name, string value, pointer var name)
alloca = []     #element form (var name)
ptrlst = []     #element form (var name)

gvarEnv = {}    #element form {var name : var type}
funEnv = {  "i32_to_double" : "double",
            "double_to_i32" : "i32"}
def RefreshEnv():
    global varEnv, strEnv, alloca
    varEnv = {}
    strEnv = []
    alloca = []

def CPS(stmt, f):
    match stmt[0]:
        case "Var":
            ty = varEnv.get(stmt[1], "undef")
            ty = gvarEnv.get(stmt[1], ty)
            return f(("kvar", stmt[1], ty))
        case "Num":
            return f(("knum", stmt[1], "i32"))
        case "FNum":
            return f(("knum", stmt[1], "double"))
        case "Str":
            sl = Fresh("str")
            z = Fresh("tmp")
            strEnv.append((sl, stmt[1], z))
            # print("strEnv:")
            # print(strEnv)
            # return f(("kstr", sl, f"[{len(stmt[1]) + 1} x i8]"))

            # return f(("kstr", z, "i8*"))
            return f(("kvar", z, "i8*"))
        case "Neg":
            if stmt[1][0] in ["Num", "FNum"]:
                return CPS(stmt[1], lambda y : f(('kneg', y)))
            elif stmt[1][0] == "Neg":
                return CPS(stmt[1][1], lambda y : f(y))
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
                    ty = funEnv.get(stmt[1])
                    if ty and ty != "void":
                        z = Fresh("tmp")
                        return ("klet", z, ("kcall", stmt[1], vs, ty), f(("kvar", z, ty)))
                    else:
                        return ("kcallv", stmt[1], vs, f(("kvoid", "")))
                else:
                    return CPS(args[0], lambda y : aux(args[1:], vs + [y]))
            return aux(stmt[2], [])
        case "writeId":
            def tyMap(y):
                ty = get_type(y)
                if ty == "i8*":
                    return "str"
                return ty
            return CPS(stmt[1], lambda y : ("kcallv", "write_" + tyMap(y), [y], f(("kvoid", ""))))
        case "array":
            def aux2(args, vs):   # largest element of form (length, type)
                if (0 == len(args)):
                    l = len(vs)
                    if l < 1:
                        return "[0 x i32]"
                    
                    firstE = vs[0]
                    if firstE[0] == "karr":
                        largestE = (len(firstE[1]), get_type(firstE))
                    else:
                        largestE = (1, get_type(firstE))

                    for i in vs[1:]:
                        # TODO: type check.
                        # if get_type(i) != largestE[1]:
                        #     raise Exception("array type error")

                        if i[0] == "karr" and len(i[1]) > largestE[0]:
                            largestE = (len(i[1]), get_type(i))
                    
                    return f(("karr", vs, f"[{l} x {largestE[1]}]"))
                else:
                    return CPS(args[0], lambda y : aux2(args[1:], vs + [y]))

            return aux2(stmt[1], [])
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
                
                if (stmt[2][0] == 'array') and (stmt[1][1] not in alloca):
                    alloca.append(stmt[1][1])

                return CPS(stmt[1], lambda y1 : CPS(stmt[2], lambda y2 : kassign(y1, y2)))

        case "while":
            reg = ("kvoid", "")
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
            ifReg = ("kvoid", "")
            elseReg = ("kvoid", "")
            regTy = "i32"
            #FIXME: when if branch returns void and else branch returns non i32 value, there is a problem with phi node's type.
            #FIXME: When returning i32 values. if one var is of pointer type i32*, ret will not call load but bitcast.
            def registerIf(x):
                nonlocal ifReg, regTy
                ifRet = Fresh("ifRet")
                if x == ("kvoid", ""):
                    ifReg = ("kundef", "undef", regTy)
                    return ("knone", None)
                else:
                    regTy = get_type(x)
                    ifReg = ("kvar", ifRet, regTy)
                    return ("kass", ifReg, x, ("knone", None))
            def registerElse(x):
                nonlocal elseReg, regTy
                elseRet = Fresh("elseRet")
                if x == ("kvoid", ""):
                    elseReg = ("kundef", "undef", regTy)
                    return ("knone", None)
                else:
                    regTy = get_type(x)
                    elseReg = ("kvar", elseRet, regTy)
                    return ("kass", elseReg, x, ("knone", None))

            bExp = format_bexp(stmt[1])
            blIf = stmt[2]
            blEl = stmt[3]
            z = Fresh("tmp")
            phi = Fresh("tmp")
            ifLabel = Fresh("if_branch")
            elseLabel = Fresh("else_branch")
            endLabel = Fresh("if_end")
            return CPS(bExp[2], lambda y1 : CPS(bExp[3], lambda y2 : ("klet", z, ("kop", bExp[1], y1, y2), ("kif", z, CPSB(blIf, lambda x1 : registerIf(x1)), CPSB(blEl, lambda x2 : registerElse(x2)), ("klet", phi, ("kphi", (ifReg, ifLabel), (elseReg, elseLabel), regTy), f(("kvar", phi, regTy))), (ifLabel, elseLabel, endLabel)))))
        case "skip":
            return ("kcallv", "skip", [], f(("kvoid", "")))
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

kExps = ["klet", "kreturn", "kass", "kif", "kload", "kwhile", "knone", "kcallv"]
kVals = ["knum", "kvar", "kneg", "kop", "kphi", "kcall", "karr", "kvoid", "kcast", "kundef"]

def format_klang(k):
    global ptrlst
    ptrlst = alloca + list(gvarEnv.keys())
    def check_var_ty(e):
        global ptrlst
        def check_ptr(v):
            match v[0]:
                case "kvar":
                    print(f"ptrlst: {ptrlst}")
                    if v[1] in ptrlst:
                        return ("kvar", v[1], v[2] + "*")
                    return v
                case "kneg":
                    return check_ptr(v[1])
                case "kop":
                    left = check_ptr(v[2])
                    right = check_ptr(v[3])
                    return ("kop", v[1], left, right)
                case "kphi":    #("kphi", (ifReg, ifLabel), (elseReg, elseLabel), get_type(ifReg))
                    first = check_ptr(v[1][0])
                    second = check_ptr(v[2][0])
                    ty = get_type(v[1][0])
                    newTy = get_type(first)
                    if newTy != ty:
                        return ("kphi", (first, v[1][1]), (second, v[2][1]), newTy)
                    else:
                        return ("kphi", (first, v[1][1]), (second, v[2][1]), v[3])
                #TODO: case "karr":
                case _:
                    return v

        match e[0]: #["klet", "kreturn", "kass", "kif", "kload", "kwhile", "knone", "kcallv"]
            case "klet":
                return ("klet", e[1], check_ptr(e[2]), check_var_ty(e[3]))
            case "kreturn":
                return ("kreturn", check_ptr(e[1]))
            case "kass":
                right = check_ptr(e[2])
                if right != e[2]:
                    ptrlst = ptrlst + [e[1][1]]
                left = check_ptr(e[1])
                return ("kass", left, right, check_var_ty(e[3]))
            case "kif":
                return ("kif", e[1], check_var_ty(e[2]), check_var_ty(e[3]), check_var_ty(e[4]), e[5])
            case "kload":
                return ("kload", e[1], check_ptr(e[2]), check_var_ty(e[3]))
            case "kcallv":
                return ("kcallv", e[1], list(map(check_ptr,e[2])), check_var_ty(e[3]))
            case "kwhile":
                cond = check_var_ty(e[2])
                body = check_var_ty(e[3])
                rest = check_var_ty(e[4])
                return ("kwhile", e[1], cond, body, rest, e[5])
            case "knone":
                return e


    def format_kass(e):#["klet", "kreturn", "kass", "kif", "kload", "kwhile", "knone", "kcallv"]
        match e[0]:
            case "klet":
                return ("klet", e[1], e[2], format_kass(e[3]))
            case "kreturn":
                return e
            case "kass":
                if e[1][1] in alloca:
                    return ("kass", e[1], e[2], format_kass(e[3]))
                else:
                    if e[2][0] in ["kvar", "kundef"]:
                        ty = get_type(e[2])
                        return ("klet", e[1][1], ("kcast", e[2], ty, ty), format_kass(e[3]))

                    e2 = e[2]
                    if e[2][0] in ["knum", "kneg"]:
                        e2 = ("kop", "+", e[2], ("knum", 0, "i32"))
                    return ("klet", e[1][1], e2, format_kass(e[3]))
            case "kif":
                return ("kif", e[1], format_kass(e[2]), format_kass(e[3]), format_kass(e[4]), e[5])
            case "kload":
                return(e[0], e[1], e[2], format_kass(e[3]))
            case "kcallv":
                return ("kcallv", e[1], e[2], format_kass(e[3]))
            case "kwhile":
                cond = format_kass(e[2])
                body = format_kass(e[3])
                rest = format_kass(e[4])
                return ("kwhile", e[1], cond, body, rest, e[5])
            case "knone":
                return e
    def load_var(e):
        def extract_vars(kval, vars = []):
            match kval[0]:
                case "knum":
                    return (vars, kval)
                case "kvar":
                    if kval[1] in ptrlst:
                        # tmp = Fresh("tmp")
                        # return (vars + [(kval, tmp)], ("kvar", tmp, kval[2]))
                        if kval not in [x[0] for x in vars]:
                            tmp = Fresh("tmp")
                            return (vars + [(kval, tmp)], ("kvar", tmp, kval[2][0:-1]))
                        else:
                            tmp = [x[1] for x in vars if x[0] == kval][-1]  # for not loading n twice if in case k:=n+n etc.
                            return (vars, ("kvar", tmp, kval[2]))
                    else:
                        return (vars, kval)
                case "kneg":
                    return extract_vars(kval[1], vars)
                case "kop":
                    left = extract_vars(kval[2], vars)
                    right = extract_vars(kval[3], left[0])
                    return (right[0], ("kop", kval[1], left[1], right[1])) 
                case "kphi":
                    # br1 = extract_vars(kval[1][0], vars)
                    # br2 = extract_vars(kval[2][0], br1[0])
                    # return (br2[0], ("kphi", (br1[1], kval[1][1]), (br2[1], kval[2][1]), kval[3]))
                    return (vars, kval)
                case "kcall":
                    eVars = []
                    newKvals = []
                    for i in kval[2]:
                        e = extract_vars(i, eVars)
                        eVars = e[0]
                        newKvals += [e[1]]
                    return (eVars, ("kcall", kval[1], newKvals, kval[3]))
                case "karr":
                    eVars = []
                    newKvals = []
                    for i in kval[1]:
                        e = extract_vars(i, eVars)
                        eVars = e[0]
                        newKvals += [e[1]]
                    return (eVars, ("karr", newKvals, kval[2]))
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
            case "kcallv":
                newArgs = []
                allVars = []
                for j in e[2]:
                    (vars, newKval) = extract_vars(j)
                    newArgs += [newKval]
                    allVars += vars
                e = ("kcallv", e[1], newArgs, load_var(e[3]))
                for i in allVars:
                    e = ("kload", i[1], i[0], e)
                return e
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
            case "kcallv":
                return ("kcallv", e[1], e[2], manage_branches(e[3]))
            case _:
                return e

    def type_conversion(e):
        # kExps = ["klet", "kreturn", "kass", "kif", "kload", "kwhile", "knone", "kcallv"]
        def kval_type_change(kval):
            match kval[0]:
                case "kneg":
                    (lst, newVal) = kval_type_change(kval[1])
                    return (lst, ("kneg", newVal))
                case "kop":
                    retLst = []
                    ty = get_type(kval)
                    lV = kval[2]
                    rV = kval[3]
                    lTy = get_type(lV)
                    rTy = get_type(rV)
                    if lTy != ty:
                        lz = Fresh("tmp")
                        retLst += [(lz, ("kcall", f"{lTy}_to_{ty}", [lV], ty))]
                        lV = ("kvar", lz, ty)
                    if rTy != ty:
                        rz = Fresh("tmp")
                        retLst += [(rz, ("kcall", f"{rTy}_to_{ty}", [rV], ty))]
                        rV = ("kvar", rz, ty)
                    return  (retLst, ("kop", kval[1], lV, rV))
                # TODO: case "karr":
                case _:
                    return ([], kval)
        match e[0]:
            case "klet":
                (lst, newVal) = kval_type_change(e[2])
                exp = ("klet", e[1], newVal, type_conversion(e[3]))
                for i in lst:
                    exp = ("klet", i[0], i[1], exp)
                return exp
            case "kreturn":
                return e
            case "kass":
                (lst, newVal) = kval_type_change(e[2])
                exp = ("kass", e[1], newVal, type_conversion(e[3]))
                for i in lst:
                    exp = ("klet", i[0], i[1], exp)
                return exp
            case "kif":
                return ("kif", e[1], type_conversion(e[2]), type_conversion(e[3]), type_conversion(e[4]), e[5])
            case "kload":
                return(e[0], e[1], e[2], type_conversion(e[3]))
            case "kwhile":
                cond = type_conversion(e[2])
                body = type_conversion(e[3])
                rest = type_conversion(e[4])
                return ("kwhile", e[1], cond, body, rest, e[5])
            case "kcallv":
                return ("kcallv", e[1], e[2], type_conversion(e[3]))
            case "knone":
                return e
    
    k = manage_branches(k)
    k = check_var_ty(k)
    k = format_kass(k)
    k = load_var(k)
    k = type_conversion(k)
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


def compile_args(args):
    return ", ".join([f"{get_type(a)} {compile_val(a)}" for a in args])

def compile_val(v):
    match v[0]:
        case "knum":
            return f"{v[1]}"
        case "kvar":
            if v[1] in list(gvarEnv.keys()):
                return f"@{v[1]}"
            return f"%{v[1]}"
        case "kneg":
            return f"-{compile_val(v[1])}"
        case "kstr":
            return f"%{v[1]}"
        case "kop":
            ty = get_type(v)
            if ty == "double":
                return f"{compile_fop(v[1])} {compile_val(v[2])}, {compile_val(v[3])}"
            else:
                return f"{compile_op(v[1])} {compile_val(v[2])}, {compile_val(v[3])}"
        case "kphi":
            return f"phi {v[3]} [ {compile_val(v[1][0])}, %{v[1][1]} ], [ {compile_val(v[2][0])}, %{v[2][1]} ]"
        case "kcall":
            ty = get_type(v)
            return  f"call {ty} @{v[1]} ({compile_args(v[2])})"
        case "karr":
            return "[" + ", ".join(list(map(lambda x : f"{get_type(x)} {compile_val(x)}", v[1]))) + "]"
        case "kvoid":
            return ""
        case "kundef":
            return "undef"
        case "kcast":
            return f"bitcast {v[2]} {compile_val(v[1])} to {v[3]}"
        case _:
            return "unknown kval"

def compile_exp(e):
    match e[0]:
        case "kreturn":
            ty = get_type(e[1])
            return i(f"ret {ty} {compile_val(e[1])}")
        case "klet":
            return i(f"%{e[1]} = {compile_val(e[2])}") + compile_exp(e[3])
        case "kass":
            return i(f"store {get_type(e[2])} {compile_val(e[2])}, {get_type(e[1])} {compile_val(e[1])}, align 4") + compile_exp(e[3])
        case "kload":
            ty = get_type(e[2])
            # if gvarEnv.get(e[2][1]):
            #     return i(f"%{e[1]} = load {ty}, {ty}* @{e[2][1]}") + compile_exp(e[3])
            # else:
            #     return i(f"%{e[1]} = load {ty}, {ty}* %{e[2][1]}, align 4") + compile_exp(e[3])
            return i(f"%{e[1]} = load {ty[0:-1]}, {ty} {compile_val(e[2])}, align 4") + compile_exp(e[3])
        case "kcallv":
            return i(f"call void @{e[1]} ({compile_args(e[2])})") + compile_exp(e[3])
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

# declare i32 @printf(i8*, ...)
# @.str = private unnamed_addr constant [3 x i8] c"%f\\00", align 1

# define i32 @write() #0 {
# %a = alloca double, align 8
# %1 = load double* %a, align 8
# %2 = call i32 (i8*, ...)* @printf(i8* getelementptr inbounds ([3 x i8]*  @.str, i32 0, i32 0), double %1)
# ret i32 0
# }

pre2 = """

declare i32 @printf(i8*, ...)
@.ln = private constant [2 x i8] c"\\0A\\00"
@.string = private constant [3 x i8] c"%s\\00"
@.double = private constant [3 x i8] c"%f\\00"
@.int = private constant [3 x i8] c"%d\\00"

define double @i32_to_double(i32 %x) {
   %t0 = sitofp i32 %x to double
   ret double %t0
}

define i32 @double_to_i32(double %x) {
   %t0 = fptosi double %x to i32
   ret i32 %t0
}

define void @skip() {
    ret void
}

define void @write_ln() {
    %t0 = getelementptr [2 x i8], [2 x i8]* @.ln, i64 0, i64 0
    call i32 (i8*, ...) @printf(i8* %t0)
    ret void
}

define void @write_str(i8* %x) {
    %t0 = getelementptr [3 x i8], [3 x i8]* @.string, i64 0, i64 0
    call i32 (i8*, ...) @printf(i8* %t0, i8* %x)
    ret void
}

define void @write_double(double %x) {
    %t0 = getelementptr [3 x i8], [3 x i8]* @.double, i64 0, i64 0
    call i32 (i8*, ...) @printf(i8* %t0, double %x)
    ret void
}

define void @write_i32(i32 %x) {
    %t0 = getelementptr [3 x i8], [3 x i8]* @.int, i64 0, i64 0
    call i32 (i8*, ...) @printf(i8* %t0, i32 %x)
    ret void
}

"""

def compile_alloca():
    s = ""
    for a in alloca:
        s = s + i(f"%{a} = alloca {varEnv.get(a)}, align 4")
    return s

def compile_str():
    s = ""
    for str in strEnv:
        s = s + f"@{str[0]} = private unnamed_addr constant [{len(str[1]) + 1} x i8] c\"{str[1]}\\00\"" + "\n"
    s = s + "\n"
    return s

def compile_str_ptr():
    s = ""
    for str in strEnv:
        s = s + i(f"%{str[2]} = getelementptr [{len(str[1]) + 1} x i8], [{len(str[1]) + 1} x i8]* @{str[0]}, i64 0, i64 0")
    return s

def compile_decl(d):
    RefreshEnv()
    match d[0]:
        # FIXME: handle aexp like global k := 3 + 1;
        case "dAssign": 
            ty = "undef"
            def retTy(r):
                print(f"r: {r}")
                nonlocal ty
                ty = get_type(r)
                return ("kreturn", r)
            cps = CPS(("assign", d[1], d[2]), lambda x : retTy(x))
            gvarEnv[d[1][1]] = ty
            s = f"@{d[1][1]} = global {ty} {d[2][1]}"
            return s
        case "dDef":
            funTy = "void"
            def retTy(r):
                print(f"r: {r}")
                nonlocal funTy
                funTy = get_type(r)
                return ("kreturn", r)
            cpsb = CPSB(d[2], lambda x : retTy(x))
            cpsb = format_klang(cpsb)
            # print("after format_klang:")
            # print(cpsb)
            # cpsb = CPSB(d[1], lambda x : ("kreturn", x))
            funEnv[d[1]] = funTy
            s = compile_str() + m(f"define {funTy} @{d[1]}() " + "{") + compile_alloca() + compile_str_ptr() + compile_exp(cpsb) + m("}\n")
            return s
        case "dMain":
            cpsb = CPSB(d[1], lambda x : ("kreturn", ("knum", 0, "i32")))
            print("cpsb before format_klang:")
            print(cpsb)
            cpsb = format_klang(cpsb)
            print("cpsb after format_klang:")
            print(cpsb)
            # cpsb = CPSB(d[1], lambda x : ("kreturn", x))
            s = compile_str() + m("define i32 @main() {") + compile_alloca() + compile_str_ptr() + compile_exp(cpsb) + m("}\n")
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

filedir = ""

def format_ast(ast, imported = []):
    main = []
    newast = []
    imp = []
    gvar = []

    for i in ast:
        if i[0] == "import":
            if i[1]  not in imported:
                imp.append(i)
        elif i[0] == "gassign":
            gvar.append(i)
        else: 
            if i[0] in ["aexp", "bexp", "array", "Num", "FNum", "Var"]:
                z = Fresh("tmp")
                i = ('assign', ('Var', z), i)
            main.append(i)

    for i in gvar:
        newast.append(("dAssign", i[1], i[2]))

    for i in imp:
        whilePostfix = i[1].find(".while")
        if whilePostfix < 0:
            filename = filedir + i[1] + ".while"
            varname = i[1]
        else:
            filename = filedir + i[1]
            varname = i[1][0:whilePostfix]
        impFile = open(filename)
        impData = impFile.read()
        impFile.close()
        p = parser.parse(impData)
        asti = format_ast(p, imported + imp)
        for j in asti:
            if j[0] == "dMain":
                newast.append(("dDef", varname, j[1]))
            else:
                newast.append(j)
    
    newast.append(("dMain", main))
    return newast

def compile(ast):
    prog = format_ast(ast)
    print("formated AST:")
    print(prog)
    progll = pre2 + '\n'.join(list(map(compile_decl, prog)))
    # return prelude + "\n" + progll
    return progll

if __name__ == '__main__':
    filename = sys.argv[1]

    filedirIndex = filename.rfind('/')
    if filedirIndex >= 0:
        filedir = filename[0:filedirIndex] + "/"
    
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
    RefreshEnv()
    print("\nLLVM: ")
    ll = compile(p)
    print(ll)

    f = open(filename.replace(".while", ".ll"), "w")
    f.write(ll)
    f.close()
