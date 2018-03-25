'''
Generate traffic for testing.
Format:
    prefix_int prefix_length cidr_network
    16909060 32 1.2.3.4/32

Traffic patterns:
- random (assuming default path if not covered by prefix)
- random but only from IP space covered by prefixes (only for BGP table
    where no default exists, i.e. for IPv4 table)
- in proportion to address space covered by given prefix length
- in proportion to fraction of each prefix length out of total count for
    the prefix length (IP selected only from covered address space)
'''

