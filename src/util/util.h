#ifndef UTIL
#define UTIL

#include <stdio.h>
#include <stdlib.h>

// I/O wrappers
FILE *wrap_fopen(const char *fname, const char *mode);
int wrap_fclose(FILE *f);

// dynamic memory allocation wrappers
void *wrap_malloc(size_t size);
void *wrap_calloc(size_t num_elements, size_t element_size);
void *wrap_realloc(void *mp, size_t *old_size, size_t element_size);

#endif
