#!/usr/bin/env python3
'''setup.py

Set up project directory structure.
Synthesize traffic for experiments.
Run experiments on the prototype implementation.
'''
import os, sys
from pathlib import Path

PROJDIR = os.path.dirname(os.path.realpath(__file__))
for d in ['data', 'prototype']:
    sys.path.append(os.path.join(PROJDIR, d))

from data import conf, preprocess_bgp_tables, generate_traffic
from prototype import mconf, driver
import wget


IPv4_TAB = 'http://bgp.potaroo.net/as6447/bgptable.txt' # IPv4 BGP table: AS6447, Route-Views.Oregon-ix.net
IPv6_TAB = 'http://bgp.potaroo.net/v6/as6447/bgptable.txt' # IPv6 BGP table: AS6447, Route-Views.Oregon-ix.net	

def setup_dirs():
    '''Test everything is in place...
    '''
    print('Setting up project directory tree...')
    for d in [conf.RAWDIR, conf.OUTDIR, conf.IMGDIR, conf.TRAFFICDIR,
              conf.IPv4_AS6447, conf.IPv6_AS6447, mconf.EXPERIMENTS,
              mconf.IPV4DIR, mconf.IPV6DIR]:
        if not os.path.isdir(d):
            Path(d).mkdir(parents=True, exist_ok=True)
        if not all([os.access(d, os.R_OK), os.access(d, os.W_OK)]):
            raise ValueError(
                "\nCannot read {0} directory".format(d))

    for d in [conf.ROOTDIR, mconf.CURDIR]:
        if not os.path.isdir(d):
            raise ValueError(
                "\n{0} directory does not exist".format(d))
        if not os.access(d, os.X_OK):
            raise ValueError(
                "\nCannot access scripts under {0} directory".format(d)
            )

def download_bgp_tables():
    print('...downloading Oregon IPv4 table...')
    wget.download(IPv4_TAB, os.path.join(conf.IPv4_AS6447, conf.BGPTAB))

    print('...downloading Oregon IPv6 table...')
    wget.download(IPv6_TAB, os.path.join(conf.IPv6_AS6447, conf.BGPTAB))
    print('Downloaded raw BGP tables.')

def run_experiments():
    print('Finally, will run experiments...')

    # for both IPv4 and IPv6
    driver.test_traffic_patterns()
    fib, traffic, pref_stats = driver._common_prep(protocol='v4', traffic_pattern=mconf.RANDOM_TRAFFIC)
    driver.test_bitarray_size(fib, traffic, pref_stats)
    driver.test_num_hash_funcs(fib, traffic, pref_stats)
    print('All done. Find plots under %s' %mconf.EXPERIMENTS)

if __name__ == "__main__":

    # set up project directory structure
    setup_dirs()

    # download BGP tables
    download_bgp_tables()

    # preprocess raw BGP tables
    print('Will now preprocess BGP tables for input into FIB...')
    for protocol in ['v4', 'v6']:
        preprocess_bgp_tables.preprocess(protocol)
    print('Done preprocessing BGP tables!\n\n')

    # synthesize traffic for experiments
    print('Will now generate IPv4 and IPv6 traffic. Takes a while...')
    for protocol in ['v4', 'v6']:
        generate_traffic.generate_traffic(protocol)
    print('Done generating traffic!\n\n')

    # run experiments on the prototype implementation
    run_experiments()
