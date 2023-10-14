// Header file for input output functions
#include <stdio.h>

// main function -
// where the execution of program begins
int main(int argc, char *argv[]) {
HELLO_LOOP:
  for (int i = 0; i < 5; ++i) {
    printf("Hello World %d\n", i);
  }
  return 0;
}