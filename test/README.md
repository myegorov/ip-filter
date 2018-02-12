In brief, I haven't been able to improve beyond what GCC optimization provides.
I'm still studying what's going on using [cachegrind](http://valgrind.org/docs/manual/cg-manual.html).
it seems that the CPU knows better and all prefetching ends up being
additional overhead. Refer to numbers below: we'd want the prefetched version
to have fewer misses at the expense of more loads. In reality, both
loads and misses increase for the prefetched version, which suggests
superfluous loads evicting data from cache.

I've tried disabling GCC optimization (`-O0`), but
that doesn't help. Interestingly, if I run the default vs prefetched experiments
through `valgrind`, the prefetched version runs 3x faster, not sure why the difference.


Experiment:
enter 0.5 million keys into a bloom filter, then query the filter for same keys

    target number of keys: 500,006
    target false positive probability: 1e-6
    number of hash functions: 20
    bit array size: 14,377,768 bits (1.7 MB)

I've used the GCC built-in for prefetching:
[__builtin_prefetch (const void *addr, ...)](https://gcc.gnu.org/onlinedocs/gcc-5.3.0/gcc/Other-Builtins.html)
    This function is used to minimize cache-miss latency by moving data into a
    cache before it is accessed. You can insert calls to __builtin_prefetch into
    code for which you know addresses of data in memory that is likely to be
    accessed soon. If the target supports them, data prefetch instructions are
    generated. If the prefetch is done early enough before the access then the data
    will be in the cache by the time it is accessed.


Scenarios tried:

1. no prefetching (default):

    for each ip:
      for each hash function:
        test bitarray[hash]

```shell

$ make simple
$ ./simple

...
500006 queries took 0.094916 seconds

$ perf stat -e L1-dcache-load-misses,L1-dcache-loads ./simple

...
Performance counter stats for './simple':

20,747,962      L1-dcache-load-misses:u   #   12.52% of all L1-dcache hits
165,686,262      L1-dcache-loads:u

0.280499022 seconds time elapsed
```

2. short-look-ahead scenario: prefetch next hash of current ip (also tried > 1 next hashes)

    for each ip:
      for each hash function:
        (1) test bitarray[hash]
        (2) compute next_hash and prefetch (& bitarray[next_hash]) into L1 cache

```shell
$ make prefetch
$ ./prefetch

...
500006 queries took 0.105393 seconds
$ perf stat -e L1-dcache-load-misses,L1-dcache-loads ./simple

...
Performance counter stats for './prefetch':

21,012,068      L1-dcache-load-misses:u   #   11.96% of all L1-dcache hits
175,699,283      L1-dcache-loads:u

0.284112410 seconds time elapsed
```

3. long-look-ahead scenario: prefetch all k hashes of next ip while 
testing current ip (no prefetching for current ip)

    for each (ip, next_ip) pair:
      (1) for each hash function:
        compute hash(next_ip) and prefetch (& bitarray[hash]) into L1 cache
      (2) for each hash function
        compute hash(ip) & test bitarray[hash]


L1-dcache-load-misses essentially unchanged from default scenario (1, no-prefetching)
L1-dcache-loads increase, as expected.
Runtime increases significantly above prefetching scenario (2), because of
all the extra (wasted) hashing computations on next_ip.


4. Do constant hashing work for nothing (must be eliminated as unused by
the compiler, hence the drastic reduction in run time).
Repeatedly look up same index in bitarray, no explicit pre-fetching:

There're 1e7 fewer L1-dcache-loads and 1e7 fewer L1-dcache-load-misses.
Keep in mind we have 0.5e6 entries x 20 hash lookups per entry = 1e7.
I.e. nothing happening in loop.

$ make pseudo
$ ./pseudo

...
500006 queries took 0.007698 seconds
$ perf stat -e L1-dcache-load-misses,L1-dcache-loads ./pseudo


500006 queries took 0.007671 seconds

Performance counter stats for './pseudo':

10,917,399      L1-dcache-load-misses:u   #    7.13% of all L1-dcache hits
153,129,271      L1-dcache-loads:u

0.193881172 seconds time elapsed


5. Do not re-compute hashes. Repeatedly look up same index in bitarray, no explicit
pre-fetching.

We've now eliminated hash computation for each key & no change in lookups.
The difference in loads must be due to eliminated storing of hashes for each key.


$ make pseudo
$ perf stat -e L1-dcache-load-misses,L1-dcache-loads ./idle

There're 1e7 fewer L1-dcache-loads and same number of L1-dcache-load-misses
compared to experiment (4).

...
Performance counter stats for './idle':

10,587,779      L1-dcache-load-misses:u   #    7.40% of all L1-dcache hits
143,167,774      L1-dcache-loads:u

0.183422218 seconds time elapsed
