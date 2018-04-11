'''driver.py

Conduct experiments to compare linear and guided Bloom filter performance.

Variables:
- linear search
- guided search

Metrics to collect (as a function of IP count in traffic):

- count of BloomFilter.contains() invocations (bf.contains.ncalls)
- count of hash function invocations (hash_fnv.ncalls)
- count of FIB table lookups per IP (fib.__contains__.ncalls)
- number of defaults to linear search (for guided search only, ipfilter._default_to_linear_search.ncalls)

Params to vary:

- IPv4 vs IPv6 (keeping traffic distribution constant, e.g. random traffic over
    total space, or look up prefixes themselves?)
- IPv4 by traffic pattern:
        * traffic randomly distributed over total space
        * traffic correlated with proportion of space covered by prefixes of
            given length (idealized case)
        * traffic correlated with the count of prefixes of given length
- IPv4 keeping traffic constant (random):
        * vary bitarray size (or equivalently by % bits set)
        * vary hash function count

For linear scheme, we expect this to be approximately optimal for the optimal
    BF params (target FPP)?

Reduce to common denominator:
    Contrast size of linear search BF bitarray vs guided BF for same performance
    target, e.g. same count of FIB lookups per IP traffic unit:

        IPs x (matches / IPs) x (FIB lookups / matches) --> FIB lookups
'''

import sys
from mconf import *
for d in [DATADIR]:
    sys.path.append(d)

from utils import compile_fib_table, load_traffic, load_prefixes, prefix_stats
import ipfilter
from obst import *
from fnv import hash_fnv

THROTTLE = 10000 # test with representative but limited amount of traffic

def _common_prep(protocol='v4', traffic_pattern=RANDOM_TRAFFIC):
    fib = compile_fib_table(protocol=protocol)
    traffic = load_traffic(protocol=protocol, typ=RANDOM_TRAFFIC)
    prefixes = load_prefixes(protocol=protocol)
    pref_stats = prefix_stats(prefixes)
    return fib, traffic, pref_stats

def test_traffic_patterns(fib, traffic, pref_stats):
    test_matrix = {
        'v4': [(RANDOM_TRAFFIC, 'random.txt'),
               (PREF_COUNT_TRAFFIC, 'count.txt'),
               (PREF_SPACE_TRAFFIC, 'space.txt')],
        'v6': [(RANDOM_TRAFFIC, 'random.txt')]
    }

    for protocol in test_matrix:
        ## linear tests
        bf_linear, _, _ = ipfilter.build_bloom_filter(
            protocol=protocol, lamda=None, fpp=1e-6, k=None,
            num_bits=None, fib=fib)
        print('linear BF:', bf_linear, '\n')

        ## guided tests
        # build BF
        pass

        for traffic_pattern in test_matrix[protocol]:
            infile, outfile = traffic_pattern

            # record starting ncalls for each function of interest
            # - count of BloomFilter.contains() invocations (bf.contains.ncalls)
            # - count of hash function invocations (hash_fnv.ncalls)
            # - count of FIB table lookups per IP (fib.__contains__.ncalls)
            # - number of defaults to linear search (significant for guided 
            #       search only, ipfilter._default_to_linear_search.ncalls)
            ncontains = bf_linear.contains.ncalls
            nfnv = hash_fnv.ncalls
            nfib = fib.__contains__.ncalls
            ndefault = ipfilter._default_to_linear_search.ncalls
            print('processing %s...' %outfile)
            print(ncontains, nfnv, nfib, ndefault)

            # perform the lookup
            _, _, _ =\
                ipfilter.lookup_in_bloom(bf_linear,
                                         traffic[:THROTTLE],
                                         fib,
                                         maxx=pref_stats['maxx'],
                                         minn=pref_stats['minn'],
                                         protocol=protocol)

            #       record the ending ncalls for each functio of interest
            #       record experiment to file in EXPERIMENTS: header, plot title, xaxis, yaxis, xs, ys
            ncontains = bf_linear.contains.ncalls - ncontains
            nfnv = hash_fnv.ncalls - nfnv
            nfib = fib.__contains__.ncalls - nfib
            ndefault = ipfilter._default_to_linear_search.ncalls - ndefault
            print(ncontains, nfnv, nfib, ndefault)
            input('continue?')

            pass



if __name__ == "__main__":

    fib, traffic, pref_stats = _common_prep(protocol='v4', traffic_pattern=RANDOM_TRAFFIC)
    test_traffic_patterns(fib, traffic, pref_stats)
