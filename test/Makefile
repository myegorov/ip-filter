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
	$(CC) -o test test.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c $(CFLAGS) $(LDFLAGS) -g

read: read.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c
	$(CC) -o read read.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c $(CFLAGS) $(LDFLAGS) -g

clean:
	@rm ./test
	@rm ./read

valgrind: all read
	valgrind --tool=memcheck --leak-check=full --show-reachable=yes --num-callers=20 --track-fds=yes ./test
	valgrind --tool=memcheck --leak-check=full --show-reachable=yes --num-callers=20 --track-fds=yes ./read


.PHONY: all clean valgrind
