
import simple_tree
import grid_forest
import math


def category_layout(G, fit=1000, node_categories=None, **kw):
    if node_categories is None:
        node_categories = default_categories(G)
    #anonymous_categories = numeric_categories(node_categories, G)
    anonymous_categories = fill_in_categories(node_categories, G)
    GF = CategoryForestLayout(G, fit)
    GF.node_categories = anonymous_categories
    (positions, rectangles) = GF.compute_positions()
    category_to_rectangle = {}
    for (count, nodes) in sorted((len(nodes), nodes) for nodes in rectangles):
        if count < 2:
            continue # Don't group only one node into a rectangle.
        categories = set(anonymous_categories[node] for node in nodes)
        if len(categories) == 1:
            [category] = list(categories)
            category_to_rectangle[category] = (nodes, rectangles[nodes])
    #maximal_rectangles = {nodes: rectangle for (nodes, rectangle) in category_to_rectangle.values()}
    maximal_rectangles = {label: rectangle for (label, (nodes, rectangle)) in category_to_rectangle.items()}
    return (positions, maximal_rectangles)

def fill_in_categories(node_categories, G):
    result = {}
    for (count, node) in enumerate(G.node_weights):
        if node in node_categories:
            result[node] = node_categories[node]
        else:
            result[node] = str(node) + "_" + str(count)
    return result

def numeric_categories(node_categories, G):
    "fully define categories using fresh numbers as anonymous identifiers for convenience"
    result = {}
    category_number = {}
    for (count, node) in enumerate(G.node_weights):
        if node in node_categories:
            category = node_categories[node]
            numeric_category = category_number.setdefault(category, count)
        else:
            numeric_category = count
        result[node] = numeric_category
    return result


def default_categories(G, weights=None):
    result = {}
    counts = {}
    if weights is None:
        weights = G.edge_weights
    for edge in weights:
        w = weights[edge]
        for node in edge:
            counts[node] = counts.get(node, 0) + int(math.copysign(1, w))
    log2 = math.log(2)
    for node in counts:
        c = counts[node]
        if abs(c) > 1:
            result[node] = int(math.log(abs(c) + 1)/log2 * math.copysign(1, c))
    return result


class CategoryTreeLayout(simple_tree.SimpleTreeLayout):

    node_categories = None
    heuristic = False   # scan whole list for differences in split_subtree

    def influence_paths(self, nodes=None, edge_weights=None, level=0, level_limit=5):
        paths = super(CategoryLayout, self).influence_paths(nodes, edge_weights, level, level_limit)
        categories = self.node_categories
        result = {node: (categories.get(node),) + tuple(paths[node]) for node in paths}
        return result

    def get_tree(self, *args, **kwargs):
        if self.node_categories is None:
            self.node_categories = default_categories(self.G)
        return super(CategoryLayout, self).get_tree(*args, **kwargs)


class CategoryForestLayout(grid_forest.GridForestLayout):

    node_categories = None

    def get_tree(self):
        G = self.G
        node_categories = self.node_categories
        categories = set(node_categories.values())
        assert categories is not None, "categories must be specified"
        nodes = G.node_weights
        edge_weights = G.edge_weights
        category_sets = {category: set() for category in categories}
        for node in node_categories:
            category = node_categories[node]
            category_sets[category].add(node)
        category_nodes = {}
        group_mapping = {}
        for category in categories:
            members = category_sets[category]
            member_edge_weights = {e: edge_weights[e]
                for e in edge_weights if e[0] in members and e[1] in members}
            (subtree, levels) = self.get_subtree(members, member_edge_weights)
            group_mapping.update({member: subtree for member in members})
            category_nodes[category] = subtree
        group_mapping.update({node: node for node in nodes if node not in group_mapping})
        group_weights = self.combine_edge_weights(edge_weights, group_mapping)
        subtrees = set(category_nodes.values())
        (self.root, dummy) = self.get_subtree(subtrees, group_weights)
