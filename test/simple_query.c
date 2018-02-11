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
  puts("Starting simple queries...");
  start = clock();

  for (int i = 0; i < size; i++) {
    bf_contains(bloomfilter, strs[i]);
  }

  end = clock();
  printf("%ld queries took %f seconds\n", size, ((double)(end - start)) / CLOCKS_PER_SEC);
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

  // insert & query Bloom filter
  bloomfilter_t *bloomfilter = bf_new(iter, 1e-6);
  populate_filter(bloomfilter, ips, iter);
  query_filter(bloomfilter, ips, iter);

  wrap_fclose(infile);
  bf_free(bloomfilter);
  // free allocated memory
  for (int i = 0; i < iter; i++){
    free(ips[i]);
  }
  free(ips);
  free(line_buffer);

  return 0;
}
