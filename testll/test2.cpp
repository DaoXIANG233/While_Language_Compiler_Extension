#include <stdio.h>
#include <stdlib.h>

#include <readline/readline.h>
#include <readline/history.h>

//  clang -S -emit-llvm testll/test2.cpp

int main()
{
    printf( "%s\n", readline( "test> " ) );
    return 0;
}