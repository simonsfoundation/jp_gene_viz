
import spoke_layout
import numpy as np
from numpy.linalg import norm

def tree_layout(G, fit=1000):
    GF = SimpleTreeLayout(G, fit)
    return GF.compute_positions()

class SimpleTreeLayout(spoke_layout.SpokeLayout):

    def get_tree(self):
        paths = self.influence_paths()
        node_order = sorted( (paths[n], n) for n in self.G.node_weights)
        self.root = self.split_subtree(node_order)

    def influence_paths(self, nodes=None, edge_weights=None, level=0, level_limit=5):
        if nodes == None:
            assert edge_weights == None, "provide both or neither arguments, please"
            nodes = set(self.G.node_weights)
            edge_weights = self.positive_symmetric_edges(self.G.edge_weights)
        if not edge_weights or level >= level_limit:
            return {n: () for n in nodes}
        (greatest_weight, strongest_factor, strongest_factor_inv, strongest_count, connected, isolated) = \
            self.strength_stats(nodes, edge_weights)
        # add self-loop at "maximal" factor loops of length 2
        #for n in strongest_factor.values():
        #    f = strongest_factor.get(n)
        #    if strongest_factor.get(f) == n:
        #        strongest_factor[f] = f
        # truncate factor paths to max length 1
        for n in strongest_factor.keys():
            f = strongest_factor[n]
            strongest_factor[f] = f
        influence_nodes = set(strongest_factor.values())
        influence_weights = self.combine_edge_weights(edge_weights, strongest_factor)
        tails = self.influence_paths(influence_nodes, influence_weights, level=level+1)
        result = {}
        for n in nodes:
            if n in strongest_factor:
                f = strongest_factor[n]
                result[n] = (f,) + tails[f]
            else:
                result[n] = ()
        return result

    def split_subtree(self, node_order):
        nnodes = len(node_order)
        assert nnodes > 0
        if nnodes == 1:
            (influence, node) = list(node_order)[0]
            return node
        middle = int(nnodes / 2)
        split_index = None
        deepest_difference = 0
        for offset in range(int(nnodes/4)):
            for test_index in (middle + offset, middle - offset):
                influence_before = node_order[test_index - 1][0]
                influence_after = node_order[test_index][0]
                difference = difference_depth(influence_after, influence_before)
                if difference > deepest_difference:
                    split_index = test_index
                    deepest_difference = difference
        if split_index is None:
            split_index = middle
        left = node_order[:split_index]
        right = node_order[split_index:]
        return (self.split_subtree(left), self.split_subtree(right))

def difference_depth(tuple1, tuple2):
    if tuple1 == tuple2:
        return 0
    index = 0
    for (a, b) in zip(tuple1, tuple2):
        if a != b:
            return index + 1
        index += 1
    return index + 1
