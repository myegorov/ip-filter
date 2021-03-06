'''
Generate traffic for testing.
Format:
    ip_int ip_str
    16909060 1.2.3.4

Traffic patterns:
- random (default path may or may not be covered by prefix),
    use this case for comparing IPv4 vs IPv6;
- random but only from IP space covered by prefixes (only for BGP table
    where no default exists, i.e. for IPv4 table -- will naturally
    correlate with addres space coverage by given prefix length,
    impractical for IPv6);
- in proportion to fraction of each prefix length out of total count for
    the prefix length (IP selected only from covered address space,
    impractical for IPv6);

Usage:
    python3 generate_traffic.py
'''

# TODO: (2) and (3) are impractical for IPv6 because of vast space
#       may need to do some quick and dirty sampling from prefix space instead


from preprocess_bgp_tables import parse_oregon, partition
import os
from conf import *
import netaddr as net
import random

MAXINT = {
    'v4': net.IPNetwork('0.0.0.0/0').last,
    'v6': net.IPNetwork('::/0').last
}

SIZE = int(1e7) # number of IPs (packets) in traffic to test on

def generate_random(size=SIZE, protocol='v4'):
    '''Generate traffic (IPs) from the entire IP address space.

        Returns list of pairs (ip_int, ip_str):
            [(16909060, '1.2.3.4'),...]
    '''
    res = []
    print('\nGenerating traffic...')
    for i in range(size):
        num = random.randint(0,MAXINT[protocol])
        addr = net.IPAddress(num).ipv4() if protocol=='v4'\
                else net.IPAddress(num).ipv6()
        res.append((num, str(addr)))
    return res

def generate_by_fraction_of_space(ipset, size=SIZE, protocol='v4'):
    ''' Receives set of IP networks covered by prefixes 
        (only select IPs from address range covered by prefixes).
        Traffic correlates with proportion of IP address space
        covered by prefixes.

        Returns list of pairs (ip_int, ip_str):
            [(16909060, '1.2.3.4'),...]
    '''

    # use reservoir sampling
    # https://en.wikipedia.org/wiki/Reservoir_sampling
    # only generate from the ipset
    print('\nGenerating address range...')
    print('ipset.size:', ipset.size)
    print('Will generate %d IPs...' %size)
    reservoir, i = [], -1
    for ip in ipset:
        if i % 1000000 == 0: print('processed %.5f of address space' %(i/ipset.size))
        i += 1
        if i < size:
            reservoir.append(ip)
            continue
        j = random.randint(0,i)
        if j < size:
            reservoir[j] = ip

    print('\nGenerating traffic...')
    res = [(net.IPAddress(ip).__long__(), str(ip)) for ip in reservoir]
    random.shuffle(res)
    return res

def generate_traffic(protocol='v4'):
    print('\n-> Working on traffic for protocol %s' %protocol)
    # (1) random traffic (assuming default path exists)
    random_traffic_with_default = generate_random(protocol=protocol)
    output(random_traffic_with_default, protocol=protocol,
           fname='random_traffic_with_default.txt')

    # TODO: (2) and (3) are impractical for IPv6 because of vast space
    #       may need to do some quick and dirty sampling from prefix space instead
    if protocol == 'v6': return
    # (2) generate traffic only from IP space covered by prefixes
    # --> in proportion to address space covered by given prefix length

    # extract addresses
    prefixes = parse_oregon(protocol=protocol)

    # partitions of address space by prefix length
    ipset_covered_by_prefixes, fraction_covered, ipsets_for_each_prefix_length =\
            partition(prefixes, protocol=protocol)

    traffic_correlated_with_space = generate_by_fraction_of_space(
            ipset_covered_by_prefixes,
            protocol=protocol)
    output(traffic_correlated_with_space, protocol=protocol,\
           fname='traffic_correlated_with_space.txt')

    # (3) generate traffic in proportion to fraction of each prefix length
    #   out of total count (IP selected only from covered address space)
    prefix_lens_tight, space_by_prefix_length, count_by_prefix_length =\
            zip(*ipsets_for_each_prefix_length)
    totals = sum(count_by_prefix_length) # total number of prefixes in table
    # number of samples to generate from fraction of each prefix length
    fraction_count_by_prefix_length =\
            [round(SIZE * (num/totals)) for num in count_by_prefix_length]
    traffic_correlated_with_prefix_count = []
    for i in range(len(fraction_count_by_prefix_length)):
        print('\nGenerating IPs for prefix length %d...' %i)
        if fraction_count_by_prefix_length[i] == 0: continue
        traffic_correlated_with_prefix_count.extend(
            generate_by_fraction_of_space(
                prefix_lens_tight[i],
                size=fraction_count_by_prefix_length[i],
                protocol=protocol)
        )
    output(traffic_correlated_with_prefix_count, protocol=protocol,\
           fname='traffic_correlated_with_prefix_count.txt')

def output(ips, protocol='v4', fname='random_traffic_with_default.txt'):
    print('\nWriting traffic to file...')
    with open(os.path.join(TRAFFICDIR, 'ip'+protocol, fname), 'w') as outfile:
        outfile.write('\n'.join('%d %s' %pair for pair in ips))

if __name__ == "__main__":
    generate_traffic('v4')
    generate_traffic('v6')
