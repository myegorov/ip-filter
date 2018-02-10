#include <stdio.h>

// TODO: move declarations to header file
FILE *wrap_fopen(const char *fname, const char *mode);
int wrap_fclose(FILE *f);

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
int wrap_fclose(FILE *f) {
  if(fclose(infile) != 0){
    perror("wrap_fclose");
    exit(EXIT_FAILURE);
  }
  return 0;
}

int main(void) {
  static const char *FNAME = "./data/ips/txt";
  FILE *infile = wrap_fopen(FNAME, "r");

  size_t line_length = 80;
  char *buffer = malloc(line_length);
  while(getline(&buffer, &line_length, infile) != -1){
    // strip newline
    buffer[strcspn(buffer, "\n")] = '\0';
    buffer[strcspn(buffer, "\r\n")] = '\0';

    // TODO: add to query array & insert in Bloom filter
    // TODO: dynamically resize (malloc & realloc) query array (char **ips)
    ;
  }

  free(buffer);
  int close_status = wrap_fclose(infile);

  return 0;
}
