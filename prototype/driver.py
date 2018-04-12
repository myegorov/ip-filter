'''driver.py

Conduct experiments to compare linear and guided Bloom filter performance.

Variables:
+ linear search
+ guided search

Metrics to collect (as a function of IP count in traffic):
+ count of BloomFilter lookup loops (bf._register.ncalls)
+ count of hash function invocations (hash_fnv.ncalls)
+ count of FIB table lookups per IP (fib.__contains__.ncalls)
+ number of defaults to linear search (for guided search only, ipfilter._default_to_linear_search.ncalls)

Params to vary:
+ IPv4 by traffic pattern:
        * traffic randomly distributed over total space
        * traffic correlated with proportion of space covered by prefixes of
            given length (idealized case)
        * traffic correlated with the count of prefixes of given length
+ IPv4 vs IPv6 (keeping traffic distribution constant, e.g. random traffic over
    total space, and use the other extreme of prefixes as traffic --
    former case no FIB lookups, latter case plenty of FIB lookups)
+ IPv4 keeping traffic constant (random):
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
import os
from mconf import *
for d in [DATADIR]:
    sys.path.append(d)

from utils import compile_fib_table, load_traffic, load_prefixes, prefix_stats
import ipfilter
from obst import *
from fnv import hash_fnv
from plot import plot_vbar, plot_scatter

THROTTLE = 100000 # test with representative but limited amount of traffic

# "optimal" guided Bloom settings, TODO: tune
K = 20
BITARR_SIZE=215480360

def _common_prep(protocol='v4', traffic_pattern=RANDOM_TRAFFIC):
    fib = compile_fib_table(protocol=protocol)
    traffic = load_traffic(protocol=protocol, typ=traffic_pattern)
    prefixes = load_prefixes(protocol=protocol)
    pref_stats = prefix_stats(prefixes)
    return fib, traffic, pref_stats

def _lookup_wrapper(bf, traffic, fib, pref_stats, protocol, bst=None, typ='linear'):
    # perform the lookup
    if typ == 'linear':
        _, _, _ = ipfilter.lookup_in_bloom(bf,
                                            traffic[:THROTTLE],
                                            fib,
                                            maxx=pref_stats['maxx'],
                                            minn=pref_stats['minn'],
                                            protocol=protocol)
    else:
        _, _, _ = ipfilter.lookup_in_bloom(bf,
                                            traffic[:THROTTLE],
                                            fib,
                                            root=bst,
                                            maxx=pref_stats['maxx'],
                                            minn=pref_stats['minn'],
                                            ix2len=pref_stats['ix2len'],
                                            protocol=protocol)



def test_traffic_patterns(fpp_linear=1e-6, num_bits_guided=BITARR_SIZE, k_guided=K):
    test_matrix = {
        # TODO: try also using weigh_equally throughout
        'v4': [(RANDOM_TRAFFIC, weigh_equally, 'random.txt'),
               # (PREF_COUNT_TRAFFIC, weigh_by_prefix_count, 'count.txt'),
               (PREF_COUNT_TRAFFIC, weigh_equally, 'count.txt'),
               # (PREF_SPACE_TRAFFIC, weigh_by_prefix_range, 'space.txt'),
               (PREF_SPACE_TRAFFIC, weigh_equally, 'space.txt'),
               (PREFIX_FILE, weigh_equally, 'prefixTraffic.txt')], # try also weigh_by_prefix_count?
        'v6': [(RANDOM_TRAFFIC, weigh_equally, 'random.txt'),
               (PREFIX_FILE, weigh_equally, 'prefixTraffic.txt')] # try also weigh_by_prefix_count?
    }

    for protocol in test_matrix:
        print('\nStarting on %s protocol\n' %protocol)
        fib = compile_fib_table(protocol=protocol)
        prefixes = load_prefixes(protocol=protocol)
        pref_stats = prefix_stats(prefixes)

        for traffic_pattern in test_matrix[protocol]:
            infile, lamda, outfile = traffic_pattern
            print('processing ..._%s...' %outfile)
            traffic = load_traffic(protocol=protocol, typ=infile)

            ## LINEAR
            bf_linear, _, _ = ipfilter.build_bloom_filter(
                protocol=protocol, lamda=None, fpp=fpp_linear, k=None,
                num_bits=None, fib=fib)

            # record starting ncalls for each function of interest
            ncontains = bf_linear._register.ncalls
            nfnv = hash_fnv.ncalls
            nfib = fib.__contains__.ncalls
            ndefault = ipfilter._default_to_linear_search.ncalls

            # perform the lookup
            _lookup_wrapper(bf_linear, traffic, fib, pref_stats, protocol, bst=None, typ='linear')

            # record the ending ncalls for each function of interest
            ncontains = (bf_linear._register.ncalls - ncontains)/THROTTLE
            nfnv = (hash_fnv.ncalls - nfnv)/THROTTLE
            nfib = (fib.__contains__.ncalls - nfib)/THROTTLE
            ndefault = (ipfilter._default_to_linear_search.ncalls - ndefault)/THROTTLE

            # record experiment to file in EXPERIMENTS: header, plot title, xaxis, yaxis, xs, ys, misc info
            with open(os.path.join(EXPERIMENTS, 
                                   'linear_traffic_'+protocol+'_'+outfile), 
                      'w') as out:
                lines = ["test_traffic_patterns(): using 'optimal' params for linear, invocations of funcs,xs=[bf._register(), hash_fnv(), fib.__contains__(), ipfilter._default_to_linear_search], yaxis=ncalls"] # header
                lines.append('Linear search: lookup/hashing stats') # plot title
                lines.append('Function') # xaxis title
                lines.append('Count of invocations') # yaxis title
                lines.append('bitarray lookup, hash(), FIB lookup, defaults') # xs
                lines.append('%.2f, %.2f, %.2f, %.2f' %(ncontains, nfnv, nfib, ndefault)) # ys
                lines.append('linear BF: %s' %bf_linear) # any extra info
                out.write('\n'.join(lines))

            # plot
            ys_linear = [ncontains, nfnv, nfib, ndefault]

            ## GUIDED
            # use hand tuned params
            bf_guided, bst, count_bmp = ipfilter.build_bloom_filter(
                protocol=protocol, lamda=lamda, fpp=None, k=k_guided,
                num_bits=num_bits_guided, fib=fib)

            # record starting ncalls for each function of interest
            ncontains = bf_guided._register.ncalls
            nfnv = hash_fnv.ncalls
            nfib = fib.__contains__.ncalls
            ndefault = ipfilter._default_to_linear_search.ncalls

            # perform the lookup
            _lookup_wrapper(bf_guided, traffic, fib, pref_stats, protocol,
                            bst=bst, typ='guided')

            # record the ending ncalls for each function of interest
            ncontains = (bf_guided._register.ncalls - ncontains)/THROTTLE
            nfnv = (hash_fnv.ncalls - nfnv)/THROTTLE
            nfib = (fib.__contains__.ncalls - nfib)/THROTTLE
            ndefault = (ipfilter._default_to_linear_search.ncalls - ndefault)/THROTTLE

            # record experiment to file in EXPERIMENTS: header, plot title, xaxis, yaxis, xs, ys, misc info
            with open(os.path.join(EXPERIMENTS, 
                                   'guided_traffic_'+protocol+'_'+outfile), 
                      'w') as out:
                lines = ["test_traffic_patterns(): using 'hand tuned' params for guided, invocations of funcs,xs=[bf.contains(), hash_fnv(), fib.__contains__(), ipfilter._default_to_linear_search], yaxis=ncalls"] # header
                lines.append('Guided search: stats per packet') # plot title
                lines.append('Function') # xaxis title
                lines.append('Count of invocations') # yaxis title
                lines.append('bitarray lookup, hash(), FIB lookup, defaults') # xs
                lines.append('%.2f, %.2f, %.2f, %.2f' %(ncontains, nfnv, nfib, ndefault)) # ys
                lines.append('guided BF: %s' %bf_guided) # any extra info
                out.write('\n'.join(lines))


            # plot
            fname, _ = os.path.splitext(outfile)
            xs = ['bit lookups', 'hash()', 'FIB lookups', 'defaults']
            ys_guided = [ncontains, nfnv, nfib, ndefault]
            ofile = 'traffic_'+protocol+'_'+fname+'.svg'
            title = 'Count by metric: %s-type traffic' %fname
            plot_vbar(xs, [ys_linear, ys_guided], outfile=ofile, title=title)

    print('\n\nAll done!')

def test_bitarray_size(fib, traffic, pref_stats):
    ''' vary bitarray size (or equivalently by % bits set)
    '''
    print('\n\ntest_bitarray_size()\n\n')
    test_matrix = {
        'linear': [round(BITARR_SIZE * 10**factor) for factor in range(-2,3,1)],
        'guided': [round(BITARR_SIZE * 10**factor) for factor in range(-2,3,1)]
    }
    protocol='v4'
    res = {}

    for typ in test_matrix:
        print('\nStarting on %s\n' %typ)
        res[typ] = {'percent_full': [],
                    'ncalls': [],
                    'bf':[]} # list of tuples

        for bitarray_size in test_matrix[typ]:
            if typ == 'linear':
                ## LINEAR
                bf_linear, _, _ = ipfilter.build_bloom_filter(
                    protocol=protocol, lamda=None, fpp=None, k=K,
                    num_bits=bitarray_size, fib=fib)
                res[typ]['percent_full'].append(100*bf_linear.ba.count()/bf_linear.ba.length())
                res[typ]['bf'].append(str(bf_linear))
                print(bf_linear)

                # record starting ncalls for each function of interest
                ncontains = bf_linear._register.ncalls
                nfnv = hash_fnv.ncalls
                nfib = fib.__contains__.ncalls
                ndefault = ipfilter._default_to_linear_search.ncalls

                # perform the lookup
                _lookup_wrapper(bf_linear, traffic, fib, pref_stats, protocol, bst=None, typ='linear')

                # record the ending ncalls for each function of interest
                ncontains = (bf_linear._register.ncalls - ncontains)/THROTTLE
                nfnv = (hash_fnv.ncalls - nfnv)/THROTTLE
                nfib = (fib.__contains__.ncalls - nfib)/THROTTLE
                ndefault = (ipfilter._default_to_linear_search.ncalls - ndefault)/THROTTLE

                res[typ]['ncalls'].append((ncontains, nfnv, nfib, ndefault))
            else:
                ## GUIDED
                # use hand tuned params
                bf_guided, bst, count_bmp = ipfilter.build_bloom_filter(
                    protocol=protocol, lamda=weigh_equally, fpp=None, k=K,
                    num_bits=bitarray_size, fib=fib)
                res[typ]['percent_full'].append(100*bf_guided.ba.count()/bf_guided.ba.length())
                res[typ]['bf'].append(str(bf_guided))
                print(bf_guided)

                # record starting ncalls for each function of interest
                ncontains = bf_guided._register.ncalls
                nfnv = hash_fnv.ncalls
                nfib = fib.__contains__.ncalls
                ndefault = ipfilter._default_to_linear_search.ncalls

                # perform the lookup
                _lookup_wrapper(bf_guided, traffic, fib, pref_stats, protocol,
                                bst=bst, typ='guided')

                # record the ending ncalls for each function of interest
                ncontains = (bf_guided._register.ncalls - ncontains)/THROTTLE
                nfnv = (hash_fnv.ncalls - nfnv)/THROTTLE
                nfib = (fib.__contains__.ncalls - nfib)/THROTTLE
                ndefault = (ipfilter._default_to_linear_search.ncalls - ndefault)/THROTTLE

                res[typ]['ncalls'].append((ncontains, nfnv, nfib, ndefault))

    # record experiment to file in EXPERIMENTS: header, plot title, xaxis, yaxis, xs, ys, misc info
    with open(os.path.join(EXPERIMENTS, 
                        'linear_bitarraySize_v4_random.txt'),
            'w') as out:
        lines = ["test_bitarray_size(): vary bitarray size, keeping k constant, for linear, invocations of funcs,xs=[bf._register(), hash_fnv(), fib.__contains__(), ipfilter._default_to_linear_search], yaxis=ncalls"] # header
        lines.append('Linear search: lookup/hashing stats') # plot title
        lines.append('Percent full') # xaxis title
        lines.append('Count of invocations') # yaxis title
        lines.append(';'.join([str(val) for val in res['linear']['percent_full']])) # xs
        lines.append(';'.join(['(%.2f, %.2f, %.2f, %.2f)' %quad for quad in res['linear']['ncalls']])) # ys
        lines.append(';'.join(res['linear']['bf'])) # any extra info
        out.write('\n'.join(lines))

    # record experiment to file in EXPERIMENTS: header, plot title, xaxis, yaxis, xs, ys, misc info
    with open(os.path.join(EXPERIMENTS,
                        'guided_bitarraySize_v4_random.txt'),
            'w') as out:
        lines = ["test_bitarray_size(): vary bitarray size, keeping k constant, for guided, invocations of funcs,xs=[bf._register(), hash_fnv(), fib.__contains__(), ipfilter._default_to_linear_search], yaxis=ncalls"] # header
        lines.append('Guided search: lookup/hashing stats') # plot title
        lines.append('Percent full') # xaxis title
        lines.append('Count of invocations') # yaxis title
        lines.append(';'.join([str(val) for val in res['guided']['percent_full']])) # xs
        lines.append(';'.join(['(%.2f, %.2f, %.2f, %.2f)' %quad for quad in res['guided']['ncalls']])) # ys
        lines.append(';'.join(res['guided']['bf'])) # any extra info
        out.write('\n'.join(lines))

    # plot
    seqs = ['bit lookups', 'hash()', 'FIB lookups', 'defaults']
    ofile = 'bitarraySize_'+protocol+'_random.svg'
    title = 'Count by metric: bitarray size'
    xlabel = '% bitarray full'
    ylabel = 'count'
    plot_scatter(seqs, res, ofile, title, xlabel, ylabel, key='percent_full')

    print('\n\nAll done!')

def test_num_hash_funcs(fib, traffic, pref_stats):
    '''Vary hash function count
    '''
    print('\n\ntest_num_hash_funcs()\n\n')
    test_matrix = {
        'linear': list(range(7,25,1)),
        'guided': list(range(7,25,1))
    }
    protocol='v4'
    res = {}

    for typ in test_matrix:
        print('\nStarting on %s\n' %typ)
        res[typ] = {'k': [],
                    'ncalls': [],
                    'bf':[]} # list of tuples

        for k_size in test_matrix[typ]:
            if typ == 'linear':
                ## LINEAR
                bf_linear, _, _ = ipfilter.build_bloom_filter(
                    protocol=protocol, lamda=None, fpp=None, k=k_size,
                    num_bits=round(BITARR_SIZE/10), fib=fib)
                res[typ]['k'].append(k_size)
                res[typ]['bf'].append(str(bf_linear))
                print(bf_linear)

                # record starting ncalls for each function of interest
                ncontains = bf_linear._register.ncalls
                nfnv = hash_fnv.ncalls
                nfib = fib.__contains__.ncalls
                ndefault = ipfilter._default_to_linear_search.ncalls

                # perform the lookup
                _lookup_wrapper(bf_linear, traffic, fib, pref_stats, protocol, bst=None, typ='linear')

                # record the ending ncalls for each function of interest
                ncontains = (bf_linear._register.ncalls - ncontains)/THROTTLE
                nfnv = (hash_fnv.ncalls - nfnv)/THROTTLE
                nfib = (fib.__contains__.ncalls - nfib)/THROTTLE
                ndefault = (ipfilter._default_to_linear_search.ncalls - ndefault)/THROTTLE

                res[typ]['ncalls'].append((ncontains, nfnv, nfib, ndefault))
            else:
                ## GUIDED
                # use hand tuned params
                bf_guided, bst, count_bmp = ipfilter.build_bloom_filter(
                    protocol=protocol, lamda=weigh_equally, fpp=None, k=k_size,
                    num_bits=BITARR_SIZE, fib=fib)
                res[typ]['k'].append(k_size)
                res[typ]['bf'].append(str(bf_guided))
                print(bf_guided)

                # record starting ncalls for each function of interest
                ncontains = bf_guided._register.ncalls
                nfnv = hash_fnv.ncalls
                nfib = fib.__contains__.ncalls
                ndefault = ipfilter._default_to_linear_search.ncalls

                # perform the lookup
                _lookup_wrapper(bf_guided, traffic, fib, pref_stats, protocol,
                                bst=bst, typ='guided')

                # record the ending ncalls for each function of interest
                ncontains = (bf_guided._register.ncalls - ncontains)/THROTTLE
                nfnv = (hash_fnv.ncalls - nfnv)/THROTTLE
                nfib = (fib.__contains__.ncalls - nfib)/THROTTLE
                ndefault = (ipfilter._default_to_linear_search.ncalls - ndefault)/THROTTLE

                res[typ]['ncalls'].append((ncontains, nfnv, nfib, ndefault))

    # record experiment to file in EXPERIMENTS: header, plot title, xaxis, yaxis, xs, ys, misc info
    with open(os.path.join(EXPERIMENTS, 
                        'linear_numHashFuncs_v4_random.txt'),
            'w') as out:
        lines = ["test_num_hash_funcs(): vary num hash funcs, keeping bitarray size constant, for linear, invocations of funcs,xs=[bf._register(), hash_fnv(), fib.__contains__(), ipfilter._default_to_linear_search], yaxis=ncalls"] # header
        lines.append('Linear search: lookup/hashing stats') # plot title
        lines.append('Num hash funcs') # xaxis title
        lines.append('Count of invocations') # yaxis title
        lines.append(';'.join([str(val) for val in res['linear']['k']])) # xs
        lines.append(';'.join(['(%.2f, %.2f, %.2f, %.2f)' %quad for quad in res['linear']['ncalls']])) # ys
        lines.append(';'.join(res['linear']['bf'])) # any extra info
        out.write('\n'.join(lines))

    with open(os.path.join(EXPERIMENTS, 
                        'guided_numHashFuncs_v4_random.txt'),
            'w') as out:
        lines = ["test_num_hash_funcs(): vary num hash funcs, keeping bitarray size constant, for guided, invocations of funcs,xs=[bf._register(), hash_fnv(), fib.__contains__(), ipfilter._default_to_linear_search], yaxis=ncalls"] # header
        lines.append('Linear search: lookup/hashing stats') # plot title
        lines.append('Num hash funcs') # xaxis title
        lines.append('Count of invocations') # yaxis title
        lines.append(';'.join([str(val) for val in res['guided']['k']])) # xs
        lines.append(';'.join(['(%.2f, %.2f, %.2f, %.2f)' %quad for quad in res['guided']['ncalls']])) # ys
        lines.append(';'.join(res['guided']['bf'])) # any extra info
        out.write('\n'.join(lines))

    # plot
    seqs = ['bit lookups', 'hash()', 'FIB lookups', 'defaults']
    ofile = 'numHashFuncs_'+protocol+'_random.svg'
    title = 'Count by metric: number of hash funcs'
    xlabel = 'count of hash funcs'
    ylabel = 'count'
    plot_scatter(seqs, res, ofile, title, xlabel, ylabel, key='k', x_logscale=False)

    print('\n\nAll done!')

if __name__ == "__main__":
    # tests
    test_traffic_patterns()
    fib, traffic, pref_stats = _common_prep(protocol='v4', traffic_pattern=RANDOM_TRAFFIC)
    test_bitarray_size(fib, traffic, pref_stats)
    test_num_hash_funcs(fib, traffic, pref_stats)
