'''Expose just the bare minimum of bit operations for Bloom filter.
'''

class BitArray:
    def __init__(self, size, val=0, from_bitstring=None):
        self.val = int(from_bitstring, 2) if from_bitstring is not None else val
        self.size = size

    def __lshift__(self, bits):
        return BitArray(self.size, val=self.val<<bits)

    def __rshift__(self, bits):
        return BitArray(self.size, val=self.val>>bits)

    def __and__(self, num):
        return BitArray(self.size, val=self.val&num)

    def __xor__(self, num):
        return BitArray(self.size, val=self.val^num)

    def __or__(self, num):
        return BitArray(self.size, val=self.val|num)

    def __str__(self):
        return '<'+bin(self.val)[2:]+'>'

    def __repr__(self):
        return 'BitArray(size=%d, from_bitstring=%s)'\
                %(self.size, bin(self.val))

    def set_bit(self, bit):
        if bit >= self.size:
            raise IndexError('Cannot set bit %d in array of size %d' %(bit, self.size))
        self.val |= 1<<bit
        return 1 # default response for consistency with read_bit() API

    def clear_bit(self, bit):
        if bit >= self.size:
            raise IndexError('Cannot clear bit %d in array of size %d' %(bit, self.size))
        self.val &= ~(1<<bit)

    def read_bit(self, bit):
        if bit >= self.size:
            raise IndexError('Cannot read bit %d in array of size %d' %(bit, self.size))
        return (self.val>>bit) & 1

    def count_bits(self):
        return bin(self.val).count('1')

if __name__ == "__main__":
    ba = BitArray(10, from_bitstring='101')
    ba.set_bit(1) # => '111'
    ba.clear_bit(0) # => '110'
    print(ba.read_bit(2)) # => 1
    print(ba.count_bits()) # => 2
    print(ba)
    # print(ba.read_bit(10)) # => IndexError
