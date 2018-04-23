ip-filter
===========

An adaptation of the [Bloom filter](https://en.wikipedia.org/wiki/Bloom_filter)
for use with [core router](https://en.wikipedia.org/wiki/Core_router)
[forwarding tables](https://en.wikipedia.org/wiki/Forwarding_information_base).

Longest prefix matching has long been the bottleneck of the Bloom
filter-based solutions for packet forwarding implemented in software.
We prototype a search algorithm that allows for a compact representation of 
the FIB table in cache on general purpose CPUs with an average performance
target of _O(log n)_ for `n`-bit IP addresses.


## Docs

For up-to-date documentation, see `./doc/tex/report.pdf`

## Quick Start

TBD...
