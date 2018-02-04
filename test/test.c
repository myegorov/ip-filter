#include <stdio.h>
#include <stdint.h>
#include "fnv.h"

int main(int argc, char *argv[]) {
  const char *strings[] = {"abc", "", "\n", "whatever", "12.123.1.1"};
  uint64_t hash;
  for (int i = 0; i < (sizeof(strings) / sizeof(strings[0])); i++) {
      hash = hash_fnv(strings[i]);
      printf("%s: %lu\n", strings[i], hash);
  }
  return 0;
}
