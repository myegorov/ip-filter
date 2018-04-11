import matplotlib.pyplot as plt
import sys
import os
from mconf import *
for d in [DATADIR]:
    sys.path.append(d)


def plot_vbar(x, y, outdir=EXPERIMENTS, outfile='stats.png', title='Count vs. Measure',
              y_logscale=True, xlabel='metric', ylabel='count'):
    ''' Plot bar graph of x vs y.
    '''
    print("\nPlotting the stats to %s" %(os.path.join(outdir, outfile)))
    fig, ax = plt.subplots()
    width = 0.5
    for ys in y:
        ax.bar(x, ys, width, color="red")
    if y_logscale:
        ax.set_yscale('log')

    # plt.xticks(range(x[0], x[-1]+1, len(x)//16), rotation=45)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.savefig(os.path.join(outdir, outfile), format='png',
                bbox_inches='tight')
