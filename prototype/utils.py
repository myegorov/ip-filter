'''Convenience functions to load inputs for testing:

    - Compile FIB table for testing.
    - Load traffic from preprocessed files.
    - Load prefixes from preprocessed files.
'''

import sys
from conf import *
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

if __name__ == "__main__":
    fib = compile_fib_table(protocol='v4')
    traffic=load_traffic(protocol='v4', typ=RANDOM_TRAFFIC)
    prefixe=load_prefixes('v4')
