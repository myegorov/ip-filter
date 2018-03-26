import os

ROOTDIR = os.path.dirname(os.path.realpath(__file__))
RAWDIR = os.path.join(ROOTDIR,'raw')
OUTDIR = os.path.join(ROOTDIR,'out')
IMGDIR = os.path.join(OUTDIR, 'img')
TRAFFICDIR = os.path.join(OUTDIR, 'traffic')

BGPTAB = 'bgptable.txt' # file name

# IPv4
IPv4_AS65000 = os.path.join(RAWDIR, 'ipv4', 'as2.0') # http://bgp.potaroo.net/as2.0/bgp-active.html
IPv4_AS6447 = os.path.join(RAWDIR, 'ipv4', 'as6447') # http://bgp.potaroo.net/as6447/

# IPv6
IPv6_AS65000 = os.path.join(RAWDIR, 'ipv6', 'as2.0') # http://bgp.potaroo.net/v6/as2.0/index.html
IPv6_AS6447 = os.path.join(RAWDIR, 'ipv6', 'as6447') # http://bgp.potaroo.net/v6/as6447/
