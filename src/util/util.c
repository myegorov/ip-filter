#include "util.h"

/* fopen() with error checking */
FILE *wrap_fopen(const char *fname, const char *mode) {
  FILE *infile = fopen(fname, mode);

  if (infile == NULL) {
    perror(fname);
    exit(EXIT_FAILURE);
  }
  return infile;
}

/* fclose() with error checking */
int wrap_fclose(FILE *infile) {
  if(fclose(infile) != 0){
    perror("wrap_fclose");
    exit(EXIT_FAILURE);
  }
  return 0;
}

/* malloc() with error checking */
void *wrap_malloc(size_t size) {
  void *mp = malloc(size);
  if (mp == NULL) {
    perror("wrap_malloc");
    exit(EXIT_FAILURE);
  }
  return mp;
}

/* calloc() with error checking */
void *wrap_calloc(size_t num_elements, size_t element_size) {
  void *mp = calloc(num_elements, element_size);
  if (mp == NULL) {
    perror("wrap_calloc");
    exit(EXIT_FAILURE);
  }
  return mp;
}

/* realloc() with error checking */
void *wrap_realloc(void *mp, size_t *old_size, size_t element_size) {
  void *new_mp = realloc(mp, 2 * (*old_size) * element_size);
  if (new_mp == NULL) {
    free(mp); // free old array
    perror("wrap_realloc");
    exit(EXIT_FAILURE);
  }

  *old_size *= 2;
  return new_mp;
}
