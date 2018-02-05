#include <stdio.h>
#include <stdint.h>
#include "fnv.h"
#include "bitarray.h"

int main(int argc, char *argv[]) {
  // test bitarray
  bitarray_t *bitarray = ba_new(12LU);
  printf("length: %lu, bits[14]: %d\n", bitarray->size, ba_read_bit(bitarray, 14));

  ba_set_bit(bitarray, 15);
  printf("set @15: bits[15]: %d\n", ba_read_bit(bitarray, 15));

  ba_clear_bit(bitarray, 15);
  printf("clear @15: bits[15]: %d\n", ba_read_bit(bitarray, 15));

  ba_free(bitarray);

  // test hashing
  const char *strings[] = {"abc", "", "\n", "whatever", "12.123.1.1"};
  uint64_t hash;
  for (int i = 0; i < (sizeof(strings) / sizeof(strings[0])); i++) {
      hash = hash_fnv(strings[i]);
      printf("%s: %lu\n", strings[i], hash);
  }
  return 0;
}
