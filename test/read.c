#include <stdio.h>
#include <stdlib.h>
#include "util.h"

int main(void) {
  static const char *FNAME = "./data/ips/txt";
  FILE *infile = wrap_fopen(FNAME, "r");

  // to store current line from file
  size_t line_length = 80;
  char *line_buffer = wrap_malloc(line_length);

  // hypothetical length of array of strings (may change)
  size_t strarray_length = 131072; // 2^17
  char **ips = (char **)wrap_malloc(strarray_length * sizeof(char *));
  size_t iter = 0;

  // TODO: extract to a separate function?
  while(getline(&line_buffer, &line_length, infile) != -1){
    // strip newline
    line_buffer[strcspn(line_buffer, "\n")] = '\0';
    line_buffer[strcspn(line_buffer, "\r\n")] = '\0';

    // dynamically resize ip array
    if (iter >= strarray_length) {
      ips = (char **)wrap_realloc(ips, &strarray_length);
    }
    // allocate space for ip
    ips[iter] = wrap_malloc(strlen(line_buffer)+1);
    strcpy(ips[iter], line_buffer);

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
