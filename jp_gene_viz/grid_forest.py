"""
Grid forest layout.
"""

import numpy as np
from numpy.linalg import norm

def forest_layout(G, side_length=1000):
    GF = GridForestLayout(G, side_length)
    return GF.compute_positions()

def split_position(position):
    (x, y, dx, dy) = position
    cx = cy = 0
    ddx = dx
    ddy = dy
    if dx > dy:
        cx = ddx = dx * 0.5
    else:
        cy = ddy = dy * 0.5
    return (np.array([x+cx, y+cy, ddx, ddy]), np.array([x-cx, y-cy, ddx, ddy]))

class GridForestLayout(object):

    def __init__(self, G, side_length=500.0):
        self.G = G
        self.side_length = side_length
        self.parents = {}
        self.members = {node: frozenset([node]) for node in G.node_weights}
        self.root = None
        self.levels = []

    def compute_positions(self):
        G = self.G
        self.get_tree()
        positions = self.assign_positions()
        result = {node: positions[node][:2] for node in G.node_weights}
        return result

    def get_tree(self):
        G = self.G
        nodes = set(G.node_weights)
        Gew = G.edge_weights
        # enforce positive and symmetric edge weights
        edge_weights = {}
        for edge in Gew:
            back_edge = (edge[1], edge[0])
            edge_weights[edge] = edge_weights[back_edge] = abs(Gew[edge] + Gew.get(back_edge, 0))
        #edge_weights = {edge: abs(Gew[edge]) for edge in Gew}
        assert len(nodes) > 0
        self.levels.append((nodes, edge_weights))  # leaf level
        while len(nodes) > 1:
            #print "combining", nodes
            this_level = self.combine(nodes, edge_weights)
            (nodes, edge_weights) = this_level
            self.levels.append(this_level)
        assert len(nodes) == 1
        [self.root] = list(nodes)

    def distance0(self, position1, position2):
        p1 = position1[:2]
        p2 = position2[:2]
        return norm(p1-p2) 

    def distance(self, position1, position2):
        p1 = position1[:2]
        p2 = position2[:2]
        return np.sum(np.abs(p1 - p2))

    def current_position(self, node, positions):
        "Either position assigned to node or position assigned to node parent"
        result = positions.get(node)
        if result is None:
            node_parent = self.parents[node]
            result = positions[node_parent]
        return result

    def assign_positions(self):
        root = self.root
        assert root is not None
        parents = self.parents
        non_leaves = set(parents.values())
        half_side = self.side_length/2.0
        root_position = np.array([half_side, half_side, half_side, half_side])
        positions = {root: root_position}
        # compute child nodes for each level
        root_to_leaf = list(reversed(self.levels))
        for (non_leaf_level_number, level) in enumerate(root_to_leaf[:-1]):
            (nodes, edge_weights) = level
            (child_nodes, child_edge_weights) = root_to_leaf[non_leaf_level_number + 1]
            child_adjacent = self.adjacency(child_nodes, child_edge_weights)
            for node in nodes:
                node_position = positions[node]
                if node in non_leaves:
                    (child1, child2) = node
                    assert child1 not in positions
                    assert child2 not in positions
                    if child1 not in child_adjacent or child2 not in child_adjacent:
                        # node created at later level
                        continue
                    (position1, position2) = split_position(node_position)
                    penalty12 = (self.penalty(child1, position1, child_adjacent, positions, child_edge_weights) +
                                 self.penalty(child2, position2, child_adjacent, positions, child_edge_weights))
                    penalty21 = (self.penalty(child1, position2, child_adjacent, positions, child_edge_weights) +
                                 self.penalty(child2, position1, child_adjacent, positions, child_edge_weights))
                    if penalty12 < penalty21:
                        positions[child1] = position1
                        positions[child2] = position2
                    else:
                        positions[child1] = position2
                        positions[child2] = position1
        return positions

    def penalty(self, node, position, adjacency, positions, edge_weights):
        result = 0
        for node2 in adjacency[node]:
            position2 = self.current_position(node2, positions)
            dist = self.distance(position, position2)
            weight = edge_weights[(node, node2)]
            result += weight * dist
        return result

    def adjacency(self, nodes, edge_weights):
        result = {node: set() for node in nodes}
        for (nfrom, nto) in edge_weights:
            result[nfrom].add(nto)
            result[nto].add(nfrom)
        return result

    def combine(self, nodes, edge_weights):
        "Pair up related nodes."
        not_combined = set(nodes)
        combined_nodes = set()
        level_mapping = {}
        combined_edge_weights = {}
        greatest_weight = {node: 0 for node in nodes}
        strongest_factor = {}
        strongest_count = {node: 0 for node in nodes}
        strongest_factor_inv = {node: set() for node in nodes}
        members = self.members
        connected = set()
        for edge in edge_weights:
            weight = edge_weights[edge]
            (nfrom, nto) = edge
            if weight > greatest_weight[nto]:
                greatest_weight[nto] = weight
                strongest_factor[nto] = nfrom
                strongest_count[nfrom] += 1
                strongest_factor_inv[nfrom].add(nto)
                connected.add(nfrom)
                connected.add(nto)
        isolated = set(nodes) - connected
        node_strength = sorted((strongest_count[n], n) for n in nodes if n not in isolated)
        def pair_up_list(spoke_order):
            spoke_order = list(spoke_order)
            #print "order before", spoke_order, not_combined
            while len(spoke_order) > 1:
                (count1, node1) = spoke_order.pop()
                (count2, node2) = spoke_order.pop()
                pair = (node1, node2)
                combined_nodes.add(pair)
                not_combined.remove(node1)
                not_combined.remove(node2)
                for n in (node1, node2):
                    level_mapping[n] = pair
                    self.parents[n] = pair
                members[pair] = members[node1] | members[node2]
            #print "order after", spoke_order, not_combined
            # add any trailing node as isolated
            if spoke_order:
                [(rcount, remaining_node)] = spoke_order
                not_combined.remove(remaining_node)
                level_mapping[remaining_node] = remaining_node
                combined_nodes.add(remaining_node)
        while node_strength:
            (scount, central_node) = node_strength.pop()
            if scount < 1:
                # stop for not strongest factor
                break
            spoke_nodes = {x for x in strongest_factor_inv[central_node] if x in not_combined}
            spoke_order = sorted((strongest_count[sn], sn) for sn in spoke_nodes)
            # also combine the central node_strength
            if central_node in not_combined:
                #spoke_order = [(0, central_node)] + spoke_order
                spoke_order.insert(len(spoke_order)/2, (0, central_node))
            # also combine any remaining isolated nodes
            if isolated:
                spoke_order = spoke_order + [(0, n) for n in isolated]
                isolated = set()
            if len(spoke_order) > 1:
                # combine node pairs
                spoke_order = reversed(spoke_order)
                pair_up_list(spoke_order)
        # pair up any uncombined nodes
        not_combined_list = reversed(sorted((len(members[n]), n) for n in not_combined))
        pair_up_list(not_combined_list)
        # compute combined edge weights
        for edge in edge_weights:
            (nfrom, nto) = edge
            mfrom = level_mapping[nfrom]
            mto = level_mapping[nto]
            if mfrom != mto:
                mapped_edge = (mfrom, mto)
                w = edge_weights[edge]
                combined_edge_weights[mapped_edge] = combined_edge_weights.get(mapped_edge, 0) + w
        #self.parent.update(level_mapping)
        return (combined_nodes, combined_edge_weights)

def layout(G, side_length=500):
    # Build binary tree with nodes at leaves.
    node_weights = {}
    edge_weights = {}
    #children = {}
    parent = {}
    members = {}
    neighbors = {}
    for node in G.node_weights:
        node_weights[node] = 0  # ignore input weights.
        members[node] = frozenset([node])
        neighbors[node] = set()
    ew = G.edge_weights
    for e in G.edge_weights:
        (n1, n2) = e
        w = abs(ew[e])
        node_weights[n1] += w
        node_weights[n2] += w
        edge_weights[e] = w
        edge_weights[(n2, n1)] = w
        neighbors(n1).add(n2)
        neighbors(n2).add(n1)
    # repeat until all nodes are merged into a single tree
    while len(node_weights) > 1:
        next_node_weights = {}
        next_edge_weights = {}
        level_map = {}
        unpaired = set(node_weights)
        ascending_weights = sorted((node_weights(n), n) for n in node_weights)
        descending_weights = list(reversed(ascending_weights))
        while len(unpaired) > 1:
            # find lowest weight unpaired node.
            (w, n) = descending_weights.pop()
            while w not in unpaired:
                (w, n) = descending_weights.pop()
            # find highest weight incident edge from node
            weighted_edges = []
            for neighbor in neighbors[n]:
                if neighbor not in unpaired:
                    edge = (n, neighbor)
                    weighted_edges.append((edge_weights[edge], edge))
            if weighted_edges:
                (edge_weight, edge) = max(weighted_edges)
                n2 = edge[1]
                w2 = node_weights[n2]
            else:
                # chose next least weighted node as default
                (w2, n2) = descending_weights.pop()
                while w2 not in unpaired:
                    (w2, n2) = descending_weights.pop()
            # pair the chosen nodes
            pair = (n, n2)
            next_node_weights[pair] = w + w2
            for node in pair:
                level_map[node] = pair
                unpaired.remove(node)
        if len(unpaired) == 1:
            # handle unpaired remaining node
            (w, n) = descending_weights[0]
            while w not in unpaired:
                (w, n) = descending_weights.pop()
            next_node_weights[n] = w
            level_map[n] = n
        else:
            assert len(unpaired) == 0
        # compute combined edge_weights for the new level