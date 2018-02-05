#ifndef BITARRAY
#define BITARRAY

typedef struct {
  unsigned long size;
  unsigned char *bits;
} bitarray_t;

// API
// create new array of bits, intialized to 0's
bitarray_t *ba_new(const unsigned long size);

// set bit
void ba_set_bit(bitarray_t *arr, const unsigned long ix);

// clear bit
void ba_clear_bit(bitarray_t *arr, const unsigned long ix);

// read bit
unsigned char ba_read_bit(bitarray_t *arr, const unsigned long ix);

// deallocate memory
void ba_free(bitarray_t *arr);

#endif
