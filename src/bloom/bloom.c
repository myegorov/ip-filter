#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdint.h>
#include "fnv.h"
#include "bloom.h"

// constructor
bloomfilter_t *bf_new(const unsigned long num_elements, const double fpp) {
  double m = (-(double)num_elements * log(fpp)) / (pow(log(2), 2));
  double k = m * log(2) / ((double)num_elements);
  bitarray_t *bitarray = ba_new((unsigned long)m);
  int num_hashes = (int) k;

  bloomfilter_t *bf = malloc(sizeof(bloomfilter_t));
  bf->false_positive_probability = fpp;
  bf->n = num_elements;
  bf->k = num_hashes;
  bf->ba = bitarray;

  return bf;
}

// delete bloomfilter
void bf_free(bloomfilter_t *bf) {
  ba_free(bf->ba);
  free(bf);
}

void bf_print(bloomfilter_t *bf) {
  printf("bloom filter at %p\n", (void *)bf);
  printf("\t  target num elements: %lu\n", bf->n);
  printf("\t  target false pos probability: %f\n", bf->false_positive_probability);
  printf("\t  num hash functions: %d\n", bf->k);
  printf("\t  bitarray size: %lu\n", bf->ba->size);
}

void bf_insert(bloomfilter_t *bf, const char *key) {
  uint64_t hash = hash_fnv(key);
  uint64_t h1, h2;
  h1 = hash & 0x00000000FFFFFFFFLL;
  h2 = hash & 0xFFFFFFFF00000000LL;
  unsigned long ix;
  for (int i = 0; i < bf->k; i++) {
    ix = (h1 + i * h2) % (bf->ba->size);
    ba_set_bit(bf->ba, ix);
  }
}

int bf_contains(bloomfilter_t *bf, const char *key) {
  uint64_t hash = hash_fnv(key);
  uint64_t h1, h2;
  h1 = hash & 0x00000000FFFFFFFFLL;
  h2 = hash & 0xFFFFFFFF00000000LL;
  unsigned long ix;
  for (int i = 0; i < bf->k; i++) {
    ix = (h1 + i * h2) % (bf->ba->size);
    if (ba_read_bit(bf->ba, ix) == 0) {
      return 0;
    }
  }
  return 1;
}
