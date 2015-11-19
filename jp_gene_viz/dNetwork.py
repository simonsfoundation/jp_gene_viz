
"""
Composite IPython widget for exploring gene expression networks.
"""

import pprint
import ipywidgets as widgets
from IPython.display import display
from jp_svg_canvas import canvas
import dGraph
import dLayout
import color_scale
import color_widget
import fnmatch
import igraph
import json
import os
import traitlets

SELECTION = "SELECTION"

# This function should be called once in a notebook before creating a display.
from jp_svg_canvas.canvas import load_javascript_support


Emilys_colors = """
0.8941  0.1020  0.1098
1.0000  0.4980  0
0.5961  0.3059  0.6392
0.1725  0.4941  0.7216
0.3020  0.6863  0.2902
0   0   0
0.6510  0.3373  0.1569
1.0000  1.0000  0.2000
0.9686  0.5059  0.7490
0.6000  0.6000  0.6000
1.0000  1.0000  1.0000
"""


def set_node_color_levels(network, color_text=Emilys_colors):
    G = network.display_graph
    interpolator = G.get_node_color_interpolator()
    return set_color_levels(interpolator, color_text)


def set_edge_color_levels(network, color_text=Emilys_colors):
    G = network.display_graph
    interpolator = G.get_edge_color_interpolator()
    return set_color_levels(interpolator, color_text)


def set_color_levels(interpolator, color_text=Emilys_colors):
    # split text on lines
    lines = color_text.strip().split("\n")
    # split each line
    lists = [line.split() for line in lines]
    # convert to float in range 0..255
    numlists = [[float(x) * 255 for x in L] for L in lists]
    # convert to color arrays.
    clrlists = [color_scale.clr(*L) for L in numlists]
    # convert to index mapping with indices from 0 to n-1
    clrmapping = dict((count, clr) for (count, clr) in enumerate(clrlists))
    interpolator.set_color_mapping(clrmapping)


class NetworkDisplay(object):

    """
    Create a widget which displays a network with controls for 
    manipulating the network.
    """

    default_side = 10

    def __init__(self):
        self.title_html = widgets.HTML("Gene network")
        self.zoom_button = self.make_button("zoom", self.zoom_click, True)
        self.trim_button = self.make_button("trim", self.trim_click)
        self.layout_button = self.make_button("layout", self.layout_click)
        self.expand_button = self.make_button("expand", self.expand_click)
        self.regulates_button = self.make_button("regulates", self.regulates_click)
        self.targeted_button = self.make_button("targeted by", self.targeted_click)
        self.focus_button = self.make_button("focus", self.focus_click)
        self.restore_button = self.make_button("restore", self.restore_click)
        self.ignore_button = self.make_button("ignore", self.ignore_click)
        self.nodes_button = self.make_button("list nodes", self.nodes_click)
        self.edges_button = self.make_button("list edges", self.edges_click)
        self.layout_dropdown = self.make_layout_dropdown()
        self.labels_button = self.make_checkbox("labels", self.labels_click)
        self.colors_button = self.make_checkbox("colors", self.colors_click)
        self.draw_button = self.make_button("draw", self.draw_click)
        # Assemble the layout
        self.threshhold_assembly = self.make_threshhold_assembly()
        self.pattern_assembly = self.make_pattern_assembly()
        self.info_area = widgets.Textarea(description="status")
        self.colors_assembly = self.make_colors_assembly()
        self.colors_assembly.visible = False
        svg = self.svg = canvas.SVGCanvasWidget()
        sslider = self.size_slider = widgets.FloatSlider(value=500, min=500, max=2000, step=10,
            readout=False, width="150px")
        traitlets.directional_link((sslider, "value"), (svg, "width"))
        traitlets.directional_link((sslider, "value"), (svg, "height"))
        #self.svg = widgets.Button(description="dummy button")
        svg.add_style("background-color", "white")
        svg.watch_event = "click mousedown mouseup mousemove mouseover"
        svg.default_event_callback = self.svg_callback
        left_panel = [self.title_html,
                      self.svg, 
                      self.threshhold_assembly, 
                      self.pattern_assembly,
                      self.info_area]
        self.vertical = widgets.VBox(children=left_panel)
        buttons = [self.zoom_button,
                   self.focus_button,
                   self.ignore_button,
                   self.trim_button,
                   self.expand_button,
                   self.regulates_button,
                   self.targeted_button,
                   self.layout_dropdown,
                   self.layout_button,
                   self.nodes_button,
                   self.edges_button,
                   self.labels_button,
                   self.restore_button,
                   self.size_slider,
                   self.draw_button,
                   self.colors_button,
                   self.colors_assembly]
        self.inputs = widgets.VBox(children=buttons)
        self.assembly = widgets.HBox(children=[self.inputs, self.vertical])
        self.select_start = None
        self.select_end = None
        self.selection_id = None
        self.selecting = False
        self.data_graph = None
        self.data_positions = None
        self.display_positions = None
        self.display_graph = None
        self.selected_nodes = None
        self.svg_origin = dGraph.pos(0, 0)
        self.moving_node = None

    def set_title(self, value):
        self.title_html.value = value

    def make_pattern_assembly(self):
        "Make a pattern match widget area."
        self.pattern_text = widgets.Text(value="")
        self.match_button = self.make_button("match", self.match_click)
        self.pattern_text.on_submit(self.match_click)
        assembly = widgets.HBox(children=[self.match_button, self.pattern_text])
        return assembly

    def make_checkbox(self, description, callback):
        "Make a labels toggle widget."
        #result = widgets.Button(description="labels", value=False)
        result = widgets.Checkbox(description=description, value=False)
        #result.on_click(self.labels_click)
        result.on_trait_change(callback, "value")
        return result

    def make_layout_dropdown(self):
        "Make a layout selection widget."
        options = ["skeleton"]
        for method_name in dir(igraph.Graph):
            if method_name.startswith("layout_"):
                layout_name = method_name[7:]
                options.append(layout_name)
        value = "fruchterman_reingold"
        assert value in options
        w = widgets.Dropdown(options=options, value=value)
        return w

    def make_button(self, description, on_click, disabled=False, width="150px"):
        "Create a button."
        result = widgets.Button(description=description)
        result.on_click(on_click)
        result.disabled = disabled
        result.width = width
        return result

    def make_threshhold_assembly(self):
        "Create widget area related to thresholding."
        self.threshhold_slider = widgets.FloatSlider(value=-0.1, min=-0.1, max=100.0,
                                                    step=0.1, width="300px")
        #self.apply_button = widgets.Button(description="threshhold")
        #self.apply_button.on_click(self.apply_click)
        self.apply_button = self.make_button("threshhold", self.apply_click)
        assembly = widgets.HBox(children=[self.apply_button, self.threshhold_slider])
        return assembly

    def make_colors_assembly(self):
        ncc = self.node_color_chooser = color_widget.ColorChooser()
        ncc.title = "nodes"
        ecc = self.edge_color_chooser = color_widget.ColorChooser()
        ecc.title = "edges"
        assembly = widgets.VBox(children=[ncc.svg, ecc.svg])
        assembly.visible = False # default
        return assembly

    def draw_click(self, b):
        self.svg.empty()
        self.draw()

    def apply_click(self, b):
        "Apply threshhold value to the viewable network."
        self.do_threshhold()
        self.svg.empty()
        self.draw()

    def nodes_click(self, b):
        "display nodes information in the info area."
        nw = self.display_graph.node_weights
        L = []
        for (n,w) in sorted(nw.items()):
            L.append("\t".join([n, str(w)]))
        self.info_area.value = "NODES\n" + "\n".join(L)

    def edges_click(self, b):
        ew = self.display_graph.edge_weights
        L = []
        for ((f,t), w) in sorted(ew.items()):
            L.append("\t".join([f,t,str(w)]))
        self.info_area.value = "EDGES\n" + "\n".join(L)

    def do_threshhold(self, value=None):
        "Restrict viewable edges to have abs(weight) greater than value."
        if value is None:
            value = self.threshhold_slider.value
        # negative value means no threshhold
        if value < 0:
            return
        # do nothing if no data is loaded
        if self.display_graph is None:
            return
        dG = self.data_graph
        G = self.display_graph.clone()
        ew = dG.edge_weights
        nw = G.node_weights
        # find edges between viewable nodes that satisfy threshhold.
        ewG = {}
        for e in ew:
            w = ew[e]
            (f, t) = e
            if f in nw and t in nw and abs(w) >= value:
                ewG[e] = w
        G.edge_weights = ewG
        self.display_graph = G

    def load_data(self, graph, positions=None):
        "Load and draw a graph and positions to the network display."
        if positions is None:
            self.info_area.value = "Computing default layout: " + repr(graph.sizes())
            fit = self.fit_heuristic(graph)
            positions = dLayout.group_layout(graph, fit=fit)
        self.data_positions = positions
        self.display_positions = positions.copy()
        self.data_graph = graph
        self.display_graph = graph.clone()
        ew = graph.edge_weights
        maxw = max(abs(ew[e]) for e in ew) + 1.0
        self.threshhold_slider.max = maxw
        self.do_threshhold()
        self.draw()

    def fit_heuristic(self, graph):
        "Guess an edge size for fitting network layout."
        (esize, nsize) = graph.sizes()
        fit = max(200, min(1000, 2*(esize/4 + nsize)))
        return fit

    def loaded(self):
        "Test whether a network is loaded."
        return (self.display_graph is not None and 
                self.display_positions is not None)

    def draw(self):
        "Draw the network."
        G = self.display_graph
        P = self.display_positions
        if not self.loaded():
            self.info_area.value = "Cannot draw: no graph loaded."
            return
        if not G.node_weights:
            self.info_area.value = "No nodes to draw."
            return
        self.info_area.value = "Drawing graph: " + repr((G.sizes(), len(P)))
        svg = self.svg
        svg.empty()
        self.svg_origin = G.draw(svg, P)
        self.cancel_selection()
        self.info_area.value = "Done drawing: " + repr((G.sizes(), len(P)))
        style = {"font-size": 5, "text-anchor": "middle"}
        color = "black"
        if self.labels_button.value:
            self.info_area.value = "Adding labels."
            nw = G.node_weights
            for node in nw:
                if node in P:
                    (x, y) = P[node]
                    svg.text(None, x, y-4, node, color, **style)
            svg.send_commands()
            self.info_area.value = "Labels added."
        if self.colors_assembly.visible:
            #G.reset_colorization()
            self.info_area.value = "Displaying color choosers."
            ecc = self.edge_color_chooser
            ncc = self.node_color_chooser
            ecc.scale = G.get_edge_color_interpolator()
            ecc.count_values(G.edge_weights.values(), True)
            ncc.scale = G.get_node_color_interpolator()
            ncc.count_values(G.node_weights.values(), True)
            ecc.draw()
            ncc.draw()

    def show(self):
        "Show the network widget."
        display(self.assembly)

    def match_click(self, b):
        "Restrict viewable graph to nodes matching text input."
        self.info_area.value = "match click"
        patterns = self.pattern_text.value.split()
        #print ("patterns", patterns)
        if not patterns:
            self.info_area.value = "No patterns to match."
            return
        nodes = self.data_graph.node_weights.keys()
        selected_nodes = set()
        for pattern in patterns:
            selected_nodes.update(fnmatch.filter(nodes, pattern))
        #print ("found", len(selected_nodes), "of", len(nodes))
        (Gfocus, Pfocus) = self.select_nodes(selected_nodes,
            self.data_graph, self.data_positions)
        self.display_graph = Gfocus
        self.display_positions = Pfocus
        self.do_threshhold()
        self.svg.empty()
        self.draw()

    def labels_click(self, b):
        "Label button click: toggle drawing of labels."
        self.info_area.value = "labels click " + repr(self.labels_button.value)
        self.svg.empty()
        self.draw()

    def colors_click(self, b):
        self.info_area.value = "colors click " + repr(self.colors_button.value)
        self.colors_assembly.visible = self.colors_button.value
        self.svg.empty()
        self.draw()

    def layout_click(self, b):
        "Apply the current layout to the viewable graph."
        self.info_area.value = "layout clicked"
        if not self.loaded:
            self.info_area.value = "Cannot layout: no graph loaded"
        dG = self.display_graph
        fit = self.fit_heuristic(dG)
        layout_selection = self.layout_dropdown.value
        try:
            if layout_selection == "skeleton":
                self.display_positions = dLayout.group_layout(dG, fit=fit)
            else:
                self.display_positions = dLayout.iGraphLayout(dG, layout_selection, fit)
        except Exception as e:
            self.info_area.value = repr(layout_selection) + " layout failed: " + repr(e)
        else:
            self.svg.empty()
            self.draw()

    def regulates_click(self, b):
        return self.expand_click(b, incoming=False, outgoing=True, crosslink=False)

    def targeted_click(self, b):
        return self.expand_click(b, incoming=True, outgoing=False, crosslink=False)

    def expand_click(self, b, incoming=True, outgoing=True, crosslink=True):
        "Add nodes for incoming or outgoing edges from current nodes."
        self.info_area.value = "expand clicked"
        if not self.loaded():
            self.info_area.value = "Cannot expand: no graph loaded."
            return
        threshhold = self.threshhold_slider.value
        dG = self.display_graph
        ew = self.data_graph.edge_weights
        dew = dG.edge_weights.copy()
        dnw = dG.node_weights.copy()
        nodes = set(dnw)
        # find nodes for expansion
        for e in ew:
            # observe threshhold
            w = ew[e]
            if threshhold > 0:
                if abs(w) < threshhold:
                    continue
            if not e in dew:
                (f, t) = e
                addit = False
                if incoming and t in dnw:
                    addit = True
                if outgoing and f in dnw:
                    addit = True
                if addit:
                    nodes.add(f)
                    nodes.add(t)
                    dG.add_edge(f, t, w)
        if crosslink:
            # add new edges for the nodes
            for e in ew:
                if not e in dew:
                    (f, t) = e
                    if f in nodes and t in nodes:
                        w = ew[e]
                        # observe threshhold
                        if threshhold > 0 and abs(w) < threshhold:
                            continue
                        dG.add_edge(f, t, w)
        # position new nodes
        P = self.data_positions
        dP = self.display_positions
        for n in nodes:
            if n not in dP and n in P:
                dP[n] = P[n]
        self.svg.empty()
        self.draw()

    def selection_extrema(self):
        start = self.select_start
        end = self.select_end
        if start is None or end is None:
            return None
        minx = min(start[0], end[0])
        maxx = max(start[0], end[0])
        miny = min(start[1], end[1])
        maxy = max(start[1], end[1])
        maxdiff = max([maxx - minx, maxy - miny, self.default_side])
        return (minx, miny, maxx, maxy, maxdiff)

    def nodes_in_selection(self):
        "Determine the set of nodes in the selection region."
        extrema = self.selection_extrema()
        if extrema is None:
            return None  # no selection
        (minx, miny, maxx, maxy, maxdiff) = extrema
        P = self.display_positions
        G = self.display_graph
        selected = set()
        nw = G.node_weights
        for node in nw:
            npos = P.get(node)
            if npos is not None:
                (px, py) = npos
                if minx <= px and px <= maxx and miny <= py and py <= maxy:
                    selected.add(node)
        return selected

    def focus_click(self, b):
        "View network restricted to nodes under the selection."
        self.info_area.value = "focus clicked"
        selected = self.nodes_in_selection()
        if selected is not None:
            self.select_and_draw(selected)
        else:
            self.info_area.value = "no selection for focus"

    def ignore_click(self, b):
        "Remove selected nodes from view."
        self.info_area.value = "ignore clicked"
        selected = self.nodes_in_selection()
        if selected is not None:
            G = self.display_graph
            unselected = list(set(G.node_weights.keys()) - selected)
            self.select_and_draw(unselected)
        else:
            self.info_area.value = "no selection to ignore."

    def select_and_draw(self, nodes):
        G = self.display_graph
        P = self.display_positions
        (Gfocus, Pfocus) = self.select_nodes(nodes, G, P)
        self.display_graph = Gfocus
        self.svg.empty()
        self.draw()

    def get_selection(self):
        "Get nodes list for currently viewable nodes."
        return sorted(self.display_graph.node_weights.keys())

    def select_nodes(self, nodes, from_graph, from_positions):
        "Get network restricted to nodes list and positions for nodes."
        nodes = set(nodes)
        Gfocus = dGraph.WGraph()
        Pfocus = {}
        ew = from_graph.edge_weights
        nw = from_graph.node_weights
        # add edges
        for e in ew:
            (f, t) = e
            if f in nodes and t in nodes:
                w = ew[e]
                Gfocus.add_edge(f, t, w)
        # add node weighting and positioning
        for node in nodes:
            w = nw.get(node)
            if w is not None:
                Gfocus.node_weights[node] = w
            p = from_positions.get(node)
            if p is not None:
                Pfocus[node] = p
        return (Gfocus, Pfocus)

    def set_selection(self, nodes):
        "Restrict network to the nodes sequence and edges between them."
        (Gfocus, Pfocus) = self.select_nodes(nodes, self.data_graph, self.data_positions)
        self.display_graph = Gfocus
        self.display_positions = Pfocus
        self.do_threshhold()
        self.svg.empty()
        self.draw()

    def zoom_click(self, b):
        "Zoom button click: fit view to selection region."
        #print "zoom"
        self.info_area.value = "zoom clicked"
        extrema = self.selection_extrema()
        if extrema:
            (minx, miny, maxx, maxy, maxdiff) = extrema
            svg = self.svg
            svg.set_view_box(minx, miny, maxdiff, maxdiff)
            self.info_area.value = "set_view_box" + repr((minx, miny, maxdiff, maxdiff))
            svg.send_commands()
        else:
            self.info_area.value = "no selection for zoom"
        # Don't cancel the selection in case the user really wants to focus instead.
        #self.cancel_selection()

    def restore_click(self, b):
        "Restore button click: restore data to loaded state."
        self.display_graph = self.data_graph.clone()
        self.display_positions = self.data_positions.copy()
        self.do_threshhold()
        self.svg.empty()
        self.draw()

    def trim_click(self, b):
        "Trim button click: delete nodes without outgoing edges."
        #print "trim"
        self.info_area.value = "trim clicked"
        G = self.display_graph
        if G is None:
            self.info_area.value = "Cannot trim: no graph loaded."
            return
        self.display_graph = dGraph.trim_leaves(G)
        self.svg.empty()
        self.draw()

    def svg_callback(self, info):
        "Dispatch events over the canvas to handlers."
        typ = info["type"]
        typ_callback = getattr(self, "svg_" + typ, None)
        if typ_callback is not None:
            return typ_callback(info)
        else:
            #self.info_area.value = "No callback for event: " + repr(typ)
            pass

    def event_position(self, info):
        "Get the position array for an event info descriptor."
        x = info.get("svgX")
        y = info.get("svgY")
        return dGraph.pos(x, y)

    def svg_mouseover(self, info):
        "Handle a mouseover over the canvas."
        name = info.get("name")
        shift = info.get("shiftKey")
        if name and not shift:
            self.info_area.value = name
            split = name.split("_")
            L = []
            if len(split) == 2:
                [indicator, data] = split
                if indicator == "NODE":
                    L.append(self.node_detail(data))
                elif indicator == "EDGE":
                    e = json.loads(data)
                    L.append(self.edge_detail(e))
                else:
                    L.append("name " + repr(name))
            self.info_area.value = "\n".join(L)

    def node_detail(self, node):
        "Return a string describing a node of the network."
        dg = self.display_graph
        ew = dg.edge_weights
        nw = dg.node_weights
        incoming = []
        outgoing = []
        for e in ew:
            (f, t) = e
            w = ew[e]
            if f == node:
                outgoing.append((w, e))
            if t == node:
                incoming.append((w, e))
        for L in (incoming, outgoing):
            L.sort()
            L.reverse()
        lines = ["%s : %s" % (node, nw.get(node))]
        lines.append("\nOutgoing:")
        for (w, e) in outgoing:
            lines.append(self.edge_detail(e))
        lines.append("\nIncoming:")
        for (w, e) in incoming:
            lines.append(self.edge_detail(e))
        return "\n".join(lines)
    
    def edge_detail(self, e):
        "Return a string describing an edge of the network."
        e = tuple(e)
        w = self.display_graph.edge_weights.get(e, "no such edge?")
        (f, t) = e
        result = "    %s: %s --> %s" % (w, f, t)
        return result

    def svg_mousedown(self, info):
        "Handle a mousedown over the canvas."
        info_area = self.info_area
        (x, y) = self.event_position(info)
        shift = info.get("shiftKey")
        #info_area.value = pprint.pformat(info)
        info_area.value = ("vbox " + repr(self.svg.viewBox) + 
                           "\nep " + repr((x,y)) +
                           "\noffset " + repr((info.get("offsetX"), info.get("offsetY"))) +
                           "\n" + pprint.pformat(info)
                           )
        # if there is a shift start a selection
        if shift:
            #self.start_selecting(info)
            pass

    def start_selecting(self, info):
        svg = self.svg
        side = self.default_side
        (x, y) = self.event_position(info)
        self.select_start = dGraph.pos(x,y)
        self.select_end = dGraph.pos(x+side, y+side)
        if self.selection_id is None:
            # create a selection rectangle
            svg.rect(SELECTION, x, y, side, side, "black",
                style_dict={"fill-opacity": 0.2})
            self.selection_id = SELECTION
        else:
            atts = {"x": x, "y": y, "width": side, "height": side}
            svg.change_element(self.selection_id, atts)
        svg.send_commands()
        self.selecting = True

    def svg_mouseup(self, info):
        "handle a mouseup over the canvas."
        info_area = self.info_area
        #info_area.value = pprint.pformat(info)
        #self.selecting = False
        if self.select_end is not None:
            self.zoom_button.disabled = False

    def svg_mousemove(self, info):
        "Handle a mousemove over the canvas."
        info_area = self.info_area
        shift = info.get("shiftKey")
        # adjust the selection if it is active.
        if self.selecting:
            self.update_selection(info)
        if self.moving_node:
            self.update_moving_node(info)

    def update_moving_node(self, info):
        moving_node = self.moving_node
        svgX = info["svgX"]
        svgY = info["svgY"]
        svg = self.svg
        positions = self.display_positions
        dG = self.display_graph
        dG.move_node(svg, positions, moving_node, svgX, svgY)

    def update_selection(self, info):
        svg = self.svg
        self.select_end = self.event_position(info)
        extrema = self.selection_extrema()
        assert extrema is not None
        (minx, miny, maxx, maxy, maxdiff) = extrema
        atts = {"x": minx, "y": miny, "width": maxdiff, "height": maxdiff}
        svg.change_element(self.selection_id, atts)
        svg.send_commands()

    def svg_click(self, info):
        "Handle a click on the canvas."
        svg = self.svg
        info_area = self.info_area
        shift = info.get("shiftKey")
        #info_area.value = pprint.pformat(info)
        if shift:
            self.start_selecting(info)
        elif self.selecting:
            self.update_selection(info)
            self.selecting = False
        else:
            if self.selection_id and not shift and not self.selecting:
                self.cancel_selection()
            # if we are moving a node, stop moving it.
            name = info.get("name", "")
            moving_node = self.moving_node
            if self.moving_node:
                self.moving_node = None
                self.draw()
            elif name.startswith("NODE_"):
                # otherwords if it's a node, start moving it
                nodename = name[5:]
                self.moving_node = nodename

    def cancel_selection(self):
        "Remove the circular selection area, if present."
        svg = self.svg
        if self.selection_id:
            svg.delete_names([self.selection_id])
        self.selection_id = self.select_start = self.select_end = None
        svg.send_commands()
        self.zoom_button.disabled = True
        self.selecting = False

    def set_node_weights(self, weights, colors):
        nw = self.display_graph.node_weights
        for node in list(nw):
            nw[node] = weights.get(node, 0)
        self.display_graph.reset_colorization()
        self.display_graph.set_node_color_interpolator(colors)

def display_network(filename, N=None, threshhold=20.0, save_layout=True, show=True):
    import dLayout
    import getData
    assert os.path.exists(filename)
    print ("Reading network", filename)
    G = getData.read_network(filename)
    layoutpath = filename + ".layout.json"
    if os.path.exists(layoutpath):
        print ("Loading saved layout", layoutpath)
        layout = dLayout.load(layoutpath)
    else:
        print ("Computing layout")
        layout = dLayout.group_layout(G)
        if save_layout:
            print ("Saving layout", layoutpath)
            dLayout.dump(layout, layoutpath)
    if N is None:
        N = NetworkDisplay()
    if threshhold:
        N.threshhold_slider.value = threshhold
    N.load_data(G, layout)
    if show:
        N.show()
    return N
