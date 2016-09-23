
import grid_forest
import numpy as np

def spoke_layout(G, fit=1000):
    GF = SpokeLayout(G, fit)
    return GF.compute_positions()

class SpokeLayout(grid_forest.GridForestLayout):

    def combine(self, nodes, edge_weights):
        edgenodes = set(a for (a, b) in edge_weights) | set(b for (a, b) in edge_weights)
        assert edgenodes.issubset(set(nodes))
        combined_nodes = set()
        level_mapping = {}
        (greatest_weight, strongest_factor, strongest_factor_inv, strongest_count, connected, isolated) = \
            self.strength_stats(nodes, edge_weights)
        wheels = {center: set([center]) for center in strongest_count}
        assigned = set()
        #print "nodes", nodes, "factors", strongest_factor
        nnodes = len(nodes)
        for n in nodes:
            if n not in assigned:
                center = strongest_factor.get(n)
                if center is not None:
                    wheels[center].add(n)
                    assigned.add(n)
                    assigned.add(center)
                    if (n != center) and (n in wheels) and (n in wheels[n]):
                        wheels[n].remove(n)
        #print "wheels", wheels
        for center in wheels:
            wheel = wheels[center]
            nwheel = len(wheel)
            if nwheel < 2:
                continue
            if nwheel >= nnodes:
                wheel_root = self.default_subtree(wheel)
            else:
                wheel_root = self.subtree_root(wheel, edge_weights)
            for n in wheel:
                level_mapping[n] = wheel_root
            combined_nodes.add(wheel_root)
        isolated = set(nodes)-set(level_mapping)
        if isolated:
            isolated_root = self.default_subtree(isolated)
            for n in isolated:
                level_mapping[n] = isolated_root
            combined_nodes.add(isolated_root)
        #print "edge_weights", edge_weights
        #print "level_mapping", level_mapping
        combined_edge_weights = self.combine_edge_weights(edge_weights, level_mapping)
        return (combined_nodes, combined_edge_weights)

    def compute_geneology(self):
        """
        set up self.parents and self.levels to properly reflect self.root
        """
        G = self.G
        node_weights = G.node_weights
        edge_weights = self.positive_symmetric_edges(G.edge_weights)
        parents = self.parents = {}
        #members = self.members = {}
        level_nodesets = []
        this_level = set([self.root])
        all_leaves = False
        leaves = set(node_weights)
        # compute parent relationship and nodeset at each level, top down
        while not all_leaves:
            all_leaves = True
            level_nodesets.append(this_level)
            next_level = set()
            for node in this_level:
                if node in leaves:
                    next_level.add(node)
                else:
                    all_leaves = False
                    (n1, n2) = node
                    #members[node] = set(node)
                    for n in (n1, n2):
                        next_level.add(n)
                        parents[n] = node
            this_level = next_level
        #print "level_nodesets", level_nodesets
        assert next_level == leaves
        # compute edge weights for each level bottom up
        last_edge_weights = edge_weights.copy()
        last_node_set = set(leaves)
        levels = [(last_node_set, last_edge_weights)]
        for next_node_set in reversed(level_nodesets[:-1]):
            level_mapping = {}
            for n in next_node_set:
                if n in last_node_set:
                    level_mapping[n] = n
                else:
                    for child in n:
                        level_mapping[child] = n
            next_edge_weights = self.combine_edge_weights(last_edge_weights, level_mapping)
            levels.append((next_node_set, next_edge_weights))
            last_node_set = next_node_set
            last_edge_weights = next_edge_weights
        self.levels = levels

    def subtree_root(self, node_set, edge_weights):
        # recursively layout sub graph
        edge_weights_subset = {}
        for edge in edge_weights:
            (nfrom, nto) = edge
            if nfrom in node_set and nto in node_set:
                edge_weights_subset[edge] = edge_weights[edge]
        (root, levels) = self.get_subtree(node_set, edge_weights_subset)
        return root

    def default_subtree(self, nodes):
        L = list(nodes)
        nnodes = len(L)
        assert nnodes > 0
        if nnodes == 1:
            return L[0]
        split = int(nnodes/2)
        return (self.default_subtree(L[:split]), self.default_subtree(L[split:]))
