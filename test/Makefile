TOP := ..
SRC := $(TOP)/src
FNV := $(SRC)/fnv

CC	:= gcc
CFLAGS := $(CFLAGS) -I$(FNV) -Wall -std=c99

all: test.c $(FNV)/fnv.c
	$(CC) -o test test.c $(FNV)/fnv.c $(CFLAGS)

clean: test
	rm ./test

.PHONY: all clean
