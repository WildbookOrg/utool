# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
from utool import util_inject
(print, rrr, profile) = util_inject.inject2(__name__, '[depgraph_helpers]')


def testdata_graph():
    import networkx as nx
    import utool as ut
    # Define adjacency list
    graph = {
        'a': ['b'],
        'b': ['c', 'f', 'e'],
        'c': ['g', 'd'],
        'd': ['c', 'h'],
        'e': ['a', 'f'],
        'f': ['g'],
        'g': ['f'],
        'h': ['g', 'd'],
        'i': ['j'],
        'j': [],
    }
    graph = {
        'a': ['b'],
        'b': ['c'],
        'c': ['d'],
        'd': ['a', 'e'],
        'e': ['c'],
    }
    #graph = {'a': ['b'], 'b': ['c'], 'c': ['d'], 'd': ['a']}
    #graph = {'a': ['b'], 'b': ['c'], 'c': ['d'], 'd': ['e'], 'e': ['a']}
    #graph = {'a': ['b'], 'b': ['c'], 'c': ['d'], 'd': ['e'], 'e': ['b']}
    # Extract G = (V, E)
    nodes = list(graph.keys())
    edges = ut.flatten([[(v1, v2) for v2 in v2s] for v1, v2s in graph.items()])
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    if False:
        G.remove_node('e')
        del graph['e']

        for val in graph.values():
            try:
                val.remove('e')
            except ValueError:
                pass

    #ut.ensure_pylab_qt4()
    #pt.show_netx(G, layout='pygraphviz')
    return graph, G


def find_odd_cycle():
    r"""
    CommandLine:
        python -m utool.util_graph --exec-find_odd_cycle --show

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_graph import *  # NOQA
        >>> import utool as ut
        >>> result = find_odd_cycle()
        >>> print(result)
        >>> ut.show_if_requested()
    """
    import utool as ut
    graph, G = testdata_graph()

    seen_ = set()
    meta = {
        'clock': 0,
        'pre': {},
        'post': {},
        'pairity': ut.ddict(lambda : 0),
    }
    import sys

    def previsit(node):
        meta['pre'][node] = meta['clock']
        meta['clock'] += 1

    def postvisit(node):
        meta['post'][node] = meta['clock']
        meta['clock'] += 1

    def explore(graph, node, seen_):
        # Mark visited
        seen_.add(node)
        previsit(node)
        # Explore children
        children = graph[node]
        for child in children:
            if child not in seen_:
                meta['pairity'][child] = 1 - meta['pairity'][node]
                explore(graph, child, seen_)
            else:
                is_odd = meta['pairity'][child] == 1 - meta['pairity'][node]
                print('is_odd = %r' % (is_odd,))
                #sys.exit(0)
        postvisit(node)

    # Run pairity check on each scc
    # Then check all edges for equal pairity

    # Run Depth First Search
    for node in graph.keys():
        if node not in seen_:
            explore(graph, node, seen_)

    # Mark edge types
    #orderkeys = ['u[', 'v[', ']u', ']v']
    edge_types = {
        (0, 1, 3, 2): 'forward',
        (1, 0, 2, 3): 'back',
        (1, 3, 0, 2): 'cross',
    }
    # given any starting point in an scc
    # if there is an odd length cycle in the scc
    # then the starting node is part of the odd length cycle
    #
    # Let s* be part of the odd length cycle
    # Start from any point s
    # There is also a cycle from (s* to s) due to scc.
    # If that cycle is even, then go to s*, then go in the odd length cycle back to s*
    # and then go back to s, which makes this path odd.
    # If s s* s is odd we are done.
    #
    # because it is strongly connected there is a path from s* to s and
    # s to s*. If that cycle is odd then done otherwise,

    edge_labels = {}
    type_to_edges = ut.ddict(list)
    for u, v in G.edges():
        orders = [meta['pre'][u], meta['pre'][v], meta['post'][u], meta['post'][v]]
        sortx = tuple(ut.argsort(orders))
        #lbl = ut.take(orderkeys, sortx)
        #print(sortx)
        #print(' '.join(lbl))
        type_ = edge_types[sortx]
        edge_labels[(u, v)] = type_
        #print('type_ = %r' % (type_,))
        type_to_edges[type_].append((u, v))

    # Check back edges
    print('type_to_edges = %r' % (type_to_edges,))
    is_odd_list = []
    for back_edge in type_to_edges['back']:
        print('back_edge = %r' % (back_edge,))
        u, v = back_edge
        pre_v = meta['pre'][v]
        post_u = meta['post'][u]
        is_even = (post_u - pre_v) % 2 == 0
        is_odd = not is_even
        is_odd_list.append(is_odd)

    # Visualize the graph
    node_labels = {
        #node: (meta['pre'][node], meta['post'][node])
        node: (meta['pairity'][node])
        for node in graph
    }

    import networkx as nx
    import plottool as pt
    scc_list = list(nx.strongly_connected_components(G))

    node_colors = {node: color for scc, color in zip(scc_list, pt.distinct_colors(len(scc_list))) for node in scc}
    nx.set_node_attributes(G, 'label', node_labels)
    nx.set_node_attributes(G, 'color', node_colors)
    #nx.set_edge_attributes(G, 'label', edge_labels)

    ut.ensure_pylab_qt4()
    #pt.figure(pt.next_fnum())
    pt.show_netx(G, layout='pygraphviz')

    #dfs(G)


def dict_depth(dict_, accum=0):
    if not isinstance(dict_, dict):
        return accum
    return max([dict_depth(val, accum + 1)
                for key, val in dict_.items()])


def edges_to_adjacency_list(edges):
    import utool as ut
    children_, parents_ = list(zip(*edges))
    parent_to_children = ut.group_items(parents_, children_)
    #to_leafs = {tablename: path_to_leafs(tablename, parent_to_children)}
    return parent_to_children


def get_ancestor_levels(graph, tablename):
    import networkx as nx
    import utool as ut
    root = nx.topological_sort(graph)[0]
    reverse_edges = [(e2, e1) for e1, e2 in graph.edges()]
    child_to_parents = ut.edges_to_adjacency_list(reverse_edges)
    to_root = ut.paths_to_root(tablename, root, child_to_parents)
    from_root = ut.reverse_path(to_root, root, child_to_parents)
    ancestor_levels_ = ut.get_levels(from_root)
    ancestor_levels = ut.longest_levels(ancestor_levels_)
    return ancestor_levels


def get_descendant_levels(graph, tablename):
    #import networkx as nx
    import utool as ut
    parent_to_children = ut.edges_to_adjacency_list(graph.edges())
    to_leafs = ut.path_to_leafs(tablename, parent_to_children)
    descendant_levels_ = ut.get_levels(to_leafs)
    descendant_levels = ut.longest_levels(descendant_levels_)
    return descendant_levels


def paths_to_root(tablename, root, child_to_parents):
    """

    CommandLine:
        python -m utool.util_graph --exec-paths_to_root:0
        python -m utool.util_graph --exec-paths_to_root:1

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_graph import *  # NOQA
        >>> import utool as ut
        >>> child_to_parents = {
        >>>     'chip': ['dummy_annot'],
        >>>     'chipmask': ['dummy_annot'],
        >>>     'descriptor': ['keypoint'],
        >>>     'fgweight': ['keypoint', 'probchip'],
        >>>     'keypoint': ['chip'],
        >>>     'notch': ['dummy_annot'],
        >>>     'probchip': ['dummy_annot'],
        >>>     'spam': ['fgweight', 'chip', 'keypoint']
        >>> }
        >>> root = 'dummy_annot'
        >>> tablename = 'fgweight'
        >>> to_root = paths_to_root(tablename, root, child_to_parents)
        >>> result = ut.repr3(to_root)
        >>> print(result)
        {
            'keypoint': {
                'chip': {
                        'dummy_annot': None,
                    },
            },
            'probchip': {
                'dummy_annot': None,
            },
        }

    Example:
        >>> from utool.util_graph import *  # NOQA
        >>> import utool as ut
        >>> root = u'annotations'
        >>> tablename = u'Notch_Tips'
        >>> child_to_parents = {
        >>>     'Block_Curvature': [
        >>>         'Trailing_Edge',
        >>>     ],
        >>>     'Has_Notch': [
        >>>         'annotations',
        >>>     ],
        >>>     'Notch_Tips': [
        >>>         'annotations',
        >>>     ],
        >>>     'Trailing_Edge': [
        >>>         'Notch_Tips',
        >>>     ],
        >>> }
        >>> to_root = paths_to_root(tablename, root, child_to_parents)
        >>> result = ut.repr3(to_root)
        >>> print(result)
    """
    if tablename == root:
        return None
    parents = child_to_parents[tablename]
    return {parent: paths_to_root(parent, root, child_to_parents)
            for parent in parents}


def path_to_leafs(tablename, parent_to_children):
    children = parent_to_children[tablename]
    if len(children) == 0:
        return None
    return {child: path_to_leafs(child, parent_to_children)
            for child in children}


def get_allkeys(dict_):
    import utool as ut
    if not isinstance(dict_, dict):
        return []
    subkeys = [[key] + get_allkeys(val)
               for key, val in dict_.items()]
    return ut.unique_ordered(ut.flatten(subkeys))


def traverse_path(start, end, seen_, allkeys, mat):
    import utool as ut
    if seen_ is None:
        seen_ = set([])
    index = allkeys.index(start)
    sub_indexes = np.where(mat[index])[0]
    if len(sub_indexes) > 0:
        subkeys = ut.take(allkeys, sub_indexes)
        # subkeys_ = ut.take(allkeys, sub_indexes)
        # subkeys = [subkey for subkey in subkeys_
        #            if subkey not in seen_]
        # for sk in subkeys:
        #     seen_.add(sk)
        if len(subkeys) > 0:
            return {subkey: traverse_path(subkey, end, seen_, allkeys, mat)
                    for subkey in subkeys}
    return None


def reverse_path(dict_, root, child_to_parents):
    """
    CommandLine:
        python -m utool.util_graph --exec-reverse_path --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_graph import *  # NOQA
        >>> import utool as ut
        >>> child_to_parents = {
        >>>     'chip': ['dummy_annot'],
        >>>     'chipmask': ['dummy_annot'],
        >>>     'descriptor': ['keypoint'],
        >>>     'fgweight': ['keypoint', 'probchip'],
        >>>     'keypoint': ['chip'],
        >>>     'notch': ['dummy_annot'],
        >>>     'probchip': ['dummy_annot'],
        >>>     'spam': ['fgweight', 'chip', 'keypoint']
        >>> }
        >>> to_root = {
        >>>     'fgweight': {
        >>>         'keypoint': {
        >>>                 'chip': {
        >>>                             'dummy_annot': None,
        >>>                         },
        >>>             },
        >>>         'probchip': {
        >>>                 'dummy_annot': None,
        >>>             },
        >>>     },
        >>> }
        >>> reversed_ = reverse_path(to_root, 'dummy_annot', child_to_parents)
        >>> result = ut.repr3(reversed_)
        >>> print(result)
        {
            'dummy_annot': {
                'chip': {
                        'keypoint': {
                                    'fgweight': None,
                                },
                    },
                'probchip': {
                        'fgweight': None,
                    },
            },
        }
    """
    # Hacky but illustrative
    # TODO; implement non-hacky version
    allkeys = get_allkeys(dict_)
    mat = np.zeros((len(allkeys), len(allkeys)))
    for key in allkeys:
        if key != root:
            for parent in child_to_parents[key]:
                rx = allkeys.index(parent)
                cx = allkeys.index(key)
                mat[rx][cx] = 1
    end = None
    seen_ = set([])
    reversed_ = {root: traverse_path(root, end, seen_, allkeys, mat)}
    return reversed_


def get_levels(dict_, n=0, levels=None):
    r"""
    Args:
        dict_ (dict_):  a dictionary
        n (int): (default = 0)
        levels (None): (default = None)

    CommandLine:
        python -m utool.util_graph --test-get_levels --show
        python3 -m utool.util_graph --test-get_levels --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_graph import *  # NOQA
        >>> import utool as ut
        >>> from_root = {
        >>>     'dummy_annot': {
        >>>         'chip': {
        >>>                 'keypoint': {
        >>>                             'fgweight': None,
        >>>                         },
        >>>             },
        >>>         'probchip': {
        >>>                 'fgweight': None,
        >>>             },
        >>>     },
        >>> }
        >>> dict_ = from_root
        >>> n = 0
        >>> levels = None
        >>> levels_ = get_levels(dict_, n, levels)
        >>> result = ut.repr2(levels_, nl=1)
        >>> print(result)
        [
            ['dummy_annot'],
            ['chip', 'probchip'],
            ['keypoint', 'fgweight'],
            ['fgweight'],
        ]
    """
    if levels is None:
        levels_ = [[] for _ in range(dict_depth(dict_))]
    else:
        levels_ = levels
    if dict_ is None:
        return []
    for key in dict_.keys():
        levels_[n].append(key)
    for val in dict_.values():
        get_levels(val, n + 1, levels_)
    return levels_


def longest_levels(levels_):
    r"""
    Args:
        levels_ (list):

    CommandLine:
        python -m utool.util_graph --exec-longest_levels --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_graph import *  # NOQA
        >>> import utool as ut
        >>> levels_ = [
        >>>     ['dummy_annot'],
        >>>     ['chip', 'probchip'],
        >>>     ['keypoint', 'fgweight'],
        >>>     ['fgweight'],
        >>> ]
        >>> new_levels = longest_levels(levels_)
        >>> result = ('new_levels = %s' % (ut.repr2(new_levels, nl=1),))
        >>> print(result)
        new_levels = [
            ['dummy_annot'],
            ['chip', 'probchip'],
            ['keypoint'],
            ['fgweight'],
        ]
    """
    return shortest_levels(levels_[::-1])[::-1]
    # seen_ = set([])
    # new_levels = []
    # for level in levels_[::-1]:
    #     new_level = [item for item in level if item not in seen_]
    #     seen_ = seen_.union(set(new_level))
    #     new_levels.append(new_level)
    # new_levels = new_levels[::-1]
    # return new_levels


def shortest_levels(levels_):
    r"""
    Args:
        levels_ (list):

    CommandLine:
        python -m utool.util_graph --exec-shortest_levels --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_graph import *  # NOQA
        >>> import utool as ut
        >>> levels_ = [
        >>>     ['dummy_annot'],
        >>>     ['chip', 'probchip'],
        >>>     ['keypoint', 'fgweight'],
        >>>     ['fgweight'],
        >>> ]
        >>> new_levels = shortest_levels(levels_)
        >>> result = ('new_levels = %s' % (ut.repr2(new_levels, nl=1),))
        >>> print(result)
        new_levels = [
            ['dummy_annot'],
            ['chip', 'probchip'],
            ['keypoint', 'fgweight'],
        ]
    """
    seen_ = set([])
    new_levels = []
    for level in levels_:
        new_level = [item for item in level if item not in seen_]
        seen_ = seen_.union(set(new_level))
        if len(new_level) > 0:
            new_levels.append(new_level)
    new_levels = new_levels
    return new_levels


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m utool.util_graph --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
