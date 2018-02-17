TOP := ..
SRC := $(TOP)/src
FNV := $(SRC)/fnv
BITS := $(SRC)/bitarray
BLOOM := $(SRC)/bloom
UTIL := $(SRC)/util

CC	:= gcc
CFLAGS := $(CFLAGS) -I$(UTIL) -I$(FNV) -I$(BITS) -I$(BLOOM) -Wall -std=c99
LDFLAGS := $(LDFLAGS) -lm

all: unit_test.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c
	$(CC) -o unit_test unit_test.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c $(CFLAGS) $(LDFLAGS) -g

clean:
	@rm -f ./unit_test

valgrind: all no-prefetch prefetch
	valgrind --tool=memcheck --leak-check=full --show-reachable=yes --num-callers=20 --track-fds=yes ./unit_test

.PHONY: all clean valgrind
