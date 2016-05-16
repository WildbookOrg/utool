# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
from utool import util_inject
(print, rrr, profile) = util_inject.inject2(__name__, '[depgraph_helpers]')


def nx_transitive_reduction(G, mode=1):
    """
    References:
        https://en.wikipedia.org/wiki/Transitive_reduction#Computing_the_reduction_using_the_closure
        http://dept-info.labri.fr/~thibault/tmp/0201008.pdf
        http://stackoverflow.com/questions/17078696/im-trying-to-perform-the-transitive-reduction-of-directed-graph-in-python

    CommandLine:
        python -m utool.util_graph nx_transitive_reduction --show

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_graph import *  # NOQA
        >>> import utool as ut
        >>> import networkx as nx
        >>> G = nx.DiGraph([('a', 'b'), ('a', 'c'), ('a', 'e'),
        >>>                 ('a', 'd'), ('b', 'd'), ('c', 'e'),
        >>>                 ('d', 'e'), ('c', 'e'), ('c', 'd')])
        >>> G = testdata_graph()[1]
        >>> G_tr = nx_transitive_reduction(G, mode=1)
        >>> G_tr2 = nx_transitive_reduction(G, mode=1)
        >>> ut.quit_if_noshow()
        >>> import plottool as pt
        >>> G_ = nx.dag.transitive_closure(G)
        >>> pt.show_nx(G    , pnum=(1, 5, 1), fnum=1)
        >>> pt.show_nx(G_tr , pnum=(1, 5, 2), fnum=1)
        >>> pt.show_nx(G_tr2 , pnum=(1, 5, 3), fnum=1)
        >>> pt.show_nx(G_   , pnum=(1, 5, 4), fnum=1)
        >>> pt.show_nx(nx.dag.transitive_closure(G_tr), pnum=(1, 5, 5), fnum=1)
        >>> ut.show_if_requested()
    """

    import utool as ut
    import networkx as nx
    has_cycles = not nx.is_directed_acyclic_graph(G)
    if has_cycles:
        # FIXME: this does not work for cycle graphs. Need to do algorithm on SCCs
        G_orig = G
        G = nx.condensation(G_orig)

    nodes = list(G.nodes())
    node2_idx = ut.make_index_lookup(nodes)

    # For each node u, perform DFS consider its set of (non-self) children C.
    # For each descendant v, of a node in C, remove any edge from u to v.

    if mode == 1:
        G_tr = G.copy()

        for parent in G_tr.nodes():
            # Remove self loops
            if G_tr.has_edge(parent, parent):
                G_tr.remove_edge(parent, parent)
            # For each child of the parent
            for child in list(G_tr.successors(parent)):
                # Preorder nodes includes its argument (no added complexity)
                for gchild in list(G_tr.successors(child)):
                    # Remove all edges from parent to non-child descendants
                    for descendant in nx.dfs_preorder_nodes(G_tr, gchild):
                        if G_tr.has_edge(parent, descendant):
                            G_tr.remove_edge(parent, descendant)

        if has_cycles:
            # Uncondense graph
            uncondensed_G_tr = G.__class__()
            mapping = G.graph['mapping']
            uncondensed_G_tr.add_nodes_from(mapping.keys())
            inv_mapping = ut.invert_dict(mapping, unique_vals=False)
            for u, v in G_tr.edges():
                u_ = inv_mapping[u][0]
                v_ = inv_mapping[v][0]
                uncondensed_G_tr.add_edge(u_, v_)

            for key, path in inv_mapping.items():
                if len(path) > 1:
                    directed_cycle = list(ut.itertwo(path, wrap=True))
                    uncondensed_G_tr.add_edges_from(directed_cycle)
            G_tr = uncondensed_G_tr

    else:

        def make_adj_matrix(G):
            edges = list(G.edges())
            edge2_idx = ut.partial(ut.dict_take, node2_idx)
            uv_list = ut.lmap(edge2_idx, edges)
            A = np.zeros((len(nodes), len(nodes)))
            A[tuple(np.array(uv_list).T)] = 1
            return A

        G_ = nx.dag.transitive_closure(G)

        A = make_adj_matrix(G)
        B = make_adj_matrix(G_)

        #AB = A * B
        #AB = A.T.dot(B)
        AB = A.dot(B)
        #AB = A.dot(B.T)

        A_and_notAB = np.logical_and(A, np.logical_not(AB))
        tr_uvs = np.where(A_and_notAB)

        #nodes = G.nodes()
        edges = list(zip(*ut.unflat_take(nodes, tr_uvs)))

        G_tr = G.__class__()
        G_tr.add_nodes_from(nodes)
        G_tr.add_edges_from(edges)

        if has_cycles:
            # Uncondense graph
            uncondensed_G_tr = G.__class__()
            mapping = G.graph['mapping']
            uncondensed_G_tr.add_nodes_from(mapping.keys())
            inv_mapping = ut.invert_dict(mapping, unique_vals=False)
            for u, v in G_tr.edges():
                u_ = inv_mapping[u][0]
                v_ = inv_mapping[v][0]
                uncondensed_G_tr.add_edge(u_, v_)

            for key, path in inv_mapping.items():
                if len(path) > 1:
                    directed_cycle = list(ut.itertwo(path, wrap=True))
                    uncondensed_G_tr.add_edges_from(directed_cycle)
            G_tr = uncondensed_G_tr
    return G_tr


def testdata_graph():
    r"""
    Returns:
        tuple: (graph, G)

    CommandLine:
        python -m utool.util_graph --exec-testdata_graph --show

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_graph import *  # NOQA
        >>> import utool as ut
        >>> (graph, G) = testdata_graph()
        >>> import plottool as pt
        >>> ut.ensure_pylab_qt4()
        >>> pt.show_nx(G, layout='pygraphviz')
        >>> ut.show_if_requested()
    """
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
    graph = {'a': ['b'], 'b': ['c'], 'c': ['d'], 'd': ['e'], 'e': ['a'], 'f': ['c']}
    #graph = {'a': ['b'], 'b': ['c'], 'c': ['d'], 'd': ['e'], 'e': ['b']}

    graph = {'a': ['b', 'c', 'd'], 'e': ['d'], 'f': ['d', 'e'], 'b': [], 'c': [], 'd': []}  # double pair in non-scc
    graph = {'a': ['b', 'c', 'd'], 'e': ['d'], 'f': ['d', 'e'], 'b': [], 'c': [], 'd': ['e']}  # double pair in non-scc
    #graph = {'a': ['b', 'c', 'd'], 'e': ['d', 'f'], 'f': ['d', 'e'], 'b': [], 'c': [], 'd': ['e']}  # double pair in non-scc
    #graph = {'a': ['b', 'c', 'd'], 'e': ['d', 'c'], 'f': ['d', 'e'], 'b': ['e'], 'c': ['e'], 'd': ['e']}  # double pair in non-scc
    graph = {'a': ['b', 'c', 'd'], 'e': ['d', 'c'], 'f': ['d', 'e'], 'b': ['e'], 'c': ['e', 'b'], 'd': ['e']}  # double pair in non-scc
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
    return graph, G


def dfs_template(graph, previsit, postvisit):
    seen_ = set()
    meta = {}  # NOQA

    def previsit(parent):
        pass

    def postvisit(parent):
        pass

    def explore(graph, parent, seen_):
        # Mark visited
        seen_.add(parent)
        previsit(parent)
        # Explore children
        children = graph[parent]
        for child in children:
            if child not in seen_:
                explore(graph, child, seen_)
        postvisit(parent)

    # Run Depth First Search
    for node in graph.keys():
        if node not in seen_:
            explore(graph, node, seen_)


def topsort_ordering(G):
    graph_dict = dict(zip(G.nodes(), G.adjacency_list()))

    seen_ = set()
    meta = {
        'clock': 0,
        'pre': {},
        'post': {},
    }

    def previsit(parent):
        meta['pre'][parent] = meta['clock']
        meta['clock'] += 1

    def postvisit(parent):
        meta['post'][parent] = meta['clock']
        meta['clock'] += 1

    def explore(graph_dict, parent, seen_):
        # Mark visited
        seen_.add(parent)
        previsit(parent)
        # Explore children
        children = graph_dict[parent]
        for child in children:
            if child not in seen_:
                explore(graph_dict, child, seen_)
        postvisit(parent)

    # Run Depth First Search
    #nodes = graph_dict.keys()
    #import numpy as np
    #np.random.shuffle(nodes)

    import networkx as nx

    for node in nx.dag.topological_sort(G):
        if node not in seen_:
            explore(graph_dict, node, seen_)
    del meta['clock']
    return meta


def find_odd_cycle():
    r"""
    given any starting point in an scc
    if there is an odd length cycle in the scc
    then the starting node is part of the odd length cycle

    Let s* be part of the odd length cycle
    Start from any point s
    There is also a cycle from (s* to s) due to scc.
    If that cycle is even, then go to s*, then go in the odd length cycle back to s*
    and then go back to s, which makes this path odd.
    If s s* s is odd we are done.

    because it is strongly connected there is a path from s* to s and
    s to s*. If that cycle is odd then done otherwise,

    # Run pairity check on each scc
    # Then check all edges for equal pairity

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
        'pairity': {n: 0 for n in graph}
    }

    def previsit(parent):
        meta['pre'][parent] = meta['clock']
        meta['clock'] += 1

    def postvisit(parent):
        meta['post'][parent] = meta['clock']
        meta['clock'] += 1

    def explore(graph, parent, seen_):
        # Mark visited
        seen_.add(parent)
        previsit(parent)
        # Explore children
        children = graph[parent]
        for child in children:
            if child not in seen_:
                meta['pairity'][child] = 1 - meta['pairity'][parent]
                explore(graph, child, seen_)
        postvisit(parent)

    # Run Depth First Search
    for node in graph.keys():
        if node not in seen_:
            explore(graph, node, seen_)

    # Check edges for neighboring pairities
    import networkx as nx
    scc_list = list(nx.strongly_connected_components(G))

    found = False

    for scc in scc_list:
        SCC_G = nx.subgraph(G, scc)
        for u, v in SCC_G.edges():
            if meta['pairity'][u] == meta['pairity'][v]:
                found = True
                print('FOUND ODD CYCLE')

    if not found:
        print("NO ODD CYCLES")

    # Mark edge types
    edge_types = {(0, 1, 3, 2): 'forward',
                  (1, 0, 2, 3): 'back',
                  (1, 3, 0, 2): 'cross', }

    edge_labels = {}
    type_to_edges = ut.ddict(list)
    pre = meta['pre']
    post = meta['post']

    for u, v in G.edges():
        orders = [pre[u], pre[v], post[u], post[v]]
        sortx = tuple(ut.argsort(orders))
        type_ = edge_types[sortx]
        edge_labels[(u, v)] = type_
        type_to_edges[type_].append((u, v))

    ## Check back edges
    #is_odd_list = []
    #for back_edge in type_to_edges['back']:
    #    u, v = back_edge
    #    pre_v = meta['pre'][v]
    #    post_u = meta['post'][u]
    #    is_even = (post_u - pre_v) % 2 == 0
    #    is_odd = not is_even
    #    is_odd_list.append(is_odd)

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
    pt.show_nx(G, layout='pygraphviz')
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


def nx_source_nodes(graph):
    import networkx as nx
    topsort_iter = nx.dag.topological_sort(graph)
    source_iter = (node for node in topsort_iter if graph.in_degree(node) == 0)
    return source_iter


def nx_sink_nodes(graph):
    import networkx as nx
    topsort_iter = nx.dag.topological_sort(graph)
    sink_iter = (node for node in topsort_iter if graph.out_degree(node) == 0)
    return sink_iter


def dag_longest_path(graph, source, target):
    import networkx as nx
    def longest(gen):
        list_ = []
        for l in gen:
            if len(l) > len(list_):
                list_ = l
        return list_
    # inefficient
    if source == target:
        return [source]
    allpaths = nx.all_simple_paths(graph, source, target)
    return longest(allpaths)


def nx_dag_node_rank(graph, nodes=None):
    """
    Returns rank of nodes that define the "level" each node is on in a
    topological sort. This is the same as the Graphviz dot rank.

    >>> from utool.util_graph import *  # NOQA
    """
    import utool as ut
    source = list(ut.nx_source_nodes(graph))[0]
    longest_paths = dict([(target, dag_longest_path(graph, source, target))
                          for target in graph.nodes()])
    node_to_rank = ut.map_dict_vals(len, longest_paths)
    if nodes is None:
        return node_to_rank
    else:
        ranks = ut.dict_take(node_to_rank, nodes)
        return ranks


def level_order(graph):
    import utool as ut
    node_to_level = ut.nx_dag_node_rank(graph)
    #source = ut.nx_source_nodes(graph)[0]
    #longest_paths = dict([(target, dag_longest_path(graph, source, target))
    #                      for target in graph.nodes()])
    #node_to_level = ut.map_dict_vals(len, longest_paths)
    grouped = ut.group_items(node_to_level.keys(), node_to_level.values())
    levels = ut.take(grouped, range(1, len(grouped) + 1))
    return levels


def merge_level_order(level_orders, topsort):
    """
    Merge orders of individual subtrees into a total ordering for
    computation.

    >>> level_orders = {
    >>>     'multi_chip_multitest': [['dummy_annot'], ['chip'], ['multitest'],
    >>>         ['multitest_score'], ],
    >>>     'multi_fgweight_multitest': [ ['dummy_annot'], ['chip', 'probchip'],
    >>>         ['keypoint'], ['fgweight'], ['multitest'], ['multitest_score'], ],
    >>>     'multi_keypoint_nnindexer': [ ['dummy_annot'], ['chip'], ['keypoint'],
    >>>         ['nnindexer'], ['multitest'], ['multitest_score'], ],
    >>>     'normal': [ ['dummy_annot'], ['chip', 'probchip'], ['keypoint'],
    >>>         ['fgweight'], ['spam'], ['multitest'], ['multitest_score'], ],
    >>>     'nwise_notch_multitest_1': [ ['dummy_annot'], ['notch'], ['multitest'],
    >>>         ['multitest_score'], ],
    >>>     'nwise_notch_multitest_2': [ ['dummy_annot'], ['notch'], ['multitest'],
    >>>         ['multitest_score'], ],
    >>>     'nwise_notch_notchpair_1': [ ['dummy_annot'], ['notch'], ['notchpair'],
    >>>         ['multitest'], ['multitest_score'], ],
    >>>     'nwise_notch_notchpair_2': [ ['dummy_annot'], ['notch'], ['notchpair'],
    >>>         ['multitest'], ['multitest_score'], ],
    >>> }
    >>> topsort = [u'dummy_annot', u'notch', u'probchip', u'chip', u'keypoint',
    >>>            u'fgweight', u'nnindexer', u'spam', u'notchpair', u'multitest',
    >>>            u'multitest_score']
    >>> print(ut.repr3(ut.merge_level_order(level_orders, topsort)))

    EG2:
        level_orders = {u'normal': [[u'dummy_annot'], [u'chip', u'probchip'], [u'keypoint'], [u'fgweight'], [u'spam']]}
        topsort = [u'dummy_annot', u'probchip', u'chip', u'keypoint', u'fgweight', u'spam']
    """

    import utool as ut
    if False:
        compute_order = []
        level_orders = ut.map_dict_vals(ut.total_flatten, level_orders)
        level_sets = ut.map_dict_vals(set, level_orders)
        for tablekey in topsort:
            compute_order.append((tablekey, [groupkey for groupkey, set_ in level_sets.items() if tablekey in set_]))
        return compute_order
    else:
        # Do on common subgraph
        import itertools
        # Pointer to current level.: Start at the end and
        # then work your way up.
        main_ptr = len(topsort) - 1
        stack = []
        #from six.moves import zip_longest
        keys = list(level_orders.keys())
        type_to_ptr = {key: -1 for key in keys}
        print('level_orders = %s' % (ut.repr3(level_orders),))
        for count in itertools.count(0):
            print('----')
            print('count = %r' % (count,))
            ptred_levels = []
            for key in keys:
                levels = level_orders[key]
                ptr = type_to_ptr[key]
                try:
                    level = tuple(levels[ptr])
                except IndexError:
                    level = None
                ptred_levels.append(level)
            print('ptred_levels = %r' % (ptred_levels,))
            print('main_ptr = %r' % (main_ptr,))
            # groupkeys, groupxs = ut.group_indices(ptred_levels)
            # Group keys are tablenames
            # They point to the (type) of the input
            # num_levelkeys = len(ut.total_flatten(ptred_levels))
            groupkeys, groupxs = ut.group_indices(ptred_levels)
            main_idx = None
            while main_idx is None and main_ptr >= 0:
                target = topsort[main_ptr]
                print('main_ptr = %r' % (main_ptr,))
                print('target = %r' % (target,))
                # main_idx = ut.listfind(groupkeys, (target,))
                # if main_idx is None:
                possible_idxs = [idx for idx, keytup in enumerate(groupkeys) if keytup is not None and target in keytup]
                if len(possible_idxs) == 1:
                    main_idx = possible_idxs[0]
                else:
                    main_idx = None
                if main_idx is None:
                    main_ptr -= 1
            if main_idx is None:
                print('break I')
                break
            found_groups = ut.apply_grouping(keys, groupxs)[main_idx]
            print('found_groups = %r' % (found_groups,))
            stack.append((target, found_groups))
            for k in found_groups:
                type_to_ptr[k] -= 1

            if len(found_groups) == len(keys):
                main_ptr -= 1
                if main_ptr < 0:
                    print('break E')
                    break
        print('stack = %s' % (ut.repr3(stack),))
        print('have = %r' % (sorted(ut.take_column(stack, 0)),))
        print('need = %s' % (sorted(ut.total_flatten(level_orders.values())),))
        compute_order = stack[::-1]

    return compute_order


def convert_multigraph_to_graph(G):
    """
    For each duplicate edge make a dummy node.
    TODO: preserve data, keys, and directedness
    """
    import utool as ut
    edge_list = list(G.edges())
    node_list = list(G.nodes())
    dupitem_to_idx = ut.find_duplicate_items(edge_list)
    node_to_freq = ut.ddict(lambda: 0)
    remove_idxs = ut.flatten(dupitem_to_idx.values())
    ut.delete_items_by_index(edge_list, remove_idxs)

    for dup_edge in dupitem_to_idx.keys():
        freq = len(dupitem_to_idx[dup_edge])
        u, v = dup_edge[0:2]
        pair_node = dup_edge
        pair_nodes = [pair_node + tuple([count]) for count in range(freq)]
        for pair_node in pair_nodes:
            node_list.append(pair_node)
            for node in dup_edge:
                node_to_freq[node] += freq
            edge_list.append((u, pair_node))
            edge_list.append((pair_node, v))

    import networkx as nx
    G2 = nx.DiGraph()
    G2.add_edges_from(edge_list)
    G2.add_nodes_from(node_list)
    return G2


def subgraph_from_edges(G, edge_list, ref_back=True):
    """
    Creates a networkx graph that is a subgraph of G
    defined by the list of edges in edge_list.

    Requires G to be a networkx MultiGraph or MultiDiGraph
    edge_list is a list of edges in either (u,v) or (u,v,d) form
    where u and v are nodes comprising an edge,
    and d would be a dictionary of edge attributes

    ref_back determines whether the created subgraph refers to back
    to the original graph and therefore changes to the subgraph's
    attributes also affect the original graph, or if it is to create a
    new copy of the original graph.

    References:
        http://stackoverflow.com/questions/16150557/nx-subgraph-from-edges
    """

    # TODO: support multi-di-graph
    sub_nodes = list({y for x in edge_list for y in x[0:2]})
    #edge_list_no_data = [edge[0:2] for edge in edge_list]
    multi_edge_list = [edge[0:3] for edge in edge_list]

    if ref_back:
        G_sub = G.subgraph(sub_nodes)
        for edge in G_sub.edges(keys=True):
            if edge not in multi_edge_list:
                G_sub.remove_edge(*edge)
    else:
        G_sub = G.subgraph(sub_nodes).copy()
        for edge in G_sub.edges(keys=True):
            if edge not in multi_edge_list:
                G_sub.remove_edge(*edge)

    return G_sub


def nx_all_nodes_between(graph, source, target, data=False):
    import utool as ut
    import networkx as nx
    if source is None:
        # assume there is a single source
        sources = list(ut.nx_source_nodes(graph))
        assert len(sources) == 1, 'specify source if there is not only one'
        source = sources[0]
    if target is None:
        # assume there is a single source
        sinks = list(ut.nx_sink_nodes(graph))
        assert len(sinks) == 1, 'specify sink if there is not only one'
        target = sinks[0]
    all_simple_paths = list(nx.all_simple_paths(graph, source, target))
    nodes = list(set(ut.flatten(all_simple_paths)))
    return nodes


def all_multi_paths(graph, source, target, data=False):
    """
    Returns specific paths along multi-edges from the source to this table.
    Multipaths are identified by edge keys.

    Returns all paths from source to target. This function treats multi-edges
    as distinct and returns the key value in each edge tuple that defines a
    path.

    Example:
        >>> from dtool.depcache_control import *  # NOQA
        >>> from utool.util_graph import *  # NOQA
        >>> from dtool.example_depcache import testdata_depc
        >>> depc = testdata_depc()
        >>> graph = depc.graph
        >>> source = depc.root
        >>> target = 'notchpair'
        >>> path_list1 = ut.all_multi_paths(graph, depc.root, 'notchpair')
        >>> path_list2 = ut.all_multi_paths(graph, depc.root, 'spam')
        >>> result1 = ('path_list1 = %s' % ut.repr3(path_list1, nl=1))
        >>> result2 = ('path_list2 = %s' % ut.repr3(path_list2, nl=2))
        >>> result = '\n'.join([result1, result2])
        >>> print(result)
        path_list1 = [
            [('dummy_annot', 'notch', 0), ('notch', 'notchpair', 0)],
            [('dummy_annot', 'notch', 0), ('notch', 'notchpair', 1)],
        ]
        path_list2 = [
            [
                ('dummy_annot', 'chip', 0),
                ('chip', 'keypoint', 0),
                ('keypoint', 'fgweight', 0),
                ('fgweight', 'spam', 0),
            ],
            [
                ('dummy_annot', 'chip', 0),
                ('chip', 'keypoint', 0),
                ('keypoint', 'spam', 0),
            ],
            [
                ('dummy_annot', 'chip', 0),
                ('chip', 'spam', 0),
            ],
            [
                ('dummy_annot', 'probchip', 0),
                ('probchip', 'fgweight', 0),
                ('fgweight', 'spam', 0),
            ],
        ]
    """
    path_multiedges = list(nx_all_simple_edge_paths(graph, source, target,
                                                    keys=True, data=data))
    return path_multiedges
    #import copy
    #import utool as ut
    #import networkx as nx
    #all_simple_paths = list(nx.all_simple_paths(graph, source, target))
    #paths_from_source2 = ut.unique(ut.lmap(tuple, all_simple_paths))
    #path_edges2 = [tuple(ut.itertwo(path)) for path in paths_from_source2]

    ## expand paths with multi edge indexes
    ## hacky implementation
    #expanded_paths = []
    #for path in path_edges2:
    #    all_paths = [[]]
    #    for u, v in path:
    #        mutli_edge_data = graph.edge[u][v]
    #        items = list(mutli_edge_data.items())
    #        K = len(items)
    #        if len(items) == 1:
    #            path_iter = [all_paths]
    #            pass
    #        elif len(items) > 1:
    #            path_iter = [[copy.copy(p) for p in all_paths]
    #                         for k_ in range(K)]
    #        for (k, edge_data), paths in zip(items, path_iter):
    #            for p in paths:
    #                p.append((u, v, {k: edge_data}))
    #        all_paths = ut.flatten(path_iter)
    #    expanded_paths.extend(all_paths)

    #if data:
    #    path_multiedges = [[(u, v, k, d) for u, v, kd in path for k, d in kd.items()]
    #                       for path in expanded_paths]
    #else:
    #    path_multiedges = [[(u, v, k) for u, v, kd in path for k in kd.keys()]
    #                       for path in expanded_paths]
    ## path_multiedges = [[(u, v, list(kd.keys())[0]) for u, v, kd in path]
    ##                    for path in expanded_paths]
    ## path_multiedges = expanded_paths
    #return path_multiedges


def nx_all_simple_edge_paths(G, source, target, cutoff=None, keys=False,
                             data=False):
    """
    Returns each path from source to target as a list of edges.

    This function is meant to be used with MultiGraphs or MultiDiGraphs.
    When ``keys`` is True each edge in the path is returned with its unique key
    identifier. In this case it is possible to distinguish between different
    paths along different edges between the same two nodes.

    Derived from simple_paths.py in networkx
    """
    if cutoff is None:
        cutoff = len(G) - 1
    if cutoff < 1:
        return
    import six
    visited_nodes = [source]
    visited_edges = []
    edge_stack = [iter(G.edges(source, keys=keys, data=data))]
    while edge_stack:
        children_edges = edge_stack[-1]
        child_edge = six.next(children_edges, None)
        if child_edge is None:
            edge_stack.pop()
            visited_nodes.pop()
            if len(visited_edges) > 0:
                visited_edges.pop()
        elif len(visited_nodes) < cutoff:
            child_node = child_edge[1]
            if child_node == target:
                yield visited_edges + [child_edge]
            elif child_node not in visited_nodes:
                visited_nodes.append(child_node)
                visited_edges.append(child_edge)
                edge_stack.append(iter(G.edges(child_node, keys=keys, data=data)))
        else:
            for edge in [child_edge] + list(children_edges):
                if edge[1] == target:
                    yield visited_edges + [edge]
            edge_stack.pop()
            visited_nodes.pop()
            if len(visited_edges) > 0:
                visited_edges.pop()


def reverse_path_edges(edge_list):
    return [(edge[1], edge[0],) + tuple(edge[2:]) for edge in edge_list][::-1]


def bfs_multi_edges(G, source, reverse=False, keys=True, data=False):
    """Produce edges in a breadth-first-search starting at source.
    -----
    Based on http://www.ics.uci.edu/~eppstein/PADS/BFS.py
    by D. Eppstein, July 2004.
    """
    from collections import deque
    from functools import partial
    if reverse:
        G = G.reverse()
    edges_iter = partial(G.edges_iter, keys=keys, data=data)

    list(G.edges_iter('multitest', keys=True, data=True))

    visited_nodes = set([source])
    # visited_edges = set([])
    queue = deque([(source, edges_iter(source))])
    while queue:
        parent, edges = queue[0]
        try:
            edge = next(edges)
            edge_nodata = edge[0:3]
            # if edge_nodata not in visited_edges:
            yield edge
            # visited_edges.add(edge_nodata)
            child = edge_nodata[1]
            if child not in visited_nodes:
                visited_nodes.add(child)
                queue.append((child, edges_iter(child)))
        except StopIteration:
            queue.popleft()


def bzip(*args):
    """
    broadcasting zip. Only broadcasts on the first dimension

    args = [np.array([1, 2, 3, 4]), [[1, 2, 3]]]
    args = [np.array([1, 2, 3, 4]), [[1, 2, 3]]]

    """
    needs_cast = [isinstance(arg, list) for arg in args]
    arg_containers = [np.empty(len(arg), dtype=object) if flag else arg
                      for arg, flag in zip(args, needs_cast)]
    empty_containers = ut.compress(arg_containers, needs_cast)
    tocast_args = ut.compress(args, needs_cast)
    for container, arg in zip(empty_containers, tocast_args):
        container[:] = arg
    #[a.shape for a in arg_containers]
    bc = np.broadcast(*arg_containers)
    return bc


def nx_delete_node_attr(graph, key, nodes=None):
    removed = 0
    if nodes is None:
        nodes = list(graph.nodes())
    for node in nodes:
        try:
            del graph.node[node][key]
            removed += 1
        except KeyError:
            pass
    return removed


def nx_delete_edge_attr(graph, key, edges=None):
    removed = 0
    if not isinstance(key, list):
        keys = [key]
    else:
        keys = key
    for key in keys:
        if graph.is_multigraph():
            if edges is None:
                edges = list(graph.edges(keys=graph.is_multigraph()))
            for edge in edges:
                u, v, k = edge
                try:
                    del graph[u][v][k][key]
                    removed += 1
                except KeyError:
                    pass
        else:
            if edges is None:
                edges = list(graph.edges())
            for edge in graph.edges():
                u, v = edge
                try:
                    del graph[u][v][key]
                    removed += 1
                except KeyError:
                    pass
    return removed


def nx_delete_None_edge_attr(graph, edges=None):
    removed = 0
    if graph.is_multigraph():
        if edges is None:
            edges = list(graph.edges(keys=graph.is_multigraph()))
        for edge in edges:
            u, v, k = edge
            data = graph[u][v][k]
            for key in data.keys():
                try:
                    if data[key] is None:
                        del data[key]
                        removed += 1
                except KeyError:
                    pass
    else:
        if edges is None:
            edges = list(graph.edges())
        for edge in graph.edges():
            u, v = edge
            data = graph[u][v]
            for key in data.keys():
                try:
                    if data[key] is None:
                        del data[key]
                        removed += 1
                except KeyError:
                    pass
    return removed


def nx_set_default_node_attributes(graph, key, val):
    import networkx as nx
    unset_nodes = [n for n, d in graph.nodes(data=True) if key not in d]
    if isinstance(val, dict):
        values = {n: val[n] for n in unset_nodes if n in val}
    else:
        values = {n: val for n in unset_nodes}
    nx.set_node_attributes(graph, key, values)


def nx_get_default_node_attributes(graph, key, default=None):
    import networkx as nx
    import utool as ut
    node_list = list(graph.nodes())
    partial_attr_dict = nx.get_node_attributes(graph, key)
    attr_list = ut.dict_take(partial_attr_dict, node_list, default)
    attr_dict = dict(zip(node_list, attr_list))
    return attr_dict


def nx_from_matrix(weight_matrix, nodes=None, remove_self=True):
    import networkx as nx
    import utool as ut
    import numpy as np
    if nodes is None:
        nodes = list(range(len(weight_matrix)))
    weight_list = weight_matrix.ravel()
    flat_idxs_ = np.arange(weight_matrix.size)
    multi_idxs_ = np.unravel_index(flat_idxs_, weight_matrix.shape)

    # Remove 0 weight edges
    flags = np.logical_not(np.isclose(weight_list, 0))
    weight_list = ut.compress(weight_list, flags)
    multi_idxs = ut.compress(list(zip(*multi_idxs_)), flags)
    edge_list = ut.lmap(tuple, ut.unflat_take(nodes, multi_idxs))

    if remove_self:
        flags = [e1 != e2 for e1, e2 in edge_list]
        edge_list = ut.compress(edge_list, flags)
        weight_list = ut.compress(weight_list, flags)

    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edge_list)
    label_list = ['%.2f' % w for w in weight_list]
    nx.set_edge_attributes(graph, 'weight', dict(zip(edge_list,
                                                     weight_list)))
    nx.set_edge_attributes(graph, 'label', dict(zip(edge_list,
                                                     label_list)))
    return graph


def color_nodes(graph, labelattr='label'):
    """ Colors edges and nodes by nid """
    import plottool as pt
    import utool as ut
    import networkx as nx
    node_to_lbl = nx.get_node_attributes(graph, labelattr)
    unique_lbls = ut.unique(node_to_lbl.values())
    ncolors = len(unique_lbls)
    if (ncolors) == 1:
        unique_colors = [pt.NEUTRAL_BLUE]
    else:
        unique_colors = pt.distinct_colors(ncolors)
    # Find edges and aids strictly between two nids
    lbl_to_color = dict(zip(unique_lbls, unique_colors))
    node_to_color = {node:  lbl_to_color[lbl] for node, lbl in node_to_lbl.items()}
    nx.set_node_attributes(graph, 'color', node_to_color)
    nx_ensure_agraph_color(graph)


def nx_ensure_agraph_color(graph):
    """ changes colors to hex strings on graph attrs """
    from plottool import color_funcs
    import six
    def _fix_agraph_color(data):
        try:
            orig_color = data.get('color', None)
            color = orig_color
            if color is not None and not isinstance(color, six.string_types):
                #if isinstance(color, np.ndarray):
                #    color = color.tolist()
                color = tuple(color_funcs.ensure_base255(color))
                if len(color) == 3:
                    data['color'] = '#%02x%02x%02x' % color
                else:
                    data['color'] = '#%02x%02x%02x%02x' % color
        except Exception as ex:
            ut.printex(ex, keys=['color', 'orig_color', 'data'])
            raise

    for node, node_data in graph.nodes(data=True):
        _fix_agraph_color(node_data)

    for u, v, edge_data in graph.edges(data=True):
        _fix_agraph_color(edge_data)


def nx_makenode(graph, name, **attrkw):
    if 'size' in attrkw:
        attrkw['width'], attrkw['height'] = attrkw.pop('size')
    graph.add_node(name, **attrkw)
    return name


def nx_edges(graph, keys=False, data=False):
    if graph.is_multigraph():
        edges = graph.edges(keys=keys, data=data)
    else:
        edges = graph.edges(data=data)
        #if keys:
        #    edges = [e[0:2] + (0,) + e[:2] for e in edges]
    return edges


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m utool.util_graph --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
