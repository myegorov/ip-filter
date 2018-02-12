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

// membership test using __builtin_prefetch for forthcoming bitarray address
// prefetch addresses of bitarray[future_hash] where multiple hash functions are involved
int bf_contains_with_prefetch(const bloomfilter_t *bf, const char *key);

// pseudo membership tests
// look up bitarray[0] on each request and return 1
int bf_contains_pseudo(const bloomfilter_t *bf, const char *key);
int bf_do_nothing(const bloomfilter_t *bf);

#endif
