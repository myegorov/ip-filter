from bitarray import bitarray
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
        self.ba = bitarray(num_bits)
        self.ba.setall(False)

    def __str__(self):
        ''' Print some info for debugging.

            fpp: target false positive rate
            n: number of elements
            k: number of hash functions
            BitArray size
            % of BitArray set
        '''
        res = 'BloomFilter(fpp=%.2f, n=%d, k=%d, ba=(malloc=%.2fMB, length=%db, %%full=%.1f)'\
                %(self.fpp,
                  self.num_elements,
                  self.k,
                  self.ba.buffer_info()[-1]/(1024**2),
                  self.ba.length(),
                  100*self.ba.count()/self.ba.length())
        return res

    def _set_bit(self, ix):
        self.ba[ix] = True
        return True

    def insert(self, key, hashes=[]):
        '''Insert key into Bloom filter. By default using full
        range of hash functions. If hashes is a list/generator
        of hash funcs to use (indices).
        '''
        self._helper(key, lamda=self._set_bit,
                     hashes=hashes,
                     keep_going=True)

    def contains(self, key, hashes=[], keep_going=False):
        '''Return 1 (possibly false positive) or 0.
        '''
        return self._helper(key, lamda=self.ba.__getitem__,
                            hashes=hashes,
                            keep_going=keep_going)


    def _helper(self, key, lamda=None, hashes=[], keep_going=False):
        '''Insert or look up key (int) in Bloom filter using
            hash functions from hashes list.
            If `keep_going` is True, complete all `hashes` and decode the result.
        '''
        if not hashes: return 0
        hash64 = hash_fnv(key)
        h1 = hash64 & 0x00000000FFFFFFFF
        h2 = hash64 & 0xFFFFFFFF00000000
        decode = 0
        size = self.ba.length()
        for i in hashes:
            ix = (h1 + i * h2) % size
            res = lamda(ix)
            if res==False and not keep_going:
                return 0
            decode += int(res)<<(i-hashes[0])
        return decode

if __name__ == "__main__":
    bf = BloomFilter(1e-5, int(1e6), k=10)
    print(bf)

    bf = BloomFilter(1e-6, int(1e6))
    print(bf)

    # insert using only the first hash function
    for i in range(10):
        bf.insert(i, hashes=[0])

    # look up only using the first hash function
    for i in range(15):
        print(i, bf.contains(i, hashes=[0]))

    print('\n---\n')
    bf = BloomFilter(1e-5, int(1e6))
    bf.insert(10, hashes=[7]) # encode start=5, pattern=4
    print(bf.contains(10, hashes=[5,6,7,8,9], keep_going=True)) # => 4
