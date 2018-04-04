'''Convenience functions to load inputs for testing:

    - Compile FIB table for testing.
    - Load traffic from preprocessed files.
    - Load prefixes from preprocessed files.
'''

import sys
from mconf import *
for d in [IPV4DIR, IPV6DIR]:
    sys.path.append(d)

# ENCODING={'v4':5,'v6':6} # min num bits to encode prefix length
ENCODING={'v4':32,'v6':128}

def encode_ip_prefix_pair(ip, prefix, protocol='v4'):
    '''Takes two ints, returns an int. Used for hashing.
    '''
    return (prefix << ENCODING[protocol]) + ip

def compile_fib_table(protocol='v4'):
    '''Load prefixes into a hash table.
       Returns FIB table (dict): { encoded(pref_int, pref_len): pref_str }
            e.g. for IPv4: {103095992320: '1.0.0.0/24', ...}
    '''
    indir = IPV4DIR if protocol=='v4' else IPV6DIR
    fib = dict()
    with open (os.path.join(indir, PREFIX_FILE), 'r') as infile:
        for line in infile:
            parts = line.strip().split()
            if len(parts) != 3: continue
            fib[encode_ip_prefix_pair(int(parts[0]), int(parts[1]), protocol)] = parts[2]
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

def load_prefixes(protocol='v4'):
    prefixes = []
    indir = IPV4DIR if protocol=='v4' else IPV6DIR
    with open (os.path.join(indir, PREFIX_FILE), 'r') as infile:
        for line in infile:
            parts = line.strip().split()
            if len(parts) != 3: continue
            prefixes.append((int(parts[0]), int(parts[1])))
    return prefixes

def prefix_stats(prefixes):
    '''Return a dict of basic stats about the incoming prefixes.
    '''
    stats = dict()
    pref_lens = sorted(list(set([pref_len for (_,pref_len) in prefixes])))
    stats['minn'] = pref_lens[0]
    stats['maxx'] = pref_lens[-1]
    # if there's no default, add 0-length prefix length
    if pref_lens[0] > 0:
        pref_lens.insert(0, 0)
    stats['ix2len'] = pref_lens
    stats['len2ix'] = {pref_len:ix for (ix, pref_len) in enumerate(pref_lens)}
    stats['prefixes'] = prefixes
    return stats

if __name__ == "__main__":
    fib = compile_fib_table(protocol='v4')
    traffic=load_traffic(protocol='v4', typ=RANDOM_TRAFFIC)
    prefixes=load_prefixes('v4')
    stats = prefix_stats(prefixes)
    print('maxx:', stats['maxx'])
    print('minn:', stats['minn'])
    print('ix2len:', stats['ix2len'])
