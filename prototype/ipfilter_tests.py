'''
unit test ipfilter.py

'''
import sys
from mconf import *
for d in [DATADIR]:
    sys.path.append(d)

from utils import compile_fib_table, load_traffic, encode_ip_prefix_pair,\
                    load_prefixes, prefix_stats
import ipfilter
import netaddr as net
from obst import *

FPP = 1e-6 # false positive probability setting for Bloom filter

def _common_prep(protocol='v4', typ=RANDOM_TRAFFIC):
    fib = compile_fib_table(protocol='v4')
    traffic = load_traffic(protocol='v4', typ=RANDOM_TRAFFIC)
    prefixes = load_prefixes(protocol=protocol)
    pref_stats = prefix_stats(prefixes)
    return fib, traffic, pref_stats

def test__choose_hash_funcs():
    assert list(ipfilter._choose_hash_funcs(start=0, end=10))\
            == list(range(10))
    assert list(ipfilter._choose_hash_funcs(start=3, end=4))\
            == [3]
    assert list(ipfilter._choose_hash_funcs(start=5, pattern=4))\
            == [7] # 100_ _ _ _ _

def test__build_linear_bloom(protocol='v4'):
    prefixes = load_prefixes(protocol=protocol, infile='bgptable_tests.txt')
    pref_stats = prefix_stats(prefixes)

    # (1) test passing FPP as param
    bf1, prefixes, _ = ipfilter._build_linear_bloom(pref_stats,\
                                FPP, None, None,  protocol=protocol)
    assert bf1.num_elements==8 and bf1.fpp==FPP and bf1.k==21\
            and bf1.ba.length()==231
    _are_in_filter(prefixes['prefixes'], bf1,
                   hash_funcs=list(range(bf1.k)), protocol=protocol)

    # (2) test passing k hash funcs as param (also requires n, FPP)
    bf2, prefixes, _ = ipfilter._build_linear_bloom(pref_stats,\
                                FPP, 10, None,  protocol=protocol)
    assert bf2.num_elements==8 and bf2.fpp==FPP and bf2.k==10\
            and bf2.ba.length()==277
    _are_in_filter(prefixes['prefixes'], bf2, 
                   hash_funcs=list(range(bf2.k)), protocol=protocol)

    # (3) test passing bitarray size and k as params (also requires n)
    bf3, prefixes, _ = ipfilter._build_linear_bloom(pref_stats,\
                                None, 1, 1000, protocol=protocol)
    assert bf3.num_elements==8 and round(bf3.fpp)==-1 and bf3.k==1\
            and bf3.ba.length()==1000
    _are_in_filter(prefixes['prefixes'], bf3, 
                   hash_funcs=list(range(bf3.k)), protocol=protocol)

    # (4) test false positive rate for default BF with FPP param
    fpp = 1e-9
    # bf, prefixes, _ = ipfilter._build_linear_bloom(pref_stats,\
    #                             None, 4, 100002,  protocol=protocol)
    bf, prefixes, _ = ipfilter._build_linear_bloom(pref_stats,\
                                fpp, None, None,  protocol=protocol)
    assert bf.num_elements==8 and bf.fpp==fpp and bf.k==30\
            and bf.ba.length()==346

    # ideally, fpp_count should be 1e-6, true_negative_count should be ~1e6
    # unfortunately, it'll be orders of magnitude times more
    pseudo_ips = zip(list(range(int(1e6))), [0] * int(1e6))
    fpp_count, true_negative_count = _are_in_filter(pseudo_ips,
                                                    bf,
                                                    hash_funcs=list(range(bf.k)),
                                                    protocol=protocol,
                                                    err_on_failure=False)
    print('--> Linear Bloom:')
    print('fpp rate: %.7f' %(fpp_count/int(1e6)))
    print('true_negative_rate: %.7f' %(true_negative_count/int(1e6)))
    assert fpp_count + true_negative_count == int(1e6)

def _are_in_filter(prefixes, bf, hash_funcs=[1], protocol='v4',
                   err_on_failure=True):
    '''Test that prefixes are found in bf using hash_funcs
    '''
    # these are only used to test for fpp
    true_negative_count, fpp_count = 0, 0

    for pair in prefixes:
        key = encode_ip_prefix_pair(*pair, protocol)
        if not bf.contains(key, hashes=hash_funcs):
            if err_on_failure:
                raise Exception("test_in_bf() didn't find ip: " + str(pair))
            else:
                true_negative_count += 1
        else:
            fpp_count += 1
    return fpp_count, true_negative_count


def test__find_bmp(protocol='v4'):
    fib = compile_fib_table(protocol=protocol, infile='bgptable_tests.txt')
    prefixes = load_prefixes(protocol=protocol, infile='bgptable_tests.txt')
    pref_stats = prefix_stats(prefixes)

    # context: 3221225472 9 192.0.0.0/9 is in prefixes
    # context: look up BMP for 192.0.0.0/22
    # expect 9 as BMP
    ip, preflen22 = 3221225472, 22
    # confirm the prefix with length 9 is in BF
    bf, prefixes, _ = ipfilter._build_linear_bloom(pref_stats,\
                                FPP, None, None,  protocol=protocol)
    ip9 = encode_ip_prefix_pair(ip, 9, protocol)
    assert ip9 in fib
    assert bf.contains(ip9, hashes=list(range(bf.k))) != 0

    # now test _find_bmp(), starting with length 21 down
    bmp = ipfilter._find_bmp(ip, preflen22-1, fib,
                    pref_stats['minn'], pref_stats['len2ix'],
                    protocol)
    assert bmp == pref_stats['len2ix'][9]

    # now test with some random prefix
    assert ipfilter._find_bmp(int(net.IPAddress('128.1.4.2')), 24, fib,
                              pref_stats['minn'],
                              pref_stats['len2ix'],
                              protocol)\
            == 0

def _pattern_insert(protocol='v4', bf=None):
    '''Test encoding patterns in a Bloom filter.
    '''
    if bf is None:
        prefixes = load_prefixes(protocol=protocol, infile='bgptable_tests.txt')
        pref_stats = prefix_stats(prefixes)

        # with "optimal" Bloom filter encoding doesn't work: not sparse enough
        # test passing bitarray size and k as params (also requires n)
        # NOTE: using k = 1
        bf, prefixes, _ = ipfilter._build_linear_bloom(pref_stats,\
                                None, 1, 1000, protocol=protocol)

    # # make sure the filter is sparse
    # print(bf)

    ip = 3221225472
    ip9 = encode_ip_prefix_pair(ip, 9, protocol)
    assert bf.contains(ip9, hashes=list(range(bf.k))) != 0

    # assert (bf.contains(ip9,
    #                   hashes=list(range(bf.k)),
    #                   keep_going=True)) == 1

    ip22 = encode_ip_prefix_pair(ip, 22, protocol)
    bf.insert(ip22, hashes=ipfilter._choose_hash_funcs(3, pattern=0))
    # bf.insert(ip9, hashes=ipfilter._choose_hash_funcs(3, pattern=16))

    assert bf.contains(ip22,
                      hashes=ipfilter._choose_hash_funcs(3, end=3+5),
                      keep_going=True) == 0

def test__build_guided_bloom(protocol='v4'):
    fib = compile_fib_table(protocol=protocol, infile='bgptable_tests.txt')
    prefixes = load_prefixes(protocol=protocol, infile='bgptable_tests.txt')
    pref_stats = prefix_stats(prefixes)

    bst = obst(protocol, weigh_equally)
    bf, prefixes, bst, count_bmp = ipfilter._build_guided_bloom(
            # pref_stats, FPP, None, None, bst, fib, protocol=protocol) # optimal filter isn't sparse enough
            pref_stats, None, 1, 1000, bst, fib, protocol=protocol)

    # print(bf)
    # print(count_bmp)

    # (0) test that we can encode things in sparse guided BF
    _pattern_insert(protocol, bf)

    # test same schemes as for linear BF
    # (1) test passing FPP as param
    bf1, prefixes, _, _ = ipfilter._build_guided_bloom(
                    pref_stats, FPP, None, None, bst, fib, protocol=protocol)
    assert bf1.num_elements==8 and bf1.fpp==FPP and bf1.k==21\
            and bf1.ba.length()==231
    _are_in_filter(prefixes['prefixes'], bf1,
                   hash_funcs=list(range(bf1.k)), protocol=protocol)

    # (2) test passing k hash funcs as param (also requires n, FPP)
    bf2, prefixes, _, _ = ipfilter._build_guided_bloom(
                    pref_stats, FPP, 10, None, bst, fib, protocol=protocol)
    assert bf2.num_elements==8 and bf2.fpp==FPP and bf2.k==10\
            and bf2.ba.length()==277
    _are_in_filter(prefixes['prefixes'], bf2,
                   hash_funcs=list(range(bf2.k)), protocol=protocol)

    # (3) test passing bitarray size and k as params (also requires n)
    bf3, prefixes, _, _ = ipfilter._build_guided_bloom(pref_stats,\
                                None, 1, 1000, bst, fib, protocol=protocol)
    assert bf3.num_elements==8 and round(bf3.fpp)==-1 and bf3.k==1\
            and bf3.ba.length()==1000
    _are_in_filter(prefixes['prefixes'], bf3,
                   hash_funcs=list(range(bf3.k)), protocol=protocol)

    # (4) test false positive rate for default BF with FPP param
    fpp = 1e-9
    # bf, prefixes, _ = ipfilter._build_guided_bloom(pref_stats,\
    #                             None, 4, 100002,  protocol=protocol)
    bf, prefixes, _, _ = ipfilter._build_guided_bloom(pref_stats,\
                                fpp, None, None, bst, fib, protocol=protocol)
    assert bf.num_elements==8 and bf.fpp==fpp and bf.k==30\
            and bf.ba.length()==346

    # ideally, fpp_count should be 1e-6, true_negative_count should be ~1e6
    # unfortunately, it'll be orders of magnitude times more
    pseudo_ips = zip(list(range(int(1e6))), [0] * int(1e6))
    fpp_count, true_negative_count = _are_in_filter(pseudo_ips,
                                                    bf,
                                                    hash_funcs=list(range(bf.k)),
                                                    protocol=protocol,
                                                    err_on_failure=False)
    print('--> guided Bloom')
    print('fpp rate: %.7f' %(fpp_count/int(1e6)))
    print('true_negative_rate: %.7f' %(true_negative_count/int(1e6)))
    assert fpp_count + true_negative_count == int(1e6)

def _lookup_item_in_fib(fib, ip, maxx, minn, protocol='v4'):
    max_shift = ipfilter.NUMBITS[protocol]

    for pref_len in range(maxx, minn-1, -1):
        mask = ((1<<max_shift) - 1) << (max_shift-pref_len)
        test_pref = ip & mask
        pref_encoded = encode_ip_prefix_pair(test_pref, pref_len, protocol)
        if pref_encoded in fib:
            return fib[pref_encoded]
    return None

def _lookup_in_fib(fib, traffic, maxx, minn, protocol='v4'):
    '''Used in testing Bloom filter.
    '''
    found = 0
    for ip in traffic:
        if _lookup_item_in_fib(fib, ip, maxx, minn, protocol)\
                is not None:
            found += 1
    return found

def test_build_bloom_filter(protocol='v4'):
    ''' Verify can build linear and guided Bloom filter.
        And that we can recover all matches from either linear or guided
        BF using linear search (testing against FIB).
    '''
    fib, traffic, pref_stats = _common_prep('v4', RANDOM_TRAFFIC)

    # (1) build linear and guided Bloom filters
    bf_linear, prefixes, _ = ipfilter.build_bloom_filter(
        protocol='v4', lamda=None, fpp=FPP, k=None,
        num_bits=None, fib=fib)
    print(bf_linear)

    bf_guided, prefixes, bst, count_bmp = ipfilter.build_bloom_filter(
        protocol='v4', lamda=weigh_equally, fpp=FPP, k=None,
        num_bits=None, fib=fib)
    print(bf_guided)

    # (2) all prefixes in FIB must be found in either
    print('Will ensure all prefixes in FIB can be found in either BF...')
    for prefix in fib:
        assert bf_linear.contains(prefix, hashes=list(range(bf_linear.k))) != 0
        assert bf_guided.contains(prefix, hashes=list(range(bf_guided.k))) != 0

    # (3) test traffic against FIB, linear, and guided Bloom, use linear lookup for guided for now
    print("Test traffic against FIB and both BF's. Use linear search for guided BF...")
    fpp_linear = fpp_guided = 0
    for ip in traffic:
        if _lookup_item_in_fib(fib, ip,
                prefixes['maxx'], prefixes['minn'], protocol='v4')\
                is not None:

            bfl_found, bfl_fpps = ipfilter._linear_lookup_helper(
                    bf_linear,
                    list(range(bf_linear.k)),
                    ip,
                    prefixes['maxx'],
                    prefixes['minn'],
                    fib,
                    protocol)
            if bfl_found < 1:
                print("Found false negative in linear BF: %d" %ip)

            bfg_found, bfg_fpps = ipfilter._linear_lookup_helper(
                    bf_guided,
                    list(range(bf_guided.k)),
                    ip,
                    prefixes['maxx'],
                    prefixes['minn'],
                    fib,
                    protocol)
            if bfg_found < 1:
                print("Found false negative in guided BF: %d" %ip)

# def tmp():
#     fib, traffic, prefixes = _common_prep('v4', RANDOM_TRAFFIC)
#     # test with bin search tree

#     bf_guided, prefixes, bst, count_bmp = ipfilter.build_bloom_filter(
#         protocol='v4', lamda=weigh_equally, fpp=None, k=20,
#         num_bits=215480360, fib=fib)
#     print(bf_guided)
#     num_found, num_false_positive, num_defaulted_to_linear_search =\
#             ipfilter.lookup_in_bloom(bf_guided,
#                                      traffic,
#                                      bst,
#                                      fib,
#                                      maxx=prefixes['maxx'],
#                                      minn=prefixes['minn'],
#                                      ix2len=prefixes['ix2len'],
#                                      protocol='v4')
#     print('Guided Bloom: total found %d out of %d (%.2f)' %(num_found, len(traffic), num_found/len(traffic)))
#     print('target false positive rate: %.2f' %0.01)
#     print('approx false positive rate: %.2f' %(num_false_positive/(num_found+num_false_positive))) # not actual fpp rate
#     print('number of times defaulted to linear search: %d' %(num_defaulted_to_linear_search))


if __name__ == "__main__":
    protocol='v4'
    test__choose_hash_funcs()
    test__build_linear_bloom(protocol)
    test__find_bmp(protocol)
    _pattern_insert(protocol='v4')
    test__build_guided_bloom(protocol)
    test_build_bloom_filter(protocol='v4')

    # tmp()


    # # build a Bloom filter using a balanced binary search tree
    # # bf_guided, prefixes, bst, count_bmp = build_bloom_filter(protocol='v4', lamda=weigh_equally, fpp=0.01, fib=fib)
    # # bf_guided, prefixes, bst, count_bmp = build_bloom_filter(protocol='v4', lamda=weigh_equally, fpp=1e-15, fib=fib)
    # bf_guided, prefixes, bst, count_bmp = build_bloom_filter(protocol='v4', lamda=weigh_equally, fpp=None, k=7, num_bits=215480360, fib=fib) # => ok fpp rate, but still dismal false negative rate
    # print('guided Bloom:', bf_guided) # => BloomFilter(fpp=0.01, n=749362, k=7, ba=(malloc=0.86MB, length=7182679b, %full=59.5))
    # print('%%prefixes have a bmp: %.1f' %(100*count_bmp/len(prefixes['prefixes'])))
    # input('continue?')
