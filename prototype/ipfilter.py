import sys
from mconf import *
for d in [DATADIR]:
    sys.path.append(d)

from bloomfilter import BloomFilter
from random import shuffle
from obst import *
from utils import encode_ip_prefix_pair,\
                    load_prefixes, prefix_stats

ENCODING={'v4':5,'v6':6} # min num bits to encode prefix length
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

    # return Bloom filter and prefixes dict
    return bf, prefixes, None

# TODO: re-write _find_bmp() after lookup function is complete
def _find_bmp(prefix, max_pref_len, fib, minn, len2ix, protocol='v4'):
    '''This is just a temporary crutch. The way to look up the
        best matching prefix (BMP) is to use the prefixes already
        entered in the Bloom filter to date (hence, insert prefixes
        into BF in ascending order), i.e. to use the guided lookup
        in the BF under construction.

        For the time being, look up all subprefixes of `prefix` in
        `fib` table, starting with `max_pref_len` length.

        Returns best matching prefix length (encoded as int for prefixes['ix2len'] lookup)
        or 0 if not found (default route).
    '''
    max_shift = NUMBITS[protocol]

    for pref_len in range(max_pref_len, minn-1, -1):
        mask = ((1<<max_shift) - 1) << (max_shift - pref_len)
        test_pref = prefix & mask
        if encode_ip_prefix_pair(test_pref, pref_len, protocol) in fib:
            return len2ix[pref_len]
    return len2ix[0]

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

    count_bmp = 0 # keep track of how often a prefix has an BMP

    count = 0 # report progress
    for pair in prefixes['prefixes']:
        if count % 10000 == 0:
            print('build processsed %.3f of all prefixes' %(count/len(prefixes['prefixes'])))
        count += 1

        prefix, preflen = pair
        # BMP is an index, can recover prefix length using prefixes['ix2len']
        bmp = _find_bmp(prefix, preflen-1, fib, prefixes['minn'],
                        prefixes['len2ix'], protocol=protocol)
        if bmp != prefixes['len2ix'][0]: # if not default route
            count_bmp += 1

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
    return bf, prefixes, root, count_bmp

def build_bloom_filter(protocol='v4', lamda=None, fpp=FPP, k=None, num_bits=None, fib=None,
                      prefixes=None, pref_stats=None):
    '''Build and return a Bloom filter containing all prefixes.
        If provided with `lamda`, return also the optimal binary search tree,
        else (min, max) of prefix lengths.

        Returns a triple (Bloom filter, prefixes, optionally bin search tree)
    '''
    # [(pref_int, pref_len),...], sorted in ascending order
    if prefixes is None:
        prefixes = load_prefixes(protocol)
    if pref_stats is None:
        pref_stats = prefix_stats(prefixes)

    if lamda is None: # build for linear search
        return _build_linear_bloom(pref_stats, fpp, k, num_bits, protocol=protocol)
    else:
        bst = obst(protocol, lamda)
        # TODO: for now passing fib as argument, will NOT need it once
        #   guided lookup works and lookup_bmp() is refactored, except as final check
        return _build_guided_bloom(pref_stats, fpp, k, num_bits, bst, fib, protocol=protocol)


# TODO: unit test functions below
def lookup_in_bloom(bf, traffic, path, fib, maxx=None, minn=None, ix2len=None, protocol='v4'):
    '''Look up `traffic` in `bf`. If unguided search -> range between
        path[1] to path[0]. If guided search -> `path` is an (optimal)
        binary search tree to guide the search.
    '''
    if isinstance(path, tuple): # linear search
        return _linear_lookup_bloom(bf, traffic, path[1], path[0], fib, protocol)
    else:
        return _guided_lookup_bloom(bf, traffic, path, fib, maxx, minn, ix2len, protocol=protocol)

def _linear_lookup_bloom(bf, traffic, maxx, minn, fib, protocol):
    found, false_positives = 0, 0
    hashes = _choose_hash_funcs(0, end=bf.k)

    count = 0
    for ip in traffic:
        if count % 10000 == 0:
            print('lookup processed %.3f of all ips' %(count/len(traffic)))
        count += 1

        f, fp = _linear_lookup_helper(bf, hashes, ip, maxx, minn, fib, protocol)
        found += f
        false_positives += fp
    return found, false_positives

def _linear_lookup_helper(bf, hashes, ip, maxx, minn, fib, protocol):
    max_shift = NUMBITS[protocol]

    found, false_positives = 0, 0
    for pref_len in range(maxx, minn-1, -1):
        mask = ((1<<max_shift) - 1) << (max_shift-pref_len)
        test_pref = ip & mask
        pref_encoded = encode_ip_prefix_pair(test_pref, pref_len, protocol)
        if bf.contains(pref_encoded, hashes=hashes):
            if pref_encoded in fib:
                found += 1
                break
            else:
                false_positives += 1

    return found, false_positives

def _guided_lookup_bloom(bf, traffic, root, fib, maxx, minn, ix2len, protocol='v4'):
    max_shift = NUMBITS[protocol]

    found, false_positives = 0, 0
    num_defaulted_to_linear_search = 0 # number of times had to default to linear search
    k = bf.k

    count = 0
    for ip in traffic:
        if count % 10000 == 0:
            print('lookup processed %.3f of all ips' %(count/len(traffic)))
        count += 1

        current = root
        count_hit = 0
        preflen_hit = (0,0) # last preflen lookup that resulted in a hit, default to 0
        while current:
            masked = (((1<<max_shift) - 1) << (max_shift-current.val)) & ip
            pref_encoded = encode_ip_prefix_pair(masked, current.val, protocol)
            if not bf.contains(pref_encoded, hashes=[0]):
                current = current.left
            else:
                count_hit += 1
                preflen_hit = (current.val, count_hit)
                current = current.right

        # current is None, reached leaf of tree
        if preflen_hit[0] == 0:
            continue # return ix2len[0] <- default route

        # try decoding BMP (best matching prefix)
        masked = (((1<<max_shift) - 1) << (max_shift-preflen_hit[0])) & ip
        pref_encoded = encode_ip_prefix_pair(masked, preflen_hit[0], protocol)
        bmp_ix = bf.contains(pref_encoded,
                             hashes=_choose_hash_funcs(preflen_hit[1], end=preflen_hit[1]+ENCODING[protocol]),
                             keep_going = True)

        # bmp should always be greater than 0! and potentially pointing at the wrong BMP pref length...
        if bmp_ix > 0:
            bmp = preflen_hit[0]
            # test remaining hashes
            if bmp_ix < (1<<ENCODING[protocol]) - 1:
                # if false positive hit screws up the decoding, default to linear search
                if bmp_ix >= len(ix2len):
                    false_positives += 1
                    f, fp = _default_to_linear_search(bf, ip, bmp-1, minn, fib, protocol)
                    found += f
                    false_positives += fp
                    num_defaulted_to_linear_search += 1
                    continue
                else:
                    bmp = ix2len[bmp_ix]
                    masked = (((1<<max_shift) - 1) << (max_shift-bmp)) & ip
                    pref_encoded = encode_ip_prefix_pair(masked, bmp, protocol)
            # else: # keep going with the bmp previously found
            # TODO: note that lookup of BMP will fail if false positive hits screw up decoding and point at
            #       at incorrect BMP (while correct BMP exists). In this case,
            #       we'll register __not found__, where the correct response
            #       is that BMP exists and could be found through linear search
            #       of all prefixes below bmp. How do we deal with false negative??
            #       Decode the BMP encoded in preceding hit (preceding hit may not exist)?
            #       Add a parity bit to encoding to check if BMP makes sense?
            #       Shoot for very low fpp?
            if bf.contains(pref_encoded,
                           hashes = _choose_hash_funcs(preflen_hit[1] + ENCODING[protocol], end=k)):
                if pref_encoded in fib:
                    found += 1
                else:
                    false_positives += 1
                    # default to linear search of remaining prefixes below BMP
                    f, fp = _default_to_linear_search(bf, ip, bmp-1, minn, fib, protocol)
                    found += f
                    false_positives += fp
                    num_defaulted_to_linear_search += 1
            else: # screwed up by false positives during decoding, default to linear search
                false_positives += 1
                # default to linear search of remaining prefixes below BMP
                f, fp = _default_to_linear_search(bf, ip, bmp-1, minn, fib, protocol)
                found += f
                false_positives += fp
                num_defaulted_to_linear_search += 1

        # else: return ix2len[bmp] <- default route, effectively no update to `found`

    return found, false_positives, num_defaulted_to_linear_search

def _default_to_linear_search(bf, ip, bmp, minn, fib, protocol='v4'):
    # default to linear search of remaining prefixes below BMP
    hashes = _choose_hash_funcs(0, end=bf.k)
    return _linear_lookup_helper(bf, hashes, ip, bmp, minn, fib, protocol)

def lookup_in_fib(fib, traffic, maxx, minn, protocol='v4'):
    '''Used in testing Bloom filter.
    '''
    max_shift = NUMBITS[protocol]

    found = 0
    for ip in traffic:
        for pref_len in range(maxx, minn-1, -1):
            mask = ((1<<max_shift) - 1) << (max_shift-pref_len)
            test_pref = ip & mask
            pref_encoded = encode_ip_prefix_pair(test_pref, pref_len, protocol)
            if pref_encoded in fib:
                found += 1
                break
    return found

if __name__ == "__main__":


    # # test with FIB
    # # shuffle traffic and search
    # shuffle(traffic)
    # num_found = lookup_in_fib(fib, traffic, prefixes['maxx'], prefixes['minn'], protocol='v4')
    # print('FIB: total found %d out of %d (%.2f)' %(num_found, len(traffic), num_found/len(traffic)))

    # # test with linear lookup
    # shuffle(traffic)
    # num_found, num_false_positive = lookup_in_bloom(bf_linear, traffic, (prefixes['minn'], prefixes['maxx']), fib, protocol='v4')
    # print('Linear Bloom: total found %d out of %d (%.2f)' %(num_found, len(traffic), num_found/len(traffic)))
    # print('target false positive rate: %.2f' %0.01)
    # print('approx false positive rate: %.2f' %(num_false_positive/(num_found+num_false_positive))) # not actual fpp rate

    # test with bin search tree
    shuffle(traffic)
    num_found, num_false_positive, num_defaulted_to_linear_search = lookup_in_bloom(bf_guided, traffic, bst, fib, maxx=prefixes['maxx'], minn=prefixes['minn'], ix2len=prefixes['ix2len'], protocol='v4')
    print('Guided Bloom: total found %d out of %d (%.2f)' %(num_found, len(traffic), num_found/len(traffic)))
    print('target false positive rate: %.2f' %0.01)
    print('approx false positive rate: %.2f' %(num_false_positive/(num_found+num_false_positive))) # not actual fpp rate
    print('number of times defaulted to linear search: %d' %(num_defaulted_to_linear_search))

    # TODO: test false positive rate
    pass

    # TODO: test false negative rate
    #       problem: very high false negative rate
    #           seems like highish false positive is not the problem, rather false negative is
    #           optimal Bloom setting (i.e. by setting fpp) seems to work better than arbitrary k and num_bits settings
    pass

    # TODO: print how many times defaulted to linear search compared to total num of IPs looked up
    # TODO: currently looks like it almost exclusively finds on linear search, guided search of no use

