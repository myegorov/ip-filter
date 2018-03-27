'''
Compute optimal binary search tree with various weighting functions:
    - equal weights (balanced tree)
    - weights correlated with prefix count
    - weights correlated with prefix IP address space share

Using Knuth's dynamic programming algorithm.
'''

import os
from sys import maxsize
from conf import *

class Node:
    def __init__(self, val, left=None, right=None):
        '''val is the prefix length;
           left and right are tree Nodes
        '''
        self.val = val
        self.left=left
        self.right=right

def weigh_equally(protocol='v4'):
    '''Return equal weights for all represented prefix lengths:
        [(1.0, valid_pref_len), ..., (1.0, valid_pref_len)]
    '''
    filtered = weigh_by_prefix_count(protocol=protocol, skiplines=0)
    return [(1.0, pref_len) for (_,pref_len) in filtered]

def weigh_by_prefix_count(protocol='v4', skiplines=0):
    '''Return weights for all represented prefix lengths by fraction
        of prefixes of that length:
        [(fraction, valid_pref_len), ..., (fraction, valid_pref_len)]
    '''
    with open(os.path.join(TRAFFICDIR, 'ip'+protocol, STATSFILE), 'r') as infile:
        for i in range(skiplines): infile.readline()
        line = infile.readline().strip().split(',')[1:]
        pref_fractions = [float(prefix_len) for prefix_len in line]
        zipped = zip(pref_fractions, list(range(len(pref_fractions))))
        return list(filter(lambda pair: pair[0]>0, zipped))

def weigh_by_prefix_range(protocol='v4'):
    '''Return weights for all represented prefix lengths by fraction
        of IP address space covered by prefixes of that length:
        [(fraction, valid_pref_len), ..., (fraction, valid_pref_len)]
    '''
    return weigh_by_prefix_count(protocol=protocol, skiplines=1)

def _construct_w_tab(weights):
    '''Construct and return upper triangular weight matrix: (n+1) x (n+1)
    '''
    p = [w for w,_ in weights]
    mat = [[0.0 for i in range(len(weights)+1)] for j in range(len(weights)+1)]
    for i in range(len(weights)):
        for j in range(i, len(weights), 1):
            mat[i][j+1] = mat[i][j] + p[j]
    return mat

def _construct_tabs(weights):
    '''Construct and return upper triangular weight (w), expected cost (e)
        and optimal subtree root (r) matrices, each (n+1) x (n+1).
    '''
    w = _construct_w_tab(weights)
    # initialize optimal subtree root table (when row == col, None signals to stop iteration)
    r = [[None for i in range(len(weights)+1)] for j in range(len(weights)+1)]
    # initialize expected costs to very large num
    e = [[maxsize for i in range(len(weights)+1)] for j in range(len(weights)+1)]
    for i in range(len(weights)):
        e[i][i] = 0.0
        e[i][i+1] = weights[i][0]
        r[i][i+1] = i+1
    e[len(e)-1][len(e)-1] = 0.0

    for l in range(len(weights)+1):
        for i in range(len(weights)+1-l):
            j = i + l
            for root in range(i+1, j+1, 1):
                t = e[i][root-1] + e[root][j] + w[i][j]
                if t < e[i][j]:
                    e[i][j] = t
                    # r[i][j] = root-1
                    r[i][j] = root
    return w, e, r

def _build_optimal_bin_search_tree(r, weights):
    '''Construct optimal binary search tree from the optimal root matrix (r).
        Caveat: this functions modifies the r matrix in place.
    '''
    minn, maxx = 0, len(r)-1
    root = Node(r[0][-1])
    root.left = _build_helper(r, minn=minn, maxx=root.val-1)
    root.right = _build_helper(r, minn=root.val, maxx=maxx)

    # postprocess the tree from weights in place
    _remap(root, weights)
    return root

def _build_helper(r, minn, maxx):
    if minn >= maxx: 
        return None # base case
    subroot = Node(r[minn][maxx])
    subroot.left = _build_helper(r, minn=minn, maxx=subroot.val-1)
    subroot.right = _build_helper(r, minn=subroot.val, maxx=maxx)
    return subroot

def _remap(tree, weights):
    if tree is None: return
    tree.val = weights[tree.val-1][1]
    _remap(tree.left, weights)
    _remap(tree.right, weights)

def _graphviz(tree):
    '''Returns a Graphviz string similar to:
        digraph BST {
            node [fontname="Arial"];
            15 -> 6;
            null0 [shape=point];
            6 -> null0;
            null1 [shape=point];
            6 -> null1;
            15 -> 18;
            18 -> 17;
            null2 [shape=point];
            17 -> null2;
            null3 [shape=point];
            17 -> null3;
            null4 [shape=point];
            18 -> null4;
        }
    '''
    if not tree: return ''
    res = ['digraph BST {']
    res.append('node [fontname="Arial"];')

    if not (tree.left or tree.right):
        res.append('%d;' %tree.val)
    else:
        res.extend(_tree2str(tree))
    res.append('}')
    return '\n'.join(res)

def _tree2str(tree):
    if tree is None: 
        return ''
    else:
        res = []
        if tree.left is not None:
            res.append('%d -> %d;' %(tree.val, tree.left.val))
            res.extend(_tree2str(tree.left))
        if tree.right is not None:
            res.append('%d -> %d;' %(tree.val, tree.right.val))
            res.extend(_tree2str(tree.right))
        return res

def _output(tree, protocol='v4', fname='balanced_tree.dot'):
    dotgraph = _graphviz(tree)
    with open(os.path.join(IMGDIR, 'ip'+protocol, fname), 'w') as outfile:
        outfile.write(dotgraph)

def obst(protocol='v4', weigh=weigh_equally, plot=False, fname='tree.dot'):
    '''Return balanced tree. Optionally output .dot file for Graphviz.
    '''
    weights = (weigh(protocol=protocol))
    w, e, r = _construct_tabs(weights)

    # construct the tree
    tree = _build_optimal_bin_search_tree(r, weights)
    if plot:
        _output(tree, protocol=protocol, fname=fname)
    return tree

if __name__ == "__main__":
    '''Tests + plots.
    '''
    # balanced trees for IPv4 and IPv6
    balanced_tree_v4 = obst('v4', weigh_equally, plot=True, fname='balanced_tree.dot')
    balanced_tree_v6 = obst('v6', weigh_equally, plot=True, fname='balanced_tree.dot')

    # weights correlated with prefix count
    prefcount_tree_v4 = obst('v4', weigh_by_prefix_count, plot=True, fname='prefix_count_tree.dot')
    prefcount_tree_v6 = obst('v6', weigh_by_prefix_count, plot=True, fname='prefix_count_tree.dot')

    # weights correlated with prefix IP address space share
    addrshare_tree_v4 = obst('v4', weigh_by_prefix_range, plot=True, fname='prefix_addrshare_tree.dot')
    addrshare_tree_v6 = obst('v6', weigh_by_prefix_range, plot=True, fname='prefix_addrshare_tree.dot')
