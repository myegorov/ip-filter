'''ipfilter.py

This module builds on plain vanilla BloomFilter to construct
a guided BloomFilter that exposes the following API:

    build_bloom_filter(protocol='v4', lamda=None, fpp=FPP, k=None,
                        num_bits=None, fib=None,
                        prefixes=None, pref_stats=None)

    lookup_in_bloom(bf, traffic, fib, root=None, maxx=None, minn=None,
                        ix2len=None, protocol='v4')

    The lookup can perform linear or guided search and compile stats (in progress).
'''
import sys
from mconf import *
for d in [DATADIR]:
    sys.path.append(d)

from bloomfilter import BloomFilter
from random import shuffle
from obst import *
from utils import encode_ip_prefix_pair, load_prefixes, prefix_stats
from profiler import count_invocations

ENCODING={'v4':5,'v6':7} # min num bits to encode prefix length
NUMBITS={'v4':32,'v6':128}

FPP = 1e-6 # false positive probability setting for Bloom filter

def _choose_hash_funcs(start, end=None, pattern=None):
    '''Generate and return a list/generator of hash functions to use,
        e.g. [0,1,2,3] if `start`==0, `end`==4. Or encode `pattern` as
        a bitstring (e.g. [7] for `start`==5, `pattern`==4, encoding "100"
        starting at hash func #5 to signal BF to set bit #7)

        Range is exclusive of `end`.
    '''
    if pattern is None:
        return range(start, end, 1)
    res = []
    count = 0
    while pattern:
        if pattern & 1:
            res.append(start+count)
        count += 1
        pattern >>= 1
    return res

def _build_linear_bloom(prefixes, fpp, k, num_bits, protocol='v4'):
    if not (k or num_bits):
        bf = BloomFilter(fpp, len(prefixes['prefixes']))
    else:
        bf = BloomFilter(fpp, len(prefixes['prefixes']), k=k, num_bits=num_bits)

    count = 0
    for pair in prefixes['prefixes']:
        if count % 10000 == 0:
            print('build processsed %.3f of all prefixes' %(count/len(prefixes['prefixes'])))
        count += 1

        bf.insert(encode_ip_prefix_pair(*pair, protocol), hashes=_choose_hash_funcs(0,end=bf.k))

    return bf, None

def _find_bmp(prefix, bf, root, fib, max_pref_len, minn, len2ix, ix2len, protocol='v4'):
    '''Look up the best matching prefix (BMP) among the ones previously
        entered in the Bloom filter (hence, insert prefixes
        into BF in ascending order).

        Returns best matching prefix length (encoded as int for prefixes['ix2len'] lookup)
        or 0 if not found (default route).
    '''
    preflen, fib_val, _ = _guided_lookup_helper(
                bf, root, prefix, fib, max_pref_len, minn, ix2len, protocol)
    return len2ix[preflen], fib_val

def _build_guided_bloom(prefixes, fpp, k, num_bits, root, fib, protocol='v4'):
    '''Returns a Bloom filer optimized for the `root` bin search tree,
        and `encoded_pref_lens` dict for looking up the BMP prefix length
        from hash-encoded bit sequence.
    '''
    max_shift = NUMBITS[protocol]

    if not (k or num_bits):
        bf = BloomFilter(fpp, len(prefixes['prefixes']))
    else:
        bf = BloomFilter(fpp, len(prefixes['prefixes']), k=k, num_bits=num_bits)

    count = 0 # report progress
    for pair in prefixes['prefixes']:
        if count % 10000 == 0:
            print('build processsed %.3f of all prefixes' %(count/len(prefixes['prefixes'])))
        count += 1

        prefix, preflen = pair
        # BMP is an index, can recover prefix length using prefixes['ix2len']
        bmp, fib_val = _find_bmp(prefix, bf, root, fib, preflen-1, prefixes['minn'],
                        prefixes['len2ix'], prefixes['ix2len'],
                        protocol=protocol)

        current = root
        count_hit = 0
        while current:
            if preflen < current.val:
                current = current.left
            elif preflen == current.val:
                # insert using hash_1..hash_k
                pref_encoded = encode_ip_prefix_pair(prefix, preflen, protocol)
                bf.insert(pref_encoded, hashes=_choose_hash_funcs(0,end=bf.k))
                break
            else: # preflen > current.val
                masked = (((1<<max_shift) - 1) << (max_shift-current.val)) & prefix
                pref_encoded = encode_ip_prefix_pair(masked, current.val, protocol)
                bf.insert(pref_encoded, hashes=_choose_hash_funcs(0,end=1))
                count_hit += 1
                # insert pointers
                bf.insert(pref_encoded,
                          hashes=_choose_hash_funcs(count_hit,
                                                    pattern=bmp))
                current = current.right
    return bf, root

def build_bloom_filter(protocol='v4', lamda=None, fpp=FPP, k=None, 
                       num_bits=None, fib=None, prefixes=None, 
                       pref_stats=None):
    '''Build and return a Bloom filter containing all prefixes.
        If provided with `lamda`, return also the optimal binary search tree.

        Returns a pair:
            (Bloom filter, optionally bin search tree)
    '''
    # [(pref_int, pref_len),...], sorted in ascending order
    if prefixes is None: # default case, setting prefixes only for testing...
        prefixes = load_prefixes(protocol)
    if pref_stats is None:
        pref_stats = prefix_stats(prefixes)

    if lamda is None: # build for linear search
        return _build_linear_bloom(pref_stats, fpp, k, num_bits, protocol=protocol)
    else:
        bst = obst(protocol, lamda)
        return _build_guided_bloom(pref_stats, fpp, k, num_bits, bst, fib, protocol=protocol)

def _linear_lookup_helper(bf, hashes, ip, maxx, minn, fib, protocol):
    max_shift = NUMBITS[protocol]

    false_positives = 0
    for pref_len in range(maxx, minn-1, -1):
        mask = ((1<<max_shift) - 1) << (max_shift-pref_len)
        test_pref = ip & mask
        pref_encoded = encode_ip_prefix_pair(test_pref, pref_len, protocol)
        if bf.contains(pref_encoded, hashes=hashes):
            if pref_encoded in fib:
                return pref_len, fib[pref_encoded], false_positives
            else:
                false_positives += 1

    return 0, None, false_positives

def _linear_lookup_bloom(bf, traffic, maxx, minn, fib, protocol):
    num_found, false_positives = 0, 0
    hashes = _choose_hash_funcs(0, end=bf.k)

    count = 0
    for ip in traffic:
        if count % 10000 == 0:
            print('lookup processed %.3f of all ips' %(count/len(traffic)))
        count += 1

        # return pref_len, fib[pref_encoded], false_positives
        pref_len, fib_val, fp = _linear_lookup_helper(bf, hashes, ip, maxx, minn, fib, protocol)
        if fib_val is not None: num_found += 1
        false_positives += fp
    return num_found, false_positives

@count_invocations
def _default_to_linear_search(bf, ip, bmp_less_1, minn, fib, protocol='v4'):
    '''Default to linear search of remaining prefixes below BMP.
    '''
    hashes = _choose_hash_funcs(0, end=bf.k)
    return _linear_lookup_helper(bf, hashes, ip, bmp_less_1, minn, fib, protocol)

def _guided_lookup_helper(bf, root, ip, fib, maxx, minn, ix2len, protocol):
    ''' Returns resulting prefix length, FIB value (or None if default route), 
            num false positives
    '''
    max_shift = NUMBITS[protocol]
    k = bf.k
    false_positives = 0

    current = root # index of where we're in the binary search tree
    count_hit = 0
    preflen_hit = (0,count_hit) # (last preflen lookup that resulted in a hit (default to 0), count of hits along the path)
    while current:
        masked = (((1<<max_shift) - 1) << (max_shift-current.val)) & ip
        pref_encoded = encode_ip_prefix_pair(masked, current.val, protocol)
        if not bf.contains(pref_encoded, hashes=[0]): # guided by first hash function
            current = current.left
        else:
            count_hit += 1
            preflen_hit = (current.val, count_hit)
            current = current.right

    # current is None, reached leaf of tree
    if preflen_hit[0] == 0:
        # return default route
        return ix2len[preflen_hit[0]], None, 0

    # try decoding BMP (best matching prefix)
    masked = (((1<<max_shift) - 1) << (max_shift-preflen_hit[0])) & ip
    pref_encoded = encode_ip_prefix_pair(masked, preflen_hit[0], protocol)
    bmp_ix = bf.contains(pref_encoded,
                         hashes=_choose_hash_funcs(preflen_hit[1],
                                                   end=preflen_hit[1]+ENCODING[protocol]),
                         keep_going = True)

    # note that bmp_ix is potentially pointing at the wrong BMP pref length...
    #   if decoding fails due to false positive, default to linear search
    pref_hypothesis = preflen_hit[0]
    if bmp_ix < len(ix2len):
        pref_hypothesis = ix2len[bmp_ix] # BMP hypothesis
        masked = (((1<<max_shift) - 1) << (max_shift-pref_hypothesis)) & ip
        pref_encoded = encode_ip_prefix_pair(masked, pref_hypothesis, protocol)

    # check remaining hash funcs
    if (bmp_ix == (1<<ENCODING[protocol]) - 1 or pref_hypothesis < preflen_hit[0])\
            and bf.contains(pref_encoded,
                            hashes = _choose_hash_funcs(preflen_hit[1] + ENCODING[protocol],
                                                        end=k))\
            and pref_encoded in fib:
        return pref_hypothesis, fib[pref_encoded], 0

    # else default to linear search below longest prefix hit
    false_positives += 1
    preflen, fib_val, fp = _default_to_linear_search(bf, ip, preflen_hit[0]-1, minn, fib, protocol)
    false_positives += fp
    return preflen, fib_val, false_positives

def _guided_lookup_bloom(bf, traffic, root, fib, maxx, minn, ix2len, protocol='v4'):
    '''Currently defaulting to linear search iff led astray by false
        positive hits at any point.

        Alternatives to consider in the future:
            Investigate information theoretic approaches to noisy channels;
            Add a parity bit to encoding to check if BMP makes sense?
            Shoot for very sparse bitarrays (up to current cache bottleneck)?
    '''
    # keep track of number of times had to default to linear search
    num_found = false_positives = 0
    count = 0 # track progress
    for ip in traffic:
        if count % 10000 == 0:
            print('lookup processed %.3f of all ips' %(count/len(traffic)))
        count += 1

        # return preflen, fib_val, false_positives, 1
        preflen, fib_val, fp = _guided_lookup_helper(
                bf, root, ip, fib, maxx, minn, ix2len, protocol)
        false_positives += fp
        if fib_val is not None: num_found += 1

    return num_found, false_positives

def lookup_in_bloom(bf, traffic, fib, root=None, maxx=None, minn=None, ix2len=None, protocol='v4'):
    '''Look up `traffic` in `bf`. If unguided search -> range between
        maxx to minn. If guided search -> `root` is an (optimal)
        binary search tree to guide the search.

        Returns a pair: count of matched prefixes and count of false positives
            (return values can be used for sanity checks).
    '''
    if root is None: # linear search
        return _linear_lookup_bloom(bf, traffic, maxx, minn, fib, protocol)
    else:
        return _guided_lookup_bloom(bf, traffic, root, fib, maxx, minn, ix2len, protocol=protocol)
