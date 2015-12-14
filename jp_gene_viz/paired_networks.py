
"""
Two networks with coordinated node selection and layouts.
"""

from IPython.display import display
from jp_gene_viz import dNetwork
from ipywidgets import widgets
import traitlets

# Call this once.
from jp_gene_viz.dNetwork import load_javascript_support


class PairedNetworks(traitlets.HasTraits):

    """
    Coordinated networks.
    """

    def __init__(self, *args, **kwargs):
        super(PairedNetworks, self).__init__(*args, **kwargs)
        self.left_network = dNetwork.NetworkDisplay()
        self.right_network = dNetwork.NetworkDisplay()
        lb = self.left_sync_button = self.make_button(u"sync \u21DB", self.left_sync_click)
        rb = self.right_sync_button = self.make_button(u"\u21DA sync", self.right_sync_click)
        ib = self.intersect_button = self.make_button("intersect", self.intersect_click)
        db = self.difference_button = self.make_button("difference", self.difference_click)
        lbuttons = widgets.HBox(children=[ib, db, lb])
        left_stack = widgets.VBox(children=[lbuttons, self.left_network.assembly])
        right_stack = widgets.VBox(children=[rb, self.right_network.assembly])
        self.assembly = widgets.HBox(children=[left_stack, right_stack])

    def load_networks(self, left_filename, right_filename):
        dNetwork.display_network(left_filename, self.left_network, show=False)
        dNetwork.display_network(right_filename, self.right_network, show=False)

    def show(self):
        display(self.assembly)

    def make_button(self, description, on_click,
                    disabled=False, width="200px"):
        "Create a button."
        # XXXX refactor to superclass.
        result = widgets.Button(description=description)
        result.on_click(on_click)
        result.disabled = disabled
        result.width = width
        return result

    def right_sync_click(self, b):
        return self.sync_click(self.right_network, self.left_network)

    def left_sync_click(self, b):
        return self.sync_click(self.left_network, self.right_network)

    def sync_click(self, from_network, to_network):
        nodes = from_network.get_selection()
        to_network.set_selection(nodes)
        to_network.display_positions = from_network.display_positions.copy()
        to_network.draw()

    def intersect_click(self, b):
        return self.combine_networks("intersect")

    def difference_click(self, b):
        return self.combine_networks("difference")

    def combine_networks(self, mode):
        left_edges = self.left_network.visible_edges()
        right_edges = self.right_network.visible_edges()
        if mode == "intersect":
            combined_edges = left_edges & right_edges
        elif mode == "difference":
            combined_edges = left_edges.symmetric_difference(right_edges)
        else:
            raise ValueError("bad mode: " + repr(mode))
        if not combined_edges:
            self.left_network.alert("Network %s has no edges" % mode)
            return
        for network in (self.left_network, self.right_network):
            network.restrict_edges(combined_edges)
