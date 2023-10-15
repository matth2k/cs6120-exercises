// Header file for input output functions
#include <stdio.h>

// main function -
// where the execution of program begins
int main(int argc, char *argv[]) {
HELLO_LOOP:
  for (int i = 0; i < 5; ++i) {
    int j = argc;
    int y = 2 * i;
    int z = j + y;
    int invariant = argc * argc * argc;
    printf("Hello World %d %d\n", z, invariant);
  }
  return 0;
}