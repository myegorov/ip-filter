#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include "fnv.h"
#include "bloom.h"
#include "util.h"

// constructor
bloomfilter_t *bf_new(const unsigned long num_elements, const double fpp) {
  double m = ceil((-(double)num_elements * log(fpp)) / (pow(log(2), 2)));
  double k = ceil(m * log(2) / ((double)num_elements));
  bitarray_t *bitarray = ba_new((unsigned long)m);
  int num_hashes = (int) k;

  bloomfilter_t *bf = wrap_malloc(sizeof(bloomfilter_t));
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

/* //TODO: modified to make directly comparable to _with_prefetch version */
/* int bf_contains(const bloomfilter_t *bf, const char *key) { */
/*   uint64_t hash = hash_fnv(key); */
/*   uint64_t h1, h2; */
/*   h1 = hash & 0x00000000FFFFFFFFLL; */
/*   h2 = hash & 0xFFFFFFFF00000000LL; */
/*   unsigned long ix; */
/*   for (int i = 0; i < bf->k; i++) { */
/*     ix = (h1 + i * h2) % (bf->ba->size); */
/*     if (((bf->ba->bits)[ix/8] & (1 << (ix%8))) == 0) { */
/*       return 0; */
/*     } */
/*     /1* if (ba_read_bit(bf->ba, ix) == 0) { *1/ */
/*     /1*   return 0; *1/ */
/*     /1* } *1/ */
/*   } */
/*   return 1; */
/* } */

// modified bf_contains() identical with bf_contains_with_prefetch()
// except for no __builtin_prefetch()
int bf_contains(const bloomfilter_t *bf, const char *key) {
  uint64_t hash = hash_fnv(key);
  uint64_t h1, h2;
  h1 = hash & 0x00000000FFFFFFFFLL;
  h2 = hash & 0xFFFFFFFF00000000LL;
  unsigned long indices[bf->k];
  unsigned long ix;
  for (int i = 0; i < bf->k; i++) {
    ix = (h1 + i * h2) % (bf->ba->size);
    indices[i] = ix;
  }
  for (int i = 0; i < bf->k; i++) {
    if (((bf->ba->bits)[indices[i]/8] & (1 << (indices[i]%8))) == 0) {
      return 0;
    }
  }
  return 1;
}


/* //TODO: test3 */
/* int bf_contains_with_prefetch_next(const bloomfilter_t *bf, const char *key, const char *next_key) { */
/*   uint64_t hash = hash_fnv(key); */
/*   uint64_t h1, h2; */
/*   h1 = hash & 0x00000000FFFFFFFFLL; */
/*   h2 = hash & 0xFFFFFFFF00000000LL; */

/*   uint64_t hash_next = hash_fnv(next_key); */
/*   uint64_t h1_next, h2_next; */
/*   h1_next = hash_next & 0x00000000FFFFFFFFLL; */
/*   h2_next = hash_next & 0xFFFFFFFF00000000LL; */

/*   unsigned long ix; */
/*   for (int i = 0; i < bf->k; i++) { */
/*     ix = (h1_next + i * h2_next) % (bf->ba->size); */
/*     __builtin_prefetch (& (bf->ba->bits)[ix/8], 0, 1); */
/*   } */
/*   for (int i = 0; i < bf->k; i++) { */
/*     ix = (h1 + i * h2) % (bf->ba->size); */
/*     if (((bf->ba->bits)[ix/8] & (1 << (ix%8))) == 0) { */
/*       return 0; */
/*     } */
/*   } */
/*   return 1; */
/* } */


//TODO: test2
int bf_contains_with_prefetch(const bloomfilter_t *bf, const char *key) {
  uint64_t hash = hash_fnv(key);
  uint64_t h1, h2;
  h1 = hash & 0x00000000FFFFFFFFLL;
  h2 = hash & 0xFFFFFFFF00000000LL;
  unsigned long indices[bf->k];
  unsigned long ix;
  for (int i = 0; i < bf->k; i++) {
    ix = (h1 + i * h2) % (bf->ba->size);
    indices[i] = ix;
    __builtin_prefetch (& (bf->ba->bits)[ix/8], 0, 1);
  }
  // TODO: loop back from end of indices[], presumably fresher in memory
  for (int i = 0; i < bf->k; i++) {
    if (((bf->ba->bits)[indices[i]/8] & (1 << (indices[i]%8))) == 0) {
      return 0;
    }
  }
  return 1;
}


/* //TODO: test1 */
/* int bf_contains_with_prefetch(const bloomfilter_t *bf, const char *key) { */
/*   uint64_t hash = hash_fnv(key); */
/*   uint64_t h1, h2; */
/*   h1 = hash & 0x00000000FFFFFFFFLL; */
/*   h2 = hash & 0xFFFFFFFF00000000LL; */
/*   unsigned long ix = h1 % (bf->ba->size); */
/*   unsigned long next_ix; */
/*   for (int i = 0; i < bf->k; i++) { */
/*     __builtin_prefetch (&(bf->ba->bits)[(next_ix=(h1 + (i+1) * h2) % (bf->ba->size))/8], 0, 1); */

/*     if (( (1 << (ix%8)) & (bf->ba->bits)[ix/8] ) == 0) { */
/*       return 0; */
/*     } */
/*     ix = next_ix; */
/*   } */
/*   return 1; */
/* } */

/* //TODO: test0 */
/* int bf_contains_with_prefetch(const bloomfilter_t *bf, const char *key) { */
/*   uint64_t hash = hash_fnv(key); */
/*   uint64_t h1, h2; */
/*   h1 = hash & 0x00000000FFFFFFFFLL; */
/*   h2 = hash & 0xFFFFFFFF00000000LL; */
/*   unsigned long ix = h1 % (bf->ba->size); */
/*   for (int i = 0; i < bf->k; i++) { */
/*     if (((bf->ba->bits)[ix/8] & (1 << (ix%8))) == 0) { */
/*       return 0; */
/*     } */
/*     __builtin_prefetch (&(bf->ba->bits)[(ix=(h1 + (i+1) * h2) % (bf->ba->size))/8], 0, 1); */
/*   } */
/*   return 1; */
/* } */

int bf_contains_pseudo(const bloomfilter_t *bf, const char *key) {
  // do some constant work
  uint64_t hash = hash_fnv(key);
  uint64_t h1, h2;
  h1 = hash & 0x00000000FFFFFFFFLL;
  h2 = hash & 0xFFFFFFFF00000000LL;
  unsigned long ix;
  // look up always at index 0
  int LOOKUP = 0;

  // note the loop is eliminated by optimizing compiler
  for (int i = 0; i < bf->k; i++) {
    (bf->ba->bits)[LOOKUP];
  }
  return 1;
}

int bf_do_nothing(const bloomfilter_t *bf) {
  // look up always at index 0
  int LOOKUP = 0;

  // note the loop is eliminated by optimizing compiler
  for (int i = 0; i < bf->k; i++) {
    (bf->ba->bits)[LOOKUP];
  }
  return 1;
}
