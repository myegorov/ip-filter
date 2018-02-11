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

simple: simple_query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c
	$(CC) -o simple simple_query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c $(CFLAGS) $(LDFLAGS) -g

clean:
	@rm -f ./unit_test
	@rm -f ./simple

valgrind: all simple
	valgrind --tool=memcheck --leak-check=full --show-reachable=yes --num-callers=20 --track-fds=yes ./unit_test
	valgrind --tool=memcheck --leak-check=full --show-reachable=yes --num-callers=20 --track-fds=yes ./simple


.PHONY: all clean valgrind
