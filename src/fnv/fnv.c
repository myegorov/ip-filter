#include "fnv.h"

uint64_t hash_fnv(const char *str) {
    uint64_t hash = FNV_OFFSET_BASIS;
    for (unsigned char *p=(unsigned char *)str;*p!='\0';++p) {
        hash ^= *p;
        hash *= FNV_PRIME;
    }
    return hash;
}
