#include <stdlib.h>
#include <math.h>
#include "bitarray.h"
#include "util.h"

// constructor
bitarray_t *ba_new(const unsigned long size) {
  bitarray_t *arr = wrap_malloc(sizeof(bitarray_t));

  // round to next multiple of 8; size is in bits
  arr->size = (size + 7UL) & ~7UL;

  // initialize bit array to 0's
  arr->bits = (unsigned char*) wrap_calloc((size_t)(arr->size)/8, sizeof(char));
  return arr;
}

// delete bitarray
void ba_free(bitarray_t *arr) {
  free(arr->bits);
  free(arr);
}

// return bit at ix
// client has to check that ix is within array bounds
unsigned char ba_read_bit(bitarray_t *arr, const unsigned long ix) {
  unsigned char val = ((arr->bits)[ix/8] & (1 << (ix%8))) != 0;
  return val;
}

// set bit at ix to 1
// client has to check that ix is within array bounds
void ba_set_bit(bitarray_t *arr, const unsigned long ix) {
  (arr->bits)[ix/8] |= (1 << (ix%8));
}


// set bit at ix to 0
// client has to check that ix is within array bounds
void ba_clear_bit(bitarray_t *arr, const unsigned long ix) {
  (arr->bits)[ix/8] &= ~(1 << (ix%8));
}
