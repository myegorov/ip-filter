from bitarray import BitArray
from fnv import hash_fnv
from math import log, ceil

class BloomFilter:
    def __init__(self, fpp, n, k=None):
        ''' Calculate size of bit array, number of hash functions
                (k, unless specified) and initialize the bitarray (ba), 
                given:

            fpp (float): 0.0 <= false positive probability <= 1.0
            n (int): expected number of elements to insert
            k (int, optional): override the number of hash functions to use
        '''
        if k is None: # default case, calculate optimal k
            num_bits = ceil(-n * log(fpp) / ((log(2))**2))
            self.k = ceil((num_bits * log(2)) / n)
        else:
            num_bits = ceil(-(k * n) / (log(1-(fpp)**(1./k))))
            self.k = k
        self.fpp = fpp
        self.num_elements = n
        self.ba = BitArray(num_bits)

    def __str__(self):
        ''' Print some info for debugging.

            fpp: target false positive rate
            n: number of elements
            k: number of hash functions
            BitArray size
            % of BitArray set
        '''
        res = 'BloomFilter(fpp=%0.2f, n=%d, k=%d, ba=BitArray(%d, %%full=%0.1f))'\
                %(self.fpp,
                  self.num_elements,
                  self.k,
                  self.ba.size,
                  100.*self.ba.count_bits()/self.ba.size)
        return res

    def insert(self, key, hashes=None):
        '''Insert key into Bloom filter. By default using full
        range of hash functions. If hashes is a pair
        of indices, will only use the range between hashes[0] and
        hashes[1], inclusive.
        '''
        self._helper(key, lamda=self.ba.set_bit, hashes=hashes)

    def contains(self, key, hashes=None):
        '''Return 1 (possibly false positive) or 0.
        '''
        return self._helper(key, lamda=self.ba.read_bit, hashes=hashes)


    def _helper(self, key, lamda=None, hashes=None):
        '''Insert or look up key (int) in Bloom filter using
            hash functions hashes[0] to hashes[k-1] inclusive (by default).
        '''
        if hashes is None:
            hashes = (0, self.k-1)
        hash64 = hash_fnv(key)
        h1 = hash64 & 0x00000000FFFFFFFF
        h2 = hash64 & 0xFFFFFFFF00000000
        for i in range(hashes[0], hashes[1]+1, 1):
            ix = (h1 + i * h2) % self.ba.size
            res = lamda(ix)
            if res==0:
                return 0
        return 1

if __name__ == "__main__":
    bf = BloomFilter(1e-5, int(1e6), k=10)
    print(bf)

    bf = BloomFilter(1e-6, int(1e6))
    print(bf)

    # insert using only the first hash function
    for i in range(10):
        bf.insert(i, hashes=(0,0))

    # look up only using the first hash function
    for i in range(15):
        print(i, bf.contains(i, hashes=(0,0)))
