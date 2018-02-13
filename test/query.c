#define _GNU_SOURCE // for getline()

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "util.h"
#include "bloom.h"

void strip_newline(char *str);
char **append(const char *line_buffer, char **ips, size_t iter, size_t *strarray_length);
void populate_filter(bloomfilter_t *bloomfilter, char **strs, size_t size);
void query_filter(const bloomfilter_t *bloomfilter, char **strs, size_t size);

void strip_newline(char *str) {
    // strip newline
    str[strcspn(str, "\n")] = '\0';
    str[strcspn(str, "\r\n")] = '\0';
}

char **append(const char *line_buffer, char **ips, size_t iter, size_t *strarray_length) {
    // dynamically resize ip array
    if (iter >= *strarray_length) {
      ips = wrap_realloc(ips, strarray_length, sizeof(char *));
    }
    // allocate space for ip
    ips[iter] = wrap_malloc((strlen(line_buffer)+1) * sizeof(char));
    strcpy(ips[iter], line_buffer);
    return ips;
}

void populate_filter(bloomfilter_t *bloomfilter, char **strs, size_t size) {
  // for debugging
  bf_print(bloomfilter);

  for (int i = 0; i < size; i++) {
      bf_insert(bloomfilter, strs[i]);
  }
}

void query_filter(const bloomfilter_t *bloomfilter, char **strs, size_t size) {
  clock_t start, end;
  int *res = wrap_malloc(size * sizeof(int));

  puts("Starting queries...");
  start = clock();

  for (int i = 0; i < size; i++) {
#ifdef PREFETCH
    res[i] = bf_contains_with_prefetch(bloomfilter, strs[i]);
#endif
#ifdef NOPREFETCH
    res[i] = bf_contains(bloomfilter, strs[i]);
#endif
#ifdef PSEUDO
    res[i] = bf_contains_pseudo(bloomfilter, strs[i]);
#endif
#ifdef IDLE
    res[i] = bf_do_nothing(bloomfilter);
#endif
  }

  end = clock();
  printf("%ld queries took %f seconds\n", size, ((double)(end - start)) / CLOCKS_PER_SEC);

  // making sure that calls to bf_contains() are not eliminated by optimizing compiler
  printf("last element of res: %d\n", res[size-1]);
  free(res);
}

int main(void) {
  static const char *FNAME = "./data/ips.txt";
  FILE *infile = wrap_fopen(FNAME, "r");

  // store current line from file
  size_t line_length = 80;
  char *line_buffer = wrap_malloc(line_length);

  // initial guess at length of array of strings
  size_t strarray_length = 131072; // 2^17
  char **ips = wrap_malloc(strarray_length * sizeof(char *));
  size_t iter = 0;

  while(getline(&line_buffer, &line_length, infile) != -1){
    strip_newline(line_buffer);
    ips = append(line_buffer, ips, iter, &strarray_length);
    iter += 1;
  }
  wrap_fclose(infile);

  // copy ips array several times over to make sure it doesn't fit in L3 cache
  size_t scale = 10;
  size_t new_iter = scale * iter;
  char **new_ips = wrap_malloc(new_iter * sizeof(char *));
  for (int i = 0; i < scale; i++) {
    memcpy(new_ips + i * iter, ips, iter * sizeof(char *));
  }

  // insert & query Bloom filter
  /* bloomfilter_t *bloomfilter = bf_new(iter, 1e-6); */
  bloomfilter_t *bloomfilter = bf_new(new_iter, 1e-6);
  /* populate_filter(bloomfilter, ips, iter); */
  populate_filter(bloomfilter, new_ips, new_iter);
  /* query_filter(bloomfilter, ips, iter); */
  query_filter(bloomfilter, new_ips, new_iter);

  // free allocated memory
  bf_free(bloomfilter);
  for (int i = 0; i < iter; i++){
    free(ips[i]);
  }
  free(ips);
  free(new_ips);
  free(line_buffer);

  return 0;
}
