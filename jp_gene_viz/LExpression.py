from IPython.display import display
import pprint
from jp_gene_viz import dExpression
from jp_gene_viz import dNetwork
from ipywidgets import widgets
import traitlets

# Call this once.
from dNetwork import load_javascript_support


class LinkedExpressionNetwork(traitlets.HasTraits):

    def __init__(self, *args, **kwargs):
        super(LinkedExpressionNetwork, self).__init__(*args, **kwargs)
        self.network = dNetwork.NetworkDisplay()
        self.expression = dExpression.ExpressionDisplay()
        self.gene_button = self.make_button(u"\u21d3 Genes", self.gene_click)
        self.condition_button = self.make_button(u"\u21d1 Condition", self.condition_click)
        buttons = [self.gene_button, self.condition_button]
        horizontal = widgets.HBox(children=buttons)
        self.assembly = widgets.VBox(children=[self.network.assembly, 
                                               horizontal, 
                                               self.expression.assembly])
    def show(self):
        display(self.assembly)

    def make_button(self, description, on_click, disabled=False, width="250px"):
        "Create a button."
        result = widgets.Button(description=description)
        result.on_click(on_click)
        result.disabled = disabled
        result.width = width
        return result

    def gene_click(self, b):
        nodes = self.network.get_selection()
        #print "nodes", nodes
        self.expression.select_rows(nodes)
        self.expression.info_area.value = "Genes\n" + pprint.pformat(nodes)

    def condition_click(self, b):
        col_weights = self.expression.column_weights()
        if not col_weights:
            self.network.info_area.value = "No column weights selected!"
            return
        self.network.set_node_weights(col_weights)
        self.network.draw()
        self.network.info_area.value = "weights\n" + pprint.pformat(col_weights)

    def load_network(self, filename):
        N = self.network
        dNetwork.display_network(filename, N, show=False)

    def load_heatmap(self, filename):
        dexpr = self.expression
        dExpression.display_heat_map(filename, dexpr)
