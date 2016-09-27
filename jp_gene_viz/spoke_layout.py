
import grid_forest
import numpy as np

def spoke_layout(G, fit=1000, **kw):
    return grid_forest.forest_layout(G, fit, klass=SpokeLayout)

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
