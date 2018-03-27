'''
Compute optimal binary search tree with various weighting functions:
    - equal weights (balanced tree)
    - weights correlated with prefix count
    - weights correlated with prefix IP address space share
'''

import os
from conf import *

def weigh_equal(protocol='v4'):
    '''Return equal weights for all represented prefix lengths:
        [(pref_len, 1), ..., (pref_len, 1)]
    '''
    with open(os.path.join(TRAFFICDIR, 'ip'+protocol, STATSFILE), 'r') as infile:
        for arr in arrays:
            outfile.write(','.join([str(elem) for elem in arr]))
            outfile.write('\n')
    # return [1 for i in range(start, end+1, 1)]

def weigh_by_prefix_count(protocol='v4')

if __name__ == "__main__":
    pass
