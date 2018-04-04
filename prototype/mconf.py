import os
import sys

CURDIR = os.path.dirname(os.path.realpath(__file__))
PROOTDIR = os.path.dirname(CURDIR)

DATADIR = os.path.join(PROOTDIR,'data')
IPV4DIR = os.path.join(DATADIR, 'out', 'traffic', 'ipv4')
IPV6DIR = os.path.join(DATADIR, 'out', 'traffic', 'ipv6')

PREFIX_FILE = 'bgptable.txt'
RANDOM_TRAFFIC = 'random_traffic_with_default.txt'
PREF_COUNT_TRAFFIC = 'traffic_correlated_with_prefix_count.txt'
PREF_SPACE_TRAFFIC = 'traffic_correlated_with_space.txt'
