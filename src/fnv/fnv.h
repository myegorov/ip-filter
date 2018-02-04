/*
 * 64-bit Fowler-Noll-Vo (FNV1a) hash function:
 * https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function
 *
 */

#ifndef FNV
#define FNV

#include <stdint.h>

#define FNV_OFFSET_BASIS 0xcbf29ce484222325
#define FNV_PRIME 0x100000001b3

uint64_t hash_fnv(const char *str);
#endif
