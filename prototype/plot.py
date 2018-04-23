import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from mconf import *
for d in [DATADIR]:
    sys.path.append(d)


def plot_vbar(x, y, outdir=EXPERIMENTS, outfile='stats.png', title='Count of function invocations vs. Measure',
              y_logscale=True, xlabel='metric', ylabel='count'):
    ''' Plot bar graph of x vs y.
    '''
    print("\nPlotting the stats to %s" %(os.path.join(outdir, outfile)))
    fig, axs = plt.subplots(2,1)

    # if y_logscale:
    #     axs[1].set_yscale('log')

    collabel = ['method'] + x
    tab_lines = [['%.1f' %num for num in y[i]] for i in range(2)]
    tab_lines[0].insert(0, 'linear')
    tab_lines[1].insert(0, 'guided')

    axs[0].axis('tight')
    axs[0].axis('off')
    the_table = axs[0].table(cellText=tab_lines,colLabels=collabel,loc='center')

    ind = np.arange(len(x))
    width = 0.35

    rects1 = axs[1].bar(ind, y[0], width, color='r')
    rects2 = axs[1].bar(ind+width, y[1], width, color='b')

    axs[1].set_ylabel(ylabel)
    axs[1].set_xlabel(xlabel)
    axs[1].set_title(title)

    axs[1].set_xticks(ind+ width/2)
    axs[1].set_xticklabels(x)

    axs[1].legend((rects1[0], rects2[0]), ('linear', 'guided'))

    plt.savefig(os.path.join(outdir, outfile), format='svg',
                bbox_inches='tight', dpi=300)

def plot_scatter(seqs, res, outfile, title, xlabel, ylabel, 
                 outdir=EXPERIMENTS, x_logscale=True,
                 y_logscale=True, key='percent_full'):

    print("\nPlotting the stats to %s" %(os.path.join(outdir, outfile)))

    # munge the data
    linear = [[i for j in range(len(seqs))] for i in res['linear'][key]]
    guided = [[i for j in range(len(seqs))] for i in res['guided'][key]]
    lseries = list(zip(linear, res['linear']['ncalls']))
    gseries = list(zip(guided, res['guided']['ncalls']))

    fig, ax = plt.subplots()
    colors = ['r', 'b']
    colors_l = ['red', 'sienna', 'plum', 'crimson']
    colors_g = ['b', 'cyan', 'teal', 'skyblue']

    ltmp = [[] for i in range(len(seqs))]
    for i in range(len(lseries)):
        for j in range(len(lseries[0][0])):
            ltmp[j].append((lseries[i][0][j], lseries[i][1][j]))

    gtmp = [[] for i in range(len(seqs))]
    for i in range(len(gseries)):
        for j in range(len(gseries[0][0])):
            gtmp[j].append((gseries[i][0][j], gseries[i][1][j]))

    for i, label in enumerate(seqs):
        lser = ltmp[i]
        gser = gtmp[i]
        lxs, lys = zip(*lser)
        gxs, gys = zip(*gser)
        ax.scatter(lxs, lys, c=colors_l[i], label=label+' linear', alpha=0.5, edgecolors='none')
        ax.scatter(gxs, gys, c=colors_g[i], label=label+' guided', alpha=0.8, edgecolors='none')
    ax.legend()
    ax.grid(True)

    if x_logscale:
        ax.set_xscale('log')
    # if y_logscale:
    #     ax.set_yscale('log')

    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_title(title)

    plt.savefig(os.path.join(outdir, outfile), format='svg',
                bbox_inches='tight', dpi=300)

if __name__ == "__main__":
    seqs = ['bit lookup', 'hashing', 'FIB lookup', '%% traffic defaulting']
    ofile = 'bitarraySize_random.png'
    title = 'Count of function invocations by metric type: bitarray size'
    xlabel = '%% bitarray full'
    ylabel = 'count'
    res = {'linear': {'percent_full': [0.05, 0.1, 0.5, 0.9], 'ncalls': [[1,2,3,4], [10,20,30,40], [100,200,300,400], [1000,2000,3000,4000]], 'bf': ['a','b','c','d']},
           'guided': {'percent_full': [0.15, 0.2, 0.8, 0.99], 'ncalls': [[1,2,3,4], [2,3,4,5], [3,4,5,6], [4,5,6,7]], 'bf': ['a','b','c','d']}}
    plot_scatter(seqs, res, ofile, title, xlabel, ylabel, key='percent_full')
