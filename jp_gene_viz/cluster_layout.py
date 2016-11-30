
from jp_gene_viz import spoke_layout
import numpy as np
from scipy.cluster.hierarchy import linkage, leaves_list, fcluster

def cluster_layout(G, fit=1000, matrix=None, row_names=None, **kw):
    GF = ClusterLayout(G, fit)
    GF.matrix = matrix
    GF.row_names = row_names
    return GF.compute_positions()

class ClusterLayout(spoke_layout.SpokeLayout):

    # leave a margin between clusters to group clustered nodes more closely.
    margin = 0.2

    matrix = None

    row_names = None

    def get_observations(self):
        matrix = self.matrix
        row_names = self.row_names
        G = self.G
        if matrix is None:
            row_names = sorted(G.node_weights.keys())
            name_index = {name: index for (index, name) in enumerate(row_names)}
            nrows = len(row_names)
            # should scale diagonal?
            #matrix = np.identity(nrows)
            matrix = np.zeros((nrows, nrows))
            edge_weights = G.edge_weights
            for edge in edge_weights:
                w = edge_weights[edge]
                (nfrom, nto) = edge
                ifrom = name_index[nfrom]
                ito = name_index[nto]
                matrix[ifrom, ito] += abs(w)
                matrix[ito, ifrom] += abs(w)
                #matrix[ifrom, ifrom] += abs(w)  # ???
        assert matrix is not None
        assert row_names is not None
        assert len(matrix) == len(row_names), "rows and names must match"
        assert set(G.node_weights) == set(row_names), "node names must match row names"
        return (row_names, matrix)

    def get_tree(self):
        (row_names, matrix) = self.get_observations()
        nrows = len(row_names)
        assert nrows > 0, "Cannot cluster 0 rows."
        if nrows == 1:
            # trivial clustering
            [row_name]  = row_names
            return row_name
        Z = linkage(matrix, "ward")
        D = {}
        for i in range(len(matrix)):
            D[i] = row_names[i]
        for (left, right, x, y) in Z:
            D[len(D)] = (D[int(left)], D[int(right)])
        self.root = D[len(D) - 1]
