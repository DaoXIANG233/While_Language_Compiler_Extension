

declare i32 @printf(i8*, ...)
@.ln = private constant [2 x i8] c"\0A\00"
@.string = private constant [3 x i8] c"%s\00"
@.double = private constant [3 x i8] c"%f\00"
@.int = private constant [3 x i8] c"%d\00"

define double @i32_to_double(i32 %x) {
   %t0 = sitofp i32 %x to double
   ret double %t0
}

define i32 @double_to_i32(double %x) {
   %t0 = fptosi double %x to i32
   ret i32 %t0
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


define i32 @main() {
    %k = alloca i32, align 4
    store i32 1, i32* %k, align 4
    store i32 2, i32* %k, align 4
    %tmp_0 = load i32, i32* %k, align 4
    call void @write_i32 (i32 %tmp_0)
    ret i32 0
}

