TOP := ..
SRC := $(TOP)/src
FNV := $(SRC)/fnv
BITS := $(SRC)/bitarray

CC	:= gcc
CFLAGS := $(CFLAGS) -I$(FNV) -I$(BITS) -Wall -std=c99

all: test.c $(FNV)/fnv.c $(BITS)/bitarray.c
	$(CC) -o test test.c $(FNV)/fnv.c $(BITS)/bitarray.c $(CFLAGS)

clean:
	@rm ./test

.PHONY: all clean
