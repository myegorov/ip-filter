# TODO: pass
# TODO: IPv6
import os
import netaddr as net
from functools import reduce

ROOTDIR = os.path.dirname(os.path.realpath(__file__))
RAWDIR = os.path.join(ROOTDIR,'raw')
CLEANDIR = os.path.join(ROOTDIR, 'processed')

BGPTAB = 'bgptable.txt' # file name

# IPv4
IPv4_AS65000 = os.path.join(RAWDIR, 'ipv4', 'as2.0') # http://bgp.potaroo.net/as2.0/bgp-active.html
IPv4_AS6447 = os.path.join(RAWDIR, 'ipv4', 'as6447') # http://bgp.potaroo.net/as6447/

# IPv6
IPv6_AS65000 = os.path.join(RAWDIR, 'ipv6', 'as2.0') # http://bgp.potaroo.net/v6/as2.0/index.html
IPv6_AS6447 = os.path.join(RAWDIR, 'ipv6', 'as6447') # http://bgp.potaroo.net/v6/as6447/

def ipv4_to_int(ipv4):
    ''' Convert IPv4 string to int:
            '1.2.3.4' -> 16909060
    '''
    parts = ipv4.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) +\
           (int(parts[2]) << 8) + int(parts[3])

def int_to_ipv4(num):
    ''' Convert an int to IPv4 string:
            16909060 -> '1.2.3.4'
    '''
    res = []
    for i in range(4):
        res.append(str(num & 0xff))
        num >>= 8
    return '.'.join(list(reversed(res)))

def parse_APNIC(protocol='v4'):
    ''' Extract network addresses from an APNIC table (IPv4 or IPv6).
        Ignore next hop for the purpose of this experiment.

        Write (NetworkStr PrefixLength NetworkInt) to file and return
        count of prefix lengths.
    '''
    if protocol == 'v4':
        return _apnic_v4()
    else:
        # return _apnic_v6()
        pass

def parse_oregon(protocol='v4'):
    ''' Extract network addresses from the Oregon table (IPv4 or IPv6).
        Ignore next hop for the purpose of this experiment.

        Write (NetworkStr PrefixLength NetworkInt) to file and return
        count of prefix lengths.
    '''
    if protocol == 'v4':
        return _oregon_v4()
    else:
        # return _oregon_v6()
        pass

def _oregon_v4():
    res = []
    prefix_lengths = [0 for i in range(33)]
    with open (os.path.join(IPv4_AS6447, BGPTAB), 'r') as infile:
        for line in infile:
            if line.startswith('>'):
                parts = line[1:].split()
                if len(parts) > 0:
                    network = parts[0]
                    ix = network.find('/')
                    if ix < 0:
                        continue
                    # convert ip address and prefix length to ints
                    addr = ipv4_to_int(network[:ix])
                    prefix_len = int(network[ix+1:])
                    res.append((network, prefix_len, addr))
                    prefix_lengths[prefix_len] += 1

    # now write the prefixes to file
    # (NetworkStr PrefixLength NetworkInt)
    with open(os.path.join(CLEANDIR, 'ipv4', BGPTAB), 'w') as outfile:
        outfile.write('\n'.join('%s %s %s' %group for group in res))

    return prefix_lengths, res


def _apnic_v4():
    res = []
    prefix_lengths = [0 for i in range(33)]
    with open (os.path.join(IPv4_AS65000, BGPTAB), 'r') as infile:
        for line in infile:
            if line.startswith('*'):
                parts = line.split()
                if len(parts) > 2:
                    network, next_hop = parts[1], parts[2]
                    if len(network.split('.')) != 4 or\
                            len(next_hop.split('.')) != 4:
                        continue
                    ix = network.find('/')
                    if ix < 0:
                        continue
                    # convert ip address and prefix length to ints
                    addr = ipv4_to_int(network[:ix])
                    prefix_len = int(network[ix+1:])
                    res.append((network, prefix_len, addr))
                    prefix_lengths[prefix_len] += 1

    # now write the prefixes to file
    # (NetworkStr PrefixLength NetworkInt)
    with open(os.path.join(CLEANDIR, 'ipv4', BGPTAB), 'w') as outfile:
        outfile.write('\n'.join('%s %s %s' %group for group in res))

    return prefix_lengths, res

def partition(prefixes):
    ''' Collect some stats about the fraction of IPv4 space covered
        by prefixes.

        Return: 
            covered_space (all networks merged where contiguous, 
                            can randomly subsample IPs from this space),
            fraction_covered (what fraction of IPv4 space is covered by prefixes),
            prefix_lens (list of IPSets for each prefix length), 
            space_by_plen (list of fractions of space covered by each
                            prefix length relative to covered_space)
    '''
    all_prefixes = [network for (network, _, _) in prefixes]
    # add all networks to set
    # calculate size of set and fraction of total IPv4 space covered
    covered_space = net.IPSet(all_prefixes)
    fraction_covered = len(covered_space) / (2**32) # not worrying about reserved addresses

    # do sets for each prefix length and calculate size (make sure to calculate difference!)
    prefix_lens = [net.IPSet([]) for plen in range(33)]
    for triple in prefixes:
        network, plen, _ = triple
        prefix_lens[plen].add(net.IPNetwork(network))
    space_by_plen = [0 for i in range(33)]
    for plen, pset in enumerate(prefix_lens):
        # more specific prefixes take precedence over less specific ones
        precedence_pset = reduce((lambda x, y: x.union(y)), prefix_lens[plen+1:])
        plen_space = pset.difference(precedence_pset)
        space_by_plen[plen] = len(plen_space) / len(covered_space)

    # verify space covered by each prefix length adds up to space covered by all prefixes
    print('fraction covered by each prefix:', space_by_plen)
    print('adds up to 1.0?', sum(space_by_plen))
    input('continue?')

    return covered_space, fraction_covered, prefix_lens, space_by_plen

if __name__ == "__main__":
    # extract addresses
    # prefix_lengths = parse_APNIC('v4')
    prefix_lengths, prefixes = parse_oregon('v4')
    print(prefix_lengths)

    # collect basic stats:
    #   total number of prefixes, number/fraction for each length
    totals = sum(prefix_lengths) # total number of prefixes in table
    fractions = [num/totals for num in prefix_lengths] # fraction of each prefix length

    # partitions of address space by prefix length

    covered_space, fraction_covered, prefix_lens, space_by_plen =\
            partition(prefixes)

    # plot the distribution of IP prefixes (do for both BGP tables)
    pass
    # plot the fractions of space covered by prefix length
    pass

    # generate traffic:
    #   randomly (assuming default if not found)
    pass
    #   randomly but only from IP space covered by prefixes
    pass
    #   in proportion to address space covered by given prefix length
    pass
    #   in proportion to number fraction of each prefix length (only from covered address space)
    pass
