#include <iostream>
using namespace std;

// #include <stdio.h>
// #include <stdlib.h>

#include <readline/readline.h>
// #include <readline/history.h>

void test() {
    return;
}

int main() {
    string s = readline( "test> " );
    int a;
    if (s == "a") {
        a = 1;
    } else {
        test();
    }
}

    // string name;
    // cout << "Hello World!";
    // cin >> name;
// string firstName;
// cout << "Type your first name: ";
// cout << "Your name is: " << firstName;