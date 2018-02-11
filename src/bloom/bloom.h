/*
 * Vanilla Bloom filter implementation
 * https://en.wikipedia.org/wiki/Bloom_filter
 *
 */

#ifndef BLOOM
#define BLOOM

#include "bitarray.h"

typedef struct {
  double false_positive_probability;
  unsigned long n; // num elements to insert != ba->size
  int k;  // num hash functions
  bitarray_t *ba; // contains size (a.k.a. m) and bit array bits
} bloomfilter_t;


// API
// create new bloom filter
bloomfilter_t *bf_new(const unsigned long num_elements, const double fpp);

// deallocate memory
void bf_free(bloomfilter_t *bf);

// print bloomfilter info for debugging
void bf_print(bloomfilter_t *bf);

// insert key in bloomfilter
void bf_insert(bloomfilter_t *bf, const char *key);

// membership test
// 0 => does NOT contain
// non-zero => positive or false positive
int bf_contains(const bloomfilter_t *bf, const char *key);

// TODO: insert a vector of keys w/ prefetching
// TODO: membership test for a vector of keys w/ prefetching
#endif
