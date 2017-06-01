from jp_gene_viz import spoke_layout
from jp_gene_viz.dGraph import primary_influence, skeleton, pos

import igraph

import json

def asIGraph(G, test=True):
    result = igraph.Graph()
    nodes = G.node_weights.keys()
    result.add_vertices(nodes)
    node_to_index = {n.attributes()["name"]: index
                     for (index, n) in enumerate(result.vs)}
    #print ("node_to_index", node_to_index)
    edges = G.edge_weights.keys()
    indexed_edges = [(node_to_index[f], node_to_index[t])
                     for (f,t)  in edges]
    result.add_edges(indexed_edges)
    return result

def iGraphLayout(G, name, fit=1000):
    iG = asIGraph(G)
    index_to_name = {i: n.attributes()["name"]
                     for (i, n) in enumerate(iG.vs)}
    L = iG.layout(name)
    L.fit_into([0, 0, fit, fit])
    D = {index_to_name[i]: pos(xy[0], xy[1])
         for (i,xy) in enumerate(L)}
    return D

def group_graph(G):
    Gk = skeleton(G)
    Gp = primary_influence(G, connect=True)
    Gp.edge_weights.update(Gk.edge_weights)
    return Gp

def group_layout(G, name="fr", fit=1000, **kw):
    Gp = group_graph(G)
    return (iGraphLayout(Gp, name, fit), {})

def group_layout0(G, fit=1000):
    return spoke_layout.spoke_layout(G, fit)

def dump(layout, filename):
    jlayout = layoutConverter.to_json_value(layout)
    with open(filename, "w") as f:
        json.dump(jlayout, f)

def load(filename):
    with open(filename) as f:
        jlayout = json.load(f)
    # Lower case gene names and array positions.
    layout = layoutConverter.from_json_value(jlayout)
    return layout

class layoutConverter(object):

    @staticmethod
    def to_json_value(layout):
        return {k: list(layout[k]) for k in layout}

    @staticmethod
    def from_json_value(jlayout):
        return {k: pos(*jlayout[k]) for k in jlayout}
