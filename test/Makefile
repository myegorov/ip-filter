TOP := ..
SRC := $(TOP)/src
FNV := $(SRC)/fnv
BITS := $(SRC)/bitarray
BLOOM := $(SRC)/bloom
UTIL := $(SRC)/util

CC	:= gcc
CFLAGS := $(CFLAGS) -I$(UTIL) -I$(FNV) -I$(BITS) -I$(BLOOM) -Wall -std=c99
LDFLAGS := $(LDFLAGS) -lm

all: test.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c
	$(CC) -o test test.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c $(CFLAGS) $(LDFLAGS)

clean:
	@rm ./test

valgrind: all
	valgrind --leak-check=full ./test


.PHONY: all clean valgrind
