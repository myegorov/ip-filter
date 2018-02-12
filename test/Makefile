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

no-prefetch: query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c
	$(CC) -o no_prefetch query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c $(CFLAGS) $(LDFLAGS) -g -O3 -DNOPREFETCH

prefetch: query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c
	$(CC) -o prefetch query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c $(CFLAGS) $(LDFLAGS) -g -O3 -DPREFETCH

pseudo: query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c
	$(CC) -o pseudo query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c $(CFLAGS) $(LDFLAGS) -g -O3 -DPSEUDO

idle: query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c
	$(CC) -o idle query.c $(UTIL)/util.c $(FNV)/fnv.c $(BITS)/bitarray.c $(BLOOM)/bloom.c $(CFLAGS) $(LDFLAGS) -g -O3 -DIDLE


clean:
	@rm -f ./unit_test
	@rm -f ./no_prefetch
	@rm -f ./prefetch
	@rm -f ./pseudo
	@rm -f ./idle

valgrind: all no-prefetch prefetch
	valgrind --tool=memcheck --leak-check=full --show-reachable=yes --num-callers=20 --track-fds=yes ./unit_test
	valgrind --tool=memcheck --leak-check=full --show-reachable=yes --num-callers=20 --track-fds=yes ./no_prefetch
	valgrind --tool=memcheck --leak-check=full --show-reachable=yes --num-callers=20 --track-fds=yes ./prefetch


.PHONY: all clean valgrind
