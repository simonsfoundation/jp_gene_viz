
"""
Two networks and heatmaps with coordinated node selection and layouts.

XXXX This is copy-pasted and edited from paired_networks.py.
At some point common functionality should be refactored, maybe.
Or perhaps the whole infrastructure should be generalized.
"""

from IPython.display import display
from jp_gene_viz import LExpression
from ipywidgets import widgets
import traitlets

# Call this once.
from dNetwork import load_javascript_support


class PairedLinks(traitlets.HasTraits):

    """
    Coordinated networks.
    """

    def __init__(self, *args, **kwargs):
        super(PairedLinks, self).__init__(*args, **kwargs)
        self.left_expression = LExpression.LinkedExpressionNetwork()
        self.right_expression = LExpression.LinkedExpressionNetwork()
        lb = self.left_sync_button = self.make_button(u"sync \u21DB", self.left_sync_click)
        rb =self.right_sync_button = self.make_button(u"\u21DA sync", self.right_sync_click)
        ib = self.intersect_button = self.make_button("intersect", self.intersect_click)
        db = self.difference_button = self.make_button("difference", self.difference_click)
        lbuttons = widgets.HBox(children=[ib, db, lb])
        left_stack = widgets.VBox(children=[lbuttons, self.left_expression.assembly])
        right_stack = widgets.VBox(children=[rb, self.right_expression.assembly])
        self.assembly = widgets.HBox(children=[left_stack, right_stack])

    def load_left(self, network_filename, heatmap_filename):
        "Load the left network and heatmap"
        self._load(self.left_expression, network_filename, heatmap_filename)

    def load_right(self, network_filename, heatmap_filename):
        "Load the right network and heatmap"
        self._load(self.right_expression, network_filename, heatmap_filename)

    def _load(self, expression, network_filename, heatmap_filename):
        expression.load_network(network_filename)
        expression.load_heatmap(heatmap_filename)

    def show(self):
        display(self.assembly)

    def make_button(self, description, on_click,
                    disabled=False, width="200px"):
        "Create a button."
        # XXXX refactor to superclass.
        result = widgets.Button(description=description)
        result.on_click(on_click)
        result.disabled = disabled
        result.layout.width = width
        return result

    def right_sync_click(self, b):
        return self.sync_click(self.right_expression, self.left_expression)

    def left_sync_click(self, b):
        return self.sync_click(self.left_expression, self.right_expression)

    def sync_click(self, from_expression, to_expression):
        nodes = from_expression.network.get_selection()
        to_expression.network.set_selection(nodes)
        to_expression.network.display_positions = from_expression.network.display_positions.copy()
        to_expression.network.draw()

    def intersect_click(self, b):
        return self.combine_networks("intersect")

    def difference_click(self, b):
        return self.combine_networks("difference")

    def combine_networks(self, mode):
        left_edges = self.left_expression.network.visible_edges()
        right_edges = self.right_expression.network.visible_edges()
        if mode == "intersect":
            combined_edges = left_edges & right_edges
        elif mode == "difference":
            combined_edges = left_edges.symmetric_difference(right_edges)
        else:
            raise ValueError("bad mode: " + repr(mode))
        if not combined_edges:
            self.left_expression.network.alert("Network %s has no edges" % mode)
            return
        for network in (self.left_expression.network, self.right_expression.network):
            network.restrict_edges(combined_edges)

