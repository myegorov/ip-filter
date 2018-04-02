import sys
from conf import *
for d in [DATADIR, IPV4DIR, IPV6DIR]:
    sys.path.append(d)
from bloomfilter import BloomFilter
from random import shuffle
from obst import *

FPP = 1e-6 # false positive probability setting for Bloom filter

def compile_fib_table(protocol='v4'):
    '''Load prefixes into a hash table.
       Returns FIB table (dict): { (pref_int, pref_len): pref_str }
            e.g. for IPv4: { (16777216, 24): '1.0.0.0/24', ...}
    '''
    indir = IPV4DIR if protocol=='v4' else IPV6DIR
    fib = dict()
    with open (os.path.join(indir, PREFIX_FILE), 'r') as infile:
        for line in infile:
            parts = line.strip().split()
            if len(parts) != 3: continue
            fib[(int(parts[0]), int(parts[1]))] = parts[2]
    return fib

def load_traffic(protocol='v4', typ=RANDOM_TRAFFIC):
    '''Load and return a list of IPs from `typ`.
    '''
    indir = IPV4DIR if protocol=='v4' else IPV6DIR
    traffic = []
    fpath = os.path.join(indir, typ)
    if os.path.isfile(fpath):
        with open(fpath, 'r') as infile:
            for line in infile:
                parts = line.strip().split()
                if len(parts) != 2: continue
                traffic.append(int(parts[0]))
    else:
        raise FileNotFoundError('No such file: "%s"' %fpath)
    return traffic

def _load_prefixes(protocol='v4'):
    prefixes = []
    indir = IPV4DIR if protocol=='v4' else IPV6DIR
    with open (os.path.join(indir, PREFIX_FILE), 'r') as infile:
        for line in infile:
            parts = line.strip().split()
            if len(parts) != 3: continue
            prefixes.append((int(parts[0]), int(parts[1])))
    return prefixes

def _build_linear_bloom(prefixes, fpp):
    # compile range of prefixes for given protocol
    minn = min([pref_len for (_,pref_len) in prefixes])
    maxx = max([pref_len for (_,pref_len) in prefixes])

    # insert prefixes in Bloom filter
    bf = BloomFilter(fpp, len(prefixes))
    count = 0
    for pair in prefixes:
        if count % 10000 == 0:
            print('processsed %.3f of all prefixes' %(count/len(prefixes)))
        bf.insert(pair)
        count += 1

    # return bloom_filter and (minn, maxx) range
    return bf, (minn, maxx)

def _build_guided_bloom(prefixes, fpp, root, fib):
    '''Returns a Bloom filer optimized for the `root` bin search tree,
        and `encoded_pref_lens` dict for looking up the BMP prefix length
        from hash-encoded bit sequence.
    '''

    # encoded_pref_lens will be used at lookup: ix -> prefix length for BMP
    # pref_lens_reverse will be used at build time
    pref_lens = sorted(list(set([pref_len for (_,pref_len) in prefixes])))
    minn = pref_lens[0]
    maxx = pref_lens[-1]
    # if there's no default, add 0-length prefix length
    if pref_lens[0] > 0:
        pref_lens.insert(0, 0)
    encoded_pref_lens = {ix:pref_len for (ix, pref_len) in enumerate(pref_lens)}
    pref_lens_reverse = {pref_len:ix for (ix, pref_len) in enumerate(pref_lens)}

    # walk the tree starting from root
    # extract prefix length from root.val
    # TODO: continue below
    while root:
        pass

        # if root is None -> return to most recent hit
        pass

        # find BMP
        bmp = _find_bmp(prefix, pref_len-1, fib, maxx, minn, pref_lens_reverse)

    return bf, encoded_pref_lens


# TODO: re-write _find_bmp() after lookup function is complete
def _find_bmp(prefix, max_pref_len, fib, maxx, minn, pref_lens_reverse):
    '''This is just a temporary crutch. The way to look up the
        best matching prefix (BMP) is to use the prefixes already
        entered in the Bloom filter to date (hence, insert prefixes
        into BF in ascending order), i.e. to use the guided lookup
        in the BF under construction.

        For the time being, look up all subprefixes of `prefix` in
        `fib` table, starting with `max_pref_len` length.

        Returns best matching prefix length (list of 0's and 1's bin encoding for int)
        or empty list if not found.
    '''
    for pref_len in range(max_pref_len, minn-1, -1):
        mask = ((1<<pref_len) - 1) << (maxx-pref_len)
        test_pref = prefix & mask
        if (test_pref, pref_len) in fib:
            return _encode(pref_len, pref_lens_reverse)

    return []

def _encode(num, table):
    width = 5 if len(table) < 32 else 6
    return list(bin(table[num])[2:].zfill(width))

def _decode(bin_array, table):
    '''Receives a list of ones and zeroes, returns decoded 
        prefix length from table.
    '''
    #TODO
    pass

def _linear_lookup_bloom(bf, traffic, maxx, minn, fib):
    found = 0
    false_positives = 0
    for ip in traffic:
        for pref_len in range(maxx, minn-1, -1):
            mask = ((1<<pref_len) - 1) << (maxx-pref_len)
            test_pref = ip & mask
            if bf.contains(test_pref):
                if (test_pref, pref_len) in fib:
                    found += 1
                    break
                else:
                    false_positives += 1
    return found, false_positives

def build_bloom_filter(protocol='v4', lamda=None, fpp=FPP):
    '''Build and return a Bloom filter containing all prefixes.
        If provided with `lamda`, return also the optimal binary search tree,
        else (min, max) of prefix lengths.
    '''
    # [(pref_int, pref_len),...], sorted in ascending order
    prefixes = _load_prefixes(protocol)

    if lamda is not None:
        # compute optimal bin search tree
        bst = obst(protocol, lamda)
        # pass bin search tree and other args to helper function
        # TODO: for now passing fib as argument, will NOT need it once
        #   guided lookup works and lookup_bmp() is refactored
        return _build_guided_bloom(prefixes, fpp, bst, fib)
    else: # build for linear search
        return _build_linear_bloom(prefixes, fpp)

def lookup_in_bloom(bf, traffic, path, fib):
    '''Look up `traffic` in `bf`. If unguided search -> range between
        path[1] to path[0]. If guided search -> `path` is an (optimal)
        binary search tree to guide the search.
    '''
    if isinstance(path, tuple): # linear search
        return _linear_lookup_bloom(bf, traffic, path[1], path[0], fib)
    else:
        # TODO
        pass

if __name__ == "__main__":
    # fib = compile_fib_table('v6')
    fib = compile_fib_table(protocol='v4')

    traffic=load_traffic(protocol='v4', typ=RANDOM_TRAFFIC)
    # traffic=load_traffic(protocol='v6', typ=PREF_SPACE_TRAFFIC)

    # bf, pref_len_range = build_bloom_filter(protocol='v4', fpp=0.01)
    # print(bf) # => BloomFilter(fpp=0.01, n=749362, k=7, ba=BitArray(7182679, %full=51.8))
    # print('range of prefixes:', pref_len_range) # => range of prefixes: (8, 32)

    # build a Bloom filter using a balanced binary search tree
    bf, bst = build_bloom_filter(protocol='v4', lamda=weigh_equally, fpp=0.01)

    # # shuffle traffic and search
    # shuffle(traffic)
    # num_found, num_false_positive = lookup_in_bloom(bf, traffic, pref_len_range, fib)
    # print('total found %d out of %d (%.2f)' %(num_found, len(traffic), num_found/len(traffic)))
    # print('actual false positive rate: %.2f' %(num_false_positive/(num_found+num_false_positive)))
    # print('target false positive rate: %.sf' %0.01)
