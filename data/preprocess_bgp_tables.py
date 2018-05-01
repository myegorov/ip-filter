'''
- parse BGP tables from http://bgp.potaroo.net/index-bgp.html
- plot and output the stats about prefix count & address space covered
- fetch covered address space and partition the space by prefix length
- output sorted list of prefixes:
    prefix_int prefix_len cidr_network
    16909060 32 1.2.3.4/32

Usage:
    python3 preprocess_bgp_tables.py
'''

import os
from conf import *
import netaddr as net
import matplotlib.pyplot as plt

# not worrying about reserved addresses
IPv4_SPACE = 2**32
IPv6_SPACE = 2**128

def parse_oregon(protocol='v4'):
    ''' Extract network addresses from the Oregon table (IPv4 or IPv6).
        Ignore next hop for the purpose of this experiment.

        Write (NetworkStr PrefixLength NetworkInt) to file and return
        count of prefix lengths.
    '''
    if protocol == 'v4':
        return _oregon_v4()
    else:
        return _oregon_v6()

def _oregon_v4():
    res = []
    print('\nParsing IPv4 BGP table...')
    with open (os.path.join(IPv4_AS6447, BGPTAB), 'r') as infile:
        for line in infile:
            if line.startswith('>'):
                parts = line[1:].split()
                if len(parts) > 0:
                    network = parts[0]
                    res.append(network)
    return res

def _oregon_v6():
    res = []
    seen = set()
    print('\nParsing IPv6 BGP table...')
    with open (os.path.join(IPv6_AS6447, BGPTAB), 'r') as infile:
        for line in infile:
            parts = line.split()
            if len(parts) > 0:
                network = parts[0]
                if network in seen: continue
                seen.add(network)
                res.append(network)
    return res


def partition(prefixes, protocol='v4'):
    ''' Collect some stats about the fraction of IPv4 space covered
        by prefixes.

        Return: 
            covered_space (all networks merged where contiguous, 
                            can randomly subsample IPs from this space),
            fraction_covered (what fraction of IPv4 space is covered by prefixes),
            [(ipset_of_prefix_length_i, fraction_of_covered_space, count_of_prefix_length_i),...]
    '''
    if protocol == 'v4':
        SPACE_SIZE = IPv4_SPACE
        LEN = 33
    else:
        SPACE_SIZE = IPv6_SPACE
        LEN = 129
    # add all networks to set
    # calculate size of set and fraction of total IPv4 space covered
    all_prefixes = [net.IPNetwork(network) for network in prefixes]
    covered_space = net.IPSet(all_prefixes)
    fraction_covered = covered_space.size / SPACE_SIZE

    # do sets for each prefix length and calculate size
    print('\nCreating a set of networks for each prefix length...')
    networks_by_prefix_length = [[] for plen in range(LEN)]
    for network in prefixes:
        network = net.IPNetwork(network)
        plen = network.prefixlen
        networks_by_prefix_length[plen].append(network)
    plen_counts = [len(plen_networks) for plen_networks in networks_by_prefix_length]
    prefix_lens = [net.IPSet(networks_by_prefix_length[plen]) for plen in range(LEN)]

    print('\nCalculating % space covered by each prefix length...')
    prefix_lens_tight = [None for plen in range(LEN)] # exclude the more specific ranges
    space_by_plen = [0 for i in range(LEN)]
    precedence_pset = net.IPSet([])
    for i in range(LEN-1,-1,-1):
        plen, pset = i, prefix_lens[i]
        print('\tprocessing length:', plen)
        if pset.size == 0:
            prefix_lens_tight[plen] = pset
            continue
        plen_space = pset.difference(precedence_pset)
        prefix_lens_tight[plen] = plen_space
        space_by_plen[plen] = plen_space.size / covered_space.size

        # more specific prefixes take precedence over less specific ones
        precedence_pset = precedence_pset.union(pset)

    # # verify space covered by each prefix length adds up to space covered by all prefixes
    # print('fraction covered by each prefix:', space_by_plen)
    # print('adds up to 1.0?', sum(space_by_plen))

    return covered_space, fraction_covered,\
            list(zip(prefix_lens_tight, space_by_plen, plen_counts))

def plot_stats(x, y, outdir=IMGDIR, outfile='stats.png', title='Count vs. Length',
              y_logscale=True, txt=''):
    ''' Plot bar graph of x vs y.
    '''
    print("\nPlotting the stats to %s" %(os.path.join(outdir, outfile)))
    fig, ax = plt.subplots()
    width = 0.5
    ax.bar(x, y, width, color="red")
    yoffset = 0.1 * max(y)
    if y_logscale:
        yoffset = 0
        ax.set_yscale('log')
    # for i, v in enumerate(y):
    #     if i % 2 != 0 or v == 0: continue
    #     ax.text(i-0.75, v+yoffset, str(v), color='blue', rotation=50)
    if txt:
        plt.text(1, max(y)-yoffset, txt, fontsize=12, color='blue')

    plt.xticks(range(x[0], x[-1]+1, len(x)//16), rotation=45)
    plt.title(title)
    parts = title.split()
    plt.xlabel(parts[-1])
    plt.ylabel(parts[0])
    plt.savefig(os.path.join(outdir, outfile), format='png',
                bbox_inches='tight')

def output(prefixes, protocol='v4'):
    res = sorted([net.IPNetwork(network) for network in prefixes])
    triples = map(lambda network: (network.first, network.prefixlen, str(network)), res)

    with open(os.path.join(TRAFFICDIR, 'ip'+protocol, BGPTAB), 'w') as outfile:
        outfile.write('\n'.join('%d %d %s' %group for group in triples))

def write_stats(arrays, protocol='v4'):
    with open(os.path.join(TRAFFICDIR, 'ip'+protocol, STATSFILE), 'w') as outfile:
        for arr in arrays:
            outfile.write(','.join([str(elem) for elem in arr]))
            outfile.write('\n')

def preprocess(protocol='v4'):
    if protocol == 'v4':
        LEN = 33
    else:
        LEN = 129
    # extract addresses
    prefixes = parse_oregon(protocol)

    # output sorted list of prefixes (will be entered in Bloom filter):
    #     prefix_int prefix_len cidr_network
    #     16909060 32 1.2.3.4/32
    output(prefixes, protocol)

    # partitions of address space by prefix length
    ipset_covered_by_prefixes, fraction_covered, ipsets_for_each_prefix_length =\
            partition(prefixes, protocol)

    # collect basic stats:
    #   total number of prefixes, number/fraction for each length
    _,space_by_prefix_length, count_by_prefix_length =\
            zip(*ipsets_for_each_prefix_length)
    totals = sum(count_by_prefix_length) # total number of prefixes in table
    # fraction of each prefix length
    fraction_count_by_prefix_length =\
            [num/totals for num in count_by_prefix_length]

    # plot the distribution of IP prefixes
    #   count vs length
    plot_stats(list(range(LEN)), count_by_prefix_length,\
               outdir=IMGDIR, outfile='count_vs_length_%s.png' %protocol,\
               title='Count vs. Length', y_logscale=True,
               txt='total of %d prefixes' %totals)
    #   percent of networks by length
    plot_stats(list(range(LEN)), fraction_count_by_prefix_length,\
               outdir=IMGDIR, outfile='fraction_count_vs_length_%s.png' %protocol,\
               title='Fraction vs. Length', y_logscale=protocol=='v6')
    #   plot the fractions of space covered by prefix length
    plot_stats(list(range(LEN)), space_by_prefix_length,\
               outdir=IMGDIR, outfile='fraction_space_vs_length_%s.png' %protocol,\
               title='Space vs. Length', y_logscale=protocol=='v6',
               txt='%.2f of IP%s space covered' %(fraction_covered, protocol))

    # output stats about prefix distribution
    # can be used, e.g. by weighting functions
    stats = [fraction_count_by_prefix_length, list(space_by_prefix_length)]
    stats[0].insert(0, 'prefix_len_fraction')
    stats[1].insert(0, 'prefix_space_fraction')
    write_stats(stats, protocol=protocol)


if __name__ == "__main__":
    preprocess('v4')
    preprocess('v6')
