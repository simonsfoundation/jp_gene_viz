"""
Grid forest layout.
"""

import numpy as np
from numpy.linalg import norm
from random import random

def forest_layout(G, fit=1000, klass=None, **kw):
    if klass is None:
        klass = GridForestLayout
    GF = klass(G, fit)
    return GF.compute_positions()

def split_position(position, ratio, margin=0):
    assert margin < 0.5
    (x, y, dx, dy) = position
    x1 = x2 = x
    y1 = y2 = y
    dx1 = dx2 = dx
    dy1 = dy2 = dy
    useable = 1.0
    if margin > 0:
        useable = 1.0 - margin
    if dx > dy:
        (x1, x2, dx1, dx2) = split_stats(x, dx, ratio)
        dx1 = dx1 * useable
        dx2 = dx2 * useable
    else:
        (y1, y2, dy1, dy2) = split_stats(y, dy, ratio)
        dy1 = dy1 * useable
        dy2 = dy2 * useable
    #if margin > 0:
    #    useable = 1.0 - margin
    #    dx1 = dx1 * useable
    #    dy1 = dy1 * useable
    #    dx2 = dx2 * useable
    #    dy2 = dy2 * useable
    return (np.array([x1, y1, dx1, dy1]), np.array([x2, y2, dx2, dy2]))

def split_stats(x, dx, ratio):
    # xxxx could be simplified?
    ox = x - dx
    s = 2 * dx
    rx1 = s * ratio
    dx1 = 0.5 * rx1
    rx2 = s - rx1
    dx2 = 0.5 * rx2
    cx1 = ox + dx1
    cx2 = ox + rx1 + dx2
    return (cx1, cx2, dx1, dx2)

class GridForestLayout(object):
    """
    Heuristic to combine nodes into binary tree based on shared greatest influence.
    Layout the binary tree using penalty heuristic.
    """
    def __init__(self, G, side_length=500.0):
        self.G = G
        self.side_length = side_length
        self.parents = {}
        self.members = {node: frozenset([node]) for node in G.node_weights}
        self.root = None
        self.positions = None
        self.levels = []

    # Margin for grouping nodes in subtree
    margin = 0.0   # default: no margin

    def fill_in_members(self, node=None, members=None, leaves=None):
        if leaves is None:
            leaves = set(self.G.node_weights)
        if node is None:
            node = self.root
        assert node is not None
        if members is None:
            members = self.members
        if node in leaves:
            members[node] = frozenset([node])
        else:
            (left, right) = node
            members[node] = (
                self.fill_in_members(left, members, leaves) | 
                self.fill_in_members(right, members, leaves))
        return members[node]
    
    def compute_positions(self, jitter=True, jitter_factor=0.5, expand=0.99):
        G = self.G
        # No positions for no nodes.
        if not self.G.node_weights:
            return {}
        self.get_tree()
        self.members = {}
        self.fill_in_members()
        positions = self.assign_positions(jitter, jitter_factor)
        #result = {node: positions[node][:2] for node in G.node_weights}
        leaf_positions = {}
        group_rectangles = {}
        members = self.members
        for node in positions:
            (x, y, dx, dy) = positions[node]
            if node in G.node_weights:
                if jitter:
                    x += random() * jitter_factor * dx
                    y += random() * jitter_factor * dy
                leaf_positions[node] = np.array([x, y])
            else:
                ddx = dx * expand
                ddy = dy * expand
                rectangle = np.array([x-ddx, y-ddy, ddx*2, ddy*2])
                #group_rectangles.append(rectangle)
                nodes = frozenset(members[node])
                group_rectangles[nodes] = rectangle
        return (leaf_positions, group_rectangles)

    def positive_symmetric_edges(self, directed_edges):
        Gew = directed_edges
        edge_weights = {}
        for edge in Gew:
            back_edge = (edge[1], edge[0])
            edge_weights[edge] = edge_weights[back_edge] = abs(Gew[edge]) + abs(Gew.get(back_edge, 0))
        return edge_weights

    def get_tree(self):
        G = self.G
        nodes = set(G.node_weights)
        Gew = G.edge_weights
        # enforce positive and symmetric edge weights
        edge_weights = self.positive_symmetric_edges(Gew)
        (self.root, self.levels) = self.get_subtree(nodes, edge_weights)

    def get_subtree(self, nodes, edge_weights):
        assert len(nodes) > 0
        levels = [(nodes, edge_weights)]  # leaf level
        while len(nodes) > 1:
            this_level = self.combine(nodes, edge_weights)
            (combined_nodes, edge_weights) = this_level
            assert len(combined_nodes) < len(nodes), repr(nodes) + " no progress."
            nodes = combined_nodes
            levels.append(this_level)
        assert len(nodes) == 1
        [root] = list(nodes)
        return (root, levels)

    def distance(self, position1, position2):
        p1 = position1[:2]
        p2 = position2[:2]
        return (norm(p1-p2))

    def distance0(self, position1, position2):
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

    def assign_positions(self, jitter=True, jitter_factor=0.7):
        margin = self.margin
        self.compute_geneology()
        root = self.root
        assert root is not None
        parents = self.parents
        non_leaves = set(parents.values())
        half_side = self.side_length/2.0
        root_position = np.array([half_side, half_side, half_side, half_side])
        positions = {root: root_position}
        members = self.members
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
                    len1 = len(members[child1])
                    len2 = len(members[child2])
                    if jitter:
                        len1 += random() * jitter_factor
                        len2 += random() * jitter_factor
                    ratio12 = len1/float(len1 + len2)
                    pos12 = split_position(node_position, ratio12, margin)
                    pos21 = split_position(node_position, 1.0 - ratio12, margin)
                    penalty12 = (self.penalty(child1, pos12[0], child_adjacent, positions, child_edge_weights) +
                                 self.penalty(child2, pos12[1], child_adjacent, positions, child_edge_weights))
                    penalty21 = (self.penalty(child1, pos21[1], child_adjacent, positions, child_edge_weights) +
                                 self.penalty(child2, pos21[0], child_adjacent, positions, child_edge_weights))
                    if penalty12 < penalty21:
                        positions[child1] = pos12[0]
                        positions[child2] = pos12[1]
                    else:
                        positions[child1] = pos21[1]
                        positions[child2] = pos21[0]
        self.positions = positions
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

    def strength_stats(self, nodes, edge_weights):
        greatest_weight = {node: 0 for node in nodes}
        strongest_factor = {}
        strongest_count = {node: 0 for node in nodes}
        strongest_factor_inv = {node: set() for node in nodes}
        connected = set()
        for edge in edge_weights:
            weight = abs(edge_weights[edge])
            (nfrom, nto) = edge
            if weight > greatest_weight[nto]:
                greatest_weight[nto] = weight
                strongest_factor[nto] = nfrom
                strongest_count[nfrom] += 1
                strongest_factor_inv[nfrom].add(nto)
                connected.add(nfrom)
                connected.add(nto)
        isolated = set(nodes) - connected
        return (greatest_weight, strongest_factor, strongest_factor_inv, strongest_count, connected, isolated)

    def pair_up_list(self, spoke_order, combined_nodes, not_combined, level_mapping, members):
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

    def combine(self, nodes, edge_weights):
        "Pair up related nodes."
        members = self.members
        not_combined = set(nodes)
        combined_nodes = set()
        level_mapping = {}
        (greatest_weight, strongest_factor, strongest_factor_inv, strongest_count, connected, isolated) = \
            self.strength_stats(nodes, edge_weights)
        node_strength = sorted((strongest_count[n], n) for n in nodes if n not in isolated)
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
                self.pair_up_list(spoke_order, combined_nodes, not_combined, level_mapping, members)
        # pair up any uncombined nodes
        not_combined_list = reversed(sorted((len(members[n]), n) for n in not_combined))
        self.pair_up_list(not_combined_list, combined_nodes, not_combined, level_mapping, members)
        combined_edge_weights = self.combine_edge_weights(edge_weights, level_mapping)
        #self.parent.update(level_mapping)
        return (combined_nodes, combined_edge_weights)

    def combine_edge_weights(self, edge_weights, level_mapping):
        # compute combined edge weights
        combined_edge_weights = {}
        for edge in edge_weights:
            (nfrom, nto) = edge
            mfrom = level_mapping[nfrom]
            mto = level_mapping[nto]
            if mfrom != mto:
                mapped_edge = (mfrom, mto)
                w = edge_weights[edge]
                combined_edge_weights[mapped_edge] = combined_edge_weights.get(mapped_edge, 0) + w
        return combined_edge_weights
