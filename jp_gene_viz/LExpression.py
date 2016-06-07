"""
Implementation of network display bound to expression heatmap.
"""

from IPython.display import display
import pprint
from jp_gene_viz import dExpression
from jp_gene_viz import dNetwork
from ipywidgets import widgets
import traitlets

# Call this once.
from dNetwork import load_javascript_support


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
        buttons = [self.gene_button, self.condition_button]
        horizontal = widgets.HBox(children=buttons)
        hideable = widgets.VBox(children=[horizontal, self.expression.assembly])
        traitlets.directional_link((self, "maximize"), (hideable, "visible"))
        traitlets.directional_link((self, "maximize"), (self.network, "maximize"))
        traitlets.directional_link((self, "svg_width"), (self.network, "svg_width"))
        self.assembly = widgets.VBox(children=[self.network.assembly, hideable])

    def show(self):
        display(self.assembly)

    def make_button(self, description, on_click,
                    disabled=False, width="250px"):
        "Create a button."
        # XXXX refactor to superclass.
        result = widgets.Button(description=description)
        result.on_click(on_click)
        result.disabled = disabled
        result.layout.width = width
        return result

    def gene_click(self, b):
        """
        Handle genes button click -- load genes selected in network
        to the heatmap.
        """
        nodes = self.network.get_selection()
        self.expression.select_rows(nodes)
        self.expression.info_area.value = "Genes\n" + pprint.pformat(nodes)

    def condition_click(self, b):
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
