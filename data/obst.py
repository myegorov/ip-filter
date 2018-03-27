'''
Compute optimal binary search tree with various weighting functions:
    - equal weights (balanced tree)
    - weights correlated with prefix count
    - weights correlated with prefix IP address space share

Using Knuth's dynamic programming algorithm.
'''

# TODO: construct tree from r matrix
# TODO: output .dot file & tree plot

import os
from sys import maxsize
from conf import *

def weigh_equally(protocol='v4'):
    '''Return equal weights for all represented prefix lengths:
        [(1.0, valid_pref_len), ..., (1.0, valid_pref_len)]
    '''
    filtered = weigh_by_prefix_count(protocol=protocol, skiplines=0)
    return [(1.0, pref_len) for (_,pref_len) in filtered]

def weigh_by_prefix_count(protocol='v4', skiplines=0):
    '''Return weights for all represented prefix lengths by fraction
        of prefixes of that length:
        [(fraction, valid_pref_len), ..., (fraction, valid_pref_len)]
    '''
    with open(os.path.join(TRAFFICDIR, 'ip'+protocol, STATSFILE), 'r') as infile:
        for i in range(skiplines): infile.readline()
        line = infile.readline().strip().split(',')[1:]
        pref_fractions = [float(prefix_len) for prefix_len in line]
        zipped = zip(pref_fractions, list(range(len(pref_fractions))))
        return list(filter(lambda pair: pair[0]>0, zipped))

def weigh_by_prefix_range(protocol='v4'):
    '''Return weights for all represented prefix lengths by fraction
        of IP address space covered by prefixes of that length:
        [(fraction, valid_pref_len), ..., (fraction, valid_pref_len)]
    '''
    return weigh_by_prefix_count(protocol=protocol, skiplines=1)

def _construct_w_tab(weights):
    '''Construct and return upper triangular weight matrix: (n+1) x (n+1)
    '''
    p = [w for w,_ in weights]
    mat = [[0.0 for i in range(len(weights)+1)] for j in range(len(weights)+1)]
    for i in range(len(weights)):
        for j in range(i, len(weights), 1):
            mat[i][j+1] = mat[i][j] + p[j]
    return mat

def construct_tabs(weights):
    '''Construct and return upper triangular weight (w), expected cost (e)
        and optimal subtree root (r) matrices, each (n+1) x (n+1).
    '''
    w = _construct_w_tab(weights)
    # initialize optimal subtree root table (when row == col, None signals to stop iteration)
    r = [[None for i in range(len(weights)+1)] for j in range(len(weights)+1)]
    # initialize expected costs to very large num
    e = [[maxsize for i in range(len(weights)+1)] for j in range(len(weights)+1)]
    for i in range(len(weights)):
        e[i][i] = 0.0
        e[i][i+1] = weights[i][0]
        r[i][i+1] = i
    e[len(e)-1][len(e)-1] = 0.0

    for l in range(len(weights)+1):
        for i in range(len(weights)+1-l):
            j = i + l
            for root in range(i+1, j+1, 1):
                t = e[i][root-1] + e[root][j] + w[i][j]
                if t < e[i][j]:
                    e[i][j] = t
                    r[i][j] = root-1
    return w, e, r


if __name__ == "__main__":
    # print(_construct_w_tab(weights))
    # print(weigh_by_prefix_count(protocol='v6'))
    # print(sum([f for f,_ in weigh_by_prefix_range(protocol='v4')])) # 1.0

    weights = (weigh_equally(protocol='v4'))
    w, e, r = construct_tabs(weights)
    # print(e)
    # print(r)

