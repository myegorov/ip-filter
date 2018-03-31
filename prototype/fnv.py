'''
64-bit Fowler-Noll-Vo (FNV1a) hash function:
https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function
'''
from sys import getsizeof

FNV_OFFSET_BASIS = 0xcbf29ce484222325
FNV_PRIME = 0x100000001b3

def hash_fnv(num):
    res = FNV_OFFSET_BASIS
    for i in range(getsizeof(num)): # for each byte
        byte_chunk = (num>>(8*i)) & 0xff # extract byte
        res ^= byte_chunk
        res *= FNV_PRIME
    return res % (1<<64)
