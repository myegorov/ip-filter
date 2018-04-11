'''
64-bit Fowler-Noll-Vo (FNV1a) hash function:
https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function
'''
from sys import getsizeof
from profiler import count_invocations

FNV_OFFSET_BASIS = 0xcbf29ce484222325
FNV_PRIME = 0x100000001b3

@count_invocations
def hash_fnv(obj):
    '''Returns a hash of obj.
    '''
    if not isinstance(obj, int):
        obj = int.from_bytes(bytes(str(obj), encoding='utf-8'), byteorder='big')

    res = FNV_OFFSET_BASIS
    for i in range(getsizeof(obj)): # for each byte
        byte_chunk = (obj>>(8*i)) & 0xff # extract byte
        res ^= byte_chunk
        res *= FNV_PRIME
    return res % (1<<64)

if __name__ == "__main__":
    print(hash_fnv(123))
    print(hash_fnv((1232342342432424242424234234234, 12)))
    print(hash_fnv('abc'))
    print(hash_fnv((121,'joe')))
