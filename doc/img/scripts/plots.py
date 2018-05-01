import matplotlib.pyplot as plt
import numpy as np
from math import log, ceil, e, pow
import os

def plot_scatter(xs, ys, title, xlabel, ylabel, outfile):

    # plt.scatter(xs, ys)
    plt.semilogy(xs, ys)

    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)
    plt.xticks([int(x) for x in xs if x%2==0]) # force integer xticks
    plt.grid(linestyle='dotted')

    plt.savefig(outfile, format='png',
                bbox_inches='tight', dpi=300)

if __name__ == "__main__":
    # plot default Bloom filter
    m = 28755176
    n = round(1e6)
    xs, ys = [0], [1]
    k = 10
    for i in range(20):
        xs.append(i+1)
        fpp = pow(1 - e**(-(i+1) / (m / n)), (i+1))
        ys.append(fpp)

    outfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'PvsK.png')
    plot_scatter(xs, ys, 'FPP vs. k', 'number of hash functions (k)', 'false positive probability (FPP)', outfile)

