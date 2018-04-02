import sys
from conf import *
for d in [DATADIR, IPV4DIR, IPV6DIR]:
    sys.path.append(d)
from bloomfilter import BloomFilter

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

def _build_linear_search_bloom(prefixes, fpp):
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

def build_bloom_filter(protocol='v4', guided=False, fpp=FPP):
    '''Build and return a Bloom filter containing all prefixes.
        If `guided` is True, return also the optimal binary search tree,
        else (min, max) of prefix lengths.
    '''
    # [(pref_int, pref_len),...], sorted in ascending order
    prefixes = _load_prefixes(protocol)
    if not guided:
        return _build_linear_search_bloom(prefixes, fpp)
    else:
        # TODO
        pass

if __name__ == "__main__":
    fib = compile_fib_table()
    fib = compile_fib_table('v6')

    traffic=load_traffic(protocol='v4', typ=RANDOM_TRAFFIC)
    # traffic=load_traffic(protocol='v6', typ=PREF_SPACE_TRAFFIC)

    bf, pref_len_range = build_bloom_filter(protocol='v4', guided=False, fpp=0.01)
    print(bf)
    print('range of prefixes:', pref_len_range)
