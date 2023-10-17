// Header file for input output functions
#include <stdio.h>

int myMathFunc(int x, int y) { return (10 * x  * x + 10 * y * y) / (x * x + y * y + 1); }

int main(int argc, char *argv[]) {
HELLO_LOOP:
  for (int i = 0; i < 5; ++i) {
    int j = argc;
    int y = 2 * i;
    int z = j + y;
    int invariant = myMathFunc(argc, 3);
    printf("Hello World %d %d\n", z, invariant);
  }
  return 0;
}