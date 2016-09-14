"""
Multiple network or network/heatmap coordinated display.
"""

from IPython.display import display
from jp_gene_viz import dNetwork
from ipywidgets import widgets
import traitlets
from jp_gene_viz import LExpression

# Call this once.
from jp_gene_viz.dNetwork import load_javascript_support

class MultipleNetworks(traitlets.HasTraits):

    svg_width = traitlets.Int(200)

    def __init__(self, members, *args, **kwargs):
        super(MultipleNetworks, self).__init__(*args, **kwargs)
        self.members = members
        self.member_list = []
        self.holders = []
        self.width_slider = s = widgets.IntSlider(value=self.svg_width, min=100, max=2000, step=10)
        traitlets.directional_link((s, "value"), (self, "svg_width"))
        self.boxes = b = self.make_boxes(self.members)
        self.assembly = widgets.VBox(children=[s,b])

    def make_boxes(self, members, vertical_layout=True):
        klass = widgets.HBox
        if vertical_layout:
            klass = widgets.VBox
        components = []
        for member in members:
            ty = type(member)
            if ty == list:
                component = self.make_boxes(member, not vertical_layout)
            else:
                holder = self.make_holder(member)
                component = holder.assembly
                if member not in self.member_list:
                    self.member_list.append(member)
            components.append(component)
        return klass(children=components)

    def show(self):
        "Show the network widget."
        display(self.assembly)
        for member in self.member_list:
            member.draw()

    def make_holder(self, member):
        ty = type(member)
        if ty == dNetwork.NetworkDisplay:
            result = NetworkHolder(member, self)
        elif ty == LExpression.LinkedExpressionNetwork:
            result = LExpressionHolder(member, self)
        else:
            raise TypeError("Can't make holder for " + repr(ty))
        self.holders.append(result)
        return result

class NetworkHolder(traitlets.HasTraits):

    def __init__(self, network, parent, *args, **kwargs):
        super(NetworkHolder, self).__init__(*args, **kwargs)
        self.network = network
        self.parent = parent
        network.maximize = False
        mcb = self.maximize_cb = widgets.Checkbox(description=u"\u22EF", tooltip="maximize", value=False)
        db = self.diff_button = self.make_button(u"\u2296", self.diff_all, "difference with all")
        ib = self.int_button = self.make_button(u"\u2227", self.intersect_all, "intersect all")
        sb = self.sync_button = self.make_button(u"\u22A8", self.sync_all, "sync all")
        self.width_slider = s = widgets.IntSlider(value=200, min=100, max=2000, step=10,
            readout=False, width="150px")
        s.layout.width = "150px"
        self.make_linkages()
        buttons = widgets.HBox(children=[db, ib, sb, s, mcb])
        self.assembly = widgets.VBox(children=[buttons, network.assembly])

    def make_linkages(self):
        traitlets.link((self.width_slider, "value"), (self.network, "svg_width"))
        traitlets.directional_link((self.parent, "svg_width"), (self.network, "svg_width"))
        traitlets.directional_link((self.maximize_cb, "value"), (self.network, "maximize"))

    def make_button(self, description, on_click, tooltip, width="40px"):
        "Create a button."
        result = widgets.Button(description=description, tooltip=tooltip)
        result.on_click(on_click)
        result.layout.width = width
        return result

    def get_network(self):
        return self.network

    def diff_all(self, b=None):
        return self.restrict_other_edges("diff")

    def intersect_all(self, b=None):
        return self.restrict_other_edges("intersect")

    def restrict_other_edges(self, mode):
        edges = self.get_network().visible_edges()
        for holder in self.parent.holders:
            if holder is not self:
                holder.restrict_edges(edges, mode)

    def restrict_edges(self, edges, mode):
        network = self.get_network()
        my_edges = network.visible_edges()
        if mode == "intersect":
            combined_edges = edges & my_edges
        elif mode == "diff":
            combined_edges = edges.symmetric_difference(my_edges)
        else:
            raise ValueError("unknown mode: " + repr(mode))
        if not combined_edges:
            network.alert("Network %s has no edges" % mode)
        else:
            network.restrict_edges(combined_edges)

    def sync_all(self, b=None):
        network = self.get_network()
        nodes = network.get_selection()
        positions = network.display_positions.copy()
        for holder in self.parent.holders:
            if holder is not self:
                holder.sync_nodes(nodes, positions)

    def sync_nodes(self, nodes, positions):
        network = self.get_network()
        network.set_selection(nodes)
        network.display_positions = positions.copy()
        network.draw()

class LExpressionHolder(NetworkHolder):

    def get_network(self):
        return self.network.network

