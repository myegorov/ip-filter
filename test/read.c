#define _GNU_SOURCE // for getline()

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "util.h"

void strip_newline(char *str);
char **append(const char *line_buffer, char **ips, size_t iter, size_t *strarray_length);

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

int main(void) {
  static const char *FNAME = "./data/ips.txt";
  FILE *infile = wrap_fopen(FNAME, "r");

  // to store current line from file
  size_t line_length = 80;
  char *line_buffer = wrap_malloc(line_length);

  // initial guess at length of array of strings
  size_t strarray_length = 131072; // 2^17
  char **ips = wrap_malloc(strarray_length * sizeof(char *));
  size_t iter = 0;

  while(getline(&line_buffer, &line_length, infile) != -1){
    strip_newline(line_buffer);
    ips = append(line_buffer, ips, iter, &strarray_length);

    // TODO: insert in Bloom filter

    iter += 1;
  }

  wrap_fclose(infile);

  // free allocated memory
  for (int i = 0; i < iter; i++){
    free(ips[i]);
  }
  free(ips);
  free(line_buffer);

  return 0;
}
