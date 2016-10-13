"""
Implementation of network display bound to expression heatmap.
"""

from IPython.display import display
import pprint
from jp_gene_viz import dExpression
from jp_gene_viz import dNetwork
from ipywidgets import widgets
from jp_gene_viz import cluster_layout
import traitlets

# Call this once.
from jp_gene_viz.dNetwork import load_javascript_support
from jp_gene_viz.widget_utils import set_visibility


class LinkedExpressionNetwork(traitlets.HasTraits):

    """
    Widget implementing a network display bound to an expression heatmap.
    """

    maximize = traitlets.Bool(True)
    svg_width = traitlets.Int(500)

    def __init__(self, *args, **kwargs):
        super(LinkedExpressionNetwork, self).__init__(*args, **kwargs)
        self.network = dNetwork.NetworkDisplay()
        self.expression = dExpression.ExpressionDisplay()
        self.gene_button = self.make_button(u"\u21d3 Genes", self.gene_click)
        self.condition_button = self.make_button(u"\u21d1 Condition",
                                                 self.condition_click)
        self.cluster_button = self.make_button(u"\u21d1 Cluster",
                                                 self.cluster_click)
        buttons = [self.gene_button, self.condition_button, self.cluster_button]
        horizontal = widgets.HBox(children=buttons)
        self.hideable = widgets.VBox(children=[horizontal, self.expression.assembly])
        #traitlets.directional_link((self, "maximize"), (hideable, "visible"))
        #traitlets.directional_link((self, "maximize"), (self.network, "maximize"))
        self.on_trait_change(self.maximize_changed, "maximize")
        traitlets.directional_link((self, "svg_width"), (self.network, "svg_width"))
        self.assembly = widgets.VBox(children=[self.network.assembly, self.hideable])

    def draw(self):
        self.expression.draw()
        self.network.draw()

    def maximize_changed(self, att_name, old, new):
        set_visibility(self.hideable, new)
        self.network.maximize = new

    def show(self):
        display(self.assembly)
        self.network.draw()

    def make_button(self, description, on_click,
                    disabled=False, width="150px"):
        "Create a button."
        # XXXX refactor to superclass.
        result = widgets.Button(description=description)
        result.on_click(on_click)
        result.disabled = disabled
        result.layout.width = width
        return result

    def gene_click(self, b=None):
        """
        Handle genes button click -- load genes selected in network
        to the heatmap.
        """
        nodes = self.network.get_selection()
        try:
            self.expression.select_rows(nodes)
        except IndexError as e:
            message = str(e)
            self.expression.info_area.value = message
            self.network.info_area.value = message
            return False
        self.expression.info_area.value = "Genes\n" + pprint.pformat(nodes)
        return nodes

    def condition_click(self, b=None):
        """
        Handle condition button click -- load weights in heatmap selected
        condition to the gene nodes in the network.
        """
        col_weights = self.expression.column_weights()
        if not col_weights:
            self.network.info_area.value = "No column weights selected!"
            return
        colors = self.expression.color_interpolator()
        self.network.set_node_weights(col_weights, colors)
        self.network.draw()
        self.network.info_area.value = ("weights\n" +
                                        pprint.pformat(col_weights))
    
    def cluster_click(self, b=None):
        """
        Apply a clustering layout to the network using the expression values.
        """
        # Restrict genes in heatmap to genes in network.
        nodes = self.gene_click()
        if not nodes:
            self.network.info_area.value = "No genes in visible network occur in heatmap."
            return
        (rows, data) = self.expression.get_observations()
        self.network.select_and_draw(rows)
        fit = self.network.fit_heuristic()
        G = self.network.display_graph
        try:
            (layout, rectangles) = cluster_layout.cluster_layout(G, fit, data, rows)
        except AssertionError as e:
            self.network.info_area.value = "Layout failed. Genes in network must match heatmap: " + repr(e)
        else:
            self.network.apply_layout(layout, rectangles)

    def load_network(self, filename):
        """
        Load the network data from a data file.
        """
        N = self.network
        dNetwork.display_network(filename, N, show=False)

    def load_heatmap(self, filename):
        """
        Load the expression data from a data file.
        """
        dexpr = self.expression
        dExpression.display_heat_map(filename, dexpr)
