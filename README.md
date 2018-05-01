ip-filter
===========

An adaptation of the [Bloom filter](https://en.wikipedia.org/wiki/Bloom_filter)
for use with [core router](https://en.wikipedia.org/wiki/Core_router)
[forwarding tables](https://en.wikipedia.org/wiki/Forwarding_information_base).

Longest prefix matching has long been the bottleneck of the Bloom
filter-based solutions for packet forwarding implemented in software.
We prototype a search algorithm that allows for a compact representation of 
the FIB table in cache on general purpose CPUs with an average performance
target of _O(log n)_, where _n_ is _max(l,b)_, for `b`-bit IP addresses and
`l` distinct outgoing links in the FIB table.


## Docs

For up-to-date documentation, see `./doc/tex/report.pdf`

## Quick Start

Requires Python 3.

To set up the project tree, download BGP tables, synthesize traffic for 
experiments, and run experiments profiling the relative performance of
the traditional _linear_ search against the _guided_ search scheme:

```shell
pip3 install -r requirements.txt
./setup.py
```
