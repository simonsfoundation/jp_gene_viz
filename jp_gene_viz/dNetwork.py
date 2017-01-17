
"""
Composite IPython widget for exploring gene expression networks.
"""

import pprint
import ipywidgets as widgets
from IPython.display import display
from jp_svg_canvas import canvas
from jp_gene_viz import js_proxy
from jp_gene_viz import dGraph
from jp_gene_viz import dLayout
from jp_gene_viz import color_scale
from jp_gene_viz import color_widget
from jp_gene_viz import js_context
from jp_gene_viz.json_mixin import JsonMixin
from jp_gene_viz import file_chooser_widget
from jp_gene_viz.widget_utils import set_visibility, is_visible
from jp_gene_viz import proxy_html5_canvas
from jp_gene_viz import grid_forest
from jp_gene_viz import spoke_layout
from jp_gene_viz import simple_tree
from jp_gene_viz import cluster_layout
from jp_gene_viz import category_layout
from jp_gene_viz import getData
import fnmatch
import igraph
import json
import os
import traitlets
import time
import zlib

SELECTION = "SELECTION"

CANVAS = "canvas"
SVG = "SVG"

SKELETON = "skeleton"
SPOKE = "spoke"
FOREST = "forest"
TREE = "tree"
CLUSTER = "cluster"
CATEGORY = "category"

LAYOUTS = [SKELETON, TREE, FOREST, SPOKE, CLUSTER, CATEGORY]

LAYOUT_METHODS = {
    SKELETON: dLayout.group_layout,
    FOREST: grid_forest.forest_layout,
    SPOKE: spoke_layout.spoke_layout,
    TREE: simple_tree.tree_layout,
    CLUSTER: cluster_layout.cluster_layout,
    CATEGORY: category_layout.category_layout,
}

# python-igraph layouts which don't work (in 2d) or abbreviations.
BROKEN_LAYOUTS = set([
    'bipartite',
    #'drl',
    'fruchterman_reingold_3d',
    'grid_3d',
    'grid_fruchterman_reingold',
    'kamada_kawai_3d',
    'random_3d',
    'sphere',
])

OUTLINE_LABEL_STYLE = {
    "font-style": "italic",
    "text-anchor": "middle",
    "stroke": "white",
    "font-weight": "bold",
    "stroke-width": 0.2,
}

NO_OUTLINE_LABEL_STYLE = {
    "font-style": "italic",
    "text-anchor": "middle",
    "font-weight": "bold",
}

# This function should be called once in a notebook before creating a display.
#from jp_svg_canvas.canvas import load_javascript_support

def load_javascript_support(verbose=False):
    canvas.load_javascript_support()
    js_proxy.load_javascript_support()
    js_context.load_if_not_loaded(["color_cursor.js"])


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


class NetworkDisplay(traitlets.HasTraits, JsonMixin):

    """
    Create a widget which displays a network with controls for 
    manipulating the network.
    """

    maximize = traitlets.Bool(True)
    svg_width = traitlets.Int(500)
    rectangle_color = traitlets.Unicode("#edefef")

    json_atts = "threshhold label_position_overrides".split()

    json_objects = {
        "data_graph": dGraph.WGraph,
        "display_graph": dGraph.WGraph,
        "data_positions": dLayout.layoutConverter,
        "display_positions": dLayout.layoutConverter,
    }

    threshhold = traitlets.Float()

    default_side = 10

    dialog_time = None

    dialog_timeout = 5

    label_style = OUTLINE_LABEL_STYLE

    # The motif collection to use for looking up motif data.
    motif_collection = None

    # Mapping of node to node category.
    node_categories = None

    def __init__(self, container=SVG, *pargs, **kwargs):
        super(NetworkDisplay, self).__init__(*pargs, **kwargs)
        containers = [SVG, CANVAS]
        assert container in containers, "valid containers: " + repr(containers)
        self.title_html = widgets.HTML("Gene network")
        cd = self.container_dropdown = widgets.Dropdown(options=containers, value=container)
        cd.layout.width = "150px"
        cd.on_trait_change(self.handle_container_change, "value")
        self.zoom_button = self.make_button("zoom", self.zoom_click, True)
        self.trim_button = self.make_button("trim", self.trim_click)
        self.layout_button = self.make_button("layout", self.layout_click)
        self.expand_button = self.make_button("expand", self.expand_click)
        self.regulates_button = self.make_button("regulates", self.regulates_click)
        self.regulates_edges_button = self.make_button("reg edges", self.regulates_edges_click)
        self.targeted_button = self.make_button("targeted by", self.targeted_click)
        self.focus_button = self.make_button("focus", self.focus_click)
        self.restore_button = self.make_button("restore", self.restore_click)
        self.ignore_button = self.make_button("ignore", self.ignore_click)
        self.nodes_button = self.make_button("list nodes", self.nodes_click)
        self.edges_button = self.make_button("list edges", self.edges_click)
        self.layout_dropdown = self.make_layout_dropdown()
        self.labels_button = self.make_checkbox("labels", self.labels_click)
        self.settings_button = self.make_checkbox("settings", self.settings_click)
        self.motifs_button = self.make_checkbox("show motifs", self.show_motifs)
        #self.motifs_button.visible = False
        set_visibility(self.motifs_button, False)
        self.motifs_button.value = True
        self.draw_button = self.make_button("draw", self.draw_click)
        self.tf_only_button = self.make_button("TF only", self.tf_only_click)
        self.split_button = self.make_button("split", self.split_click)
        self.connected_only_button = self.make_button("connected only", self.connected_only_click)
        # Assemble the layout
        self.threshhold_assembly = self.make_threshhold_assembly()
        self.pattern_assembly = self.make_pattern_assembly()
        self.info_area = widgets.Textarea(description="status")
        self.settings_assembly = self.make_settings_assembly()
        self.dialog = self.make_dialog()
        #self.settings_assembly.visible = False
        set_visibility(self.settings_assembly, False)
        # Display containers
        svg = self.svg = canvas.SVGCanvasWidget()
        self.canvas = proxy_html5_canvas.HTML5CanvasProxy()
        sslider = self.size_slider = widgets.IntSlider(value=500, min=100, max=2000, step=10,
            readout=False, width="150px")
        sslider.layout.width = "150px"
        self.depth_slider = widgets.IntSlider(
            description="depth", value=0, min=0, max=5, width="200px")
        # XXX make this smaller without making the slider vanish...
        self.depth_slider.layout.width = "200px"
        # Adjust the width and height of the svg when the size slider changes.
        traitlets.link((self, "svg_width"), (sslider, "value"))
        # Force svg format if the width changes
        self.on_trait_change(self.force_svg, "svg_width")
        for display in (svg, self.canvas):
            traitlets.directional_link((sslider, "value"), (display, "svg_width"))
            traitlets.directional_link((sslider, "value"), (display, "svg_height"))
        # List of elements which only work for SVG container
        self.requires_SVG = [
            self.zoom_button,
            self.focus_button,
            self.ignore_button,
            self.size_slider,
        ]
        # Adjust the svg view box when the bounding box changes.
        svg.on_trait_change(self.handle_bounding_box_change, "boundingBox")
        svg.add_style("background-color", "white")
        svg.watch_event = "click mousedown mouseup mousemove mouseover"
        svg.default_event_callback = self.svg_callback
        hr = self.hideable_right = widgets.VBox(
            children=[self.threshhold_assembly, self.pattern_assembly, self.info_area, self.settings_assembly])
        #traitlets.directional_link((self, "maximize"), (hr, "visible"))
        self.on_trait_change(self.handle_maximize_change, "maximize")
        right_panel = [self.title_html,
                      self.svg,
                      self.canvas.widget,
                      self.hideable_right]
        self.vertical = widgets.VBox(children=right_panel)
        buttons = [self.container_dropdown,
                   self.zoom_button,
                   self.focus_button,
                   self.ignore_button,
                   self.trim_button,
                   self.expand_button,
                   self.regulates_button,
                   self.regulates_edges_button,
                   self.targeted_button,
                   self.tf_only_button,
                   self.split_button,
                   self.connected_only_button,
                   self.layout_dropdown,
                   self.layout_button,
                   self.nodes_button,
                   self.edges_button,
                   self.labels_button,
                   self.restore_button,
                   self.size_slider,
                   self.draw_button,
                   self.depth_slider,
                   self.motifs_button,
                   self.settings_button,
                   #self.settings_assembly,
                   ]
        self.inputs = widgets.VBox(children=buttons)
        #traitlets.directional_link((self, "maximize"), (self.inputs, "visible"))
        dummy = self.dummy_widget = js_proxy.ProxyWidget()
        # Note: dummy widget has the entire assembly as its parent.
        #    So code can modify the parent using d.element().parent().
        self.assembly = widgets.HBox(children=[self.inputs, self.vertical, self.dialog, dummy])
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
        # svg name to color override dictionary
        self.color_overrides = {}
        # node weight override mapping
        self.override_node_weights = None
        # node color mapper override
        self.override_node_colors = None
        self.group_rectangles = None
        #self.rectangle_color = None
        self.reset_interactive_bookkeeping()
        self.handle_container_change()

    def handle_container_change(self, *args):
        choice = self.container_dropdown.value
        chose_svg = True
        if choice == SVG:
            self.svg.viewBox = self.canvas.viewBox
        elif choice == CANVAS:
            chose_svg = False
            self.canvas.viewBox = self.svg.viewBox
        else:
            raise ValueError("invalid container choice " + repr(choice))
        set_visibility(self.svg, chose_svg)
        set_visibility(self.canvas.widget, not chose_svg)
        for widget in self.requires_SVG:
            set_visibility(widget, chose_svg)
        self.draw()

    def force_svg(self, *args):
        "Force SVG format"
        # this will trigger a call to handle_container_change
        self.container_dropdown.value = SVG

    def chosen_container(self):
        choice = self.container_dropdown.value
        if choice == SVG:
            return self.svg
        elif choice == CANVAS:
            return self.canvas
        else:
            raise ValueError("invalid container choice " + repr(choice))

    def colorize_cursor(self, color):
        "Set the cursor to the given color"
        d = self.dummy_widget
        assembly = d.element().parent()
        d(assembly.color_cursor(color))
        d.flush()

    def uncolorize_cursor(self):
        "Restore cursor to default behavior."
        d = self.dummy_widget
        assembly = d.element().parent()
        d(assembly.color_cursor_reset())
        d.flush()

    def reset_interactive_bookkeeping(self):
        self.moving_node = None
        self.moving_label = None
        self.label_position_overrides = {}

    def set_title(self, value):
        self.title_html.value = value

    def make_dialog(self):
        "Make a dialog widget and hide it for now."
        w = js_proxy.ProxyWidget()
        e = w.element()
        w(e.html("Temporary content for dialog").dialog())
        w(e.dialog("close"))
        w.flush()
        return w

    def make_pattern_assembly(self):
        "Make a pattern match widget area."
        self.pattern_text = widgets.Text(value="")
        self.match_button = self.make_button("match", self.match_click)
        self.pattern_text.on_submit(self.match_click)
        assembly = widgets.HBox(children=[self.match_button, self.pattern_text])
        return assembly

    def make_checkbox(self, description, callback, value=False):
        "Make a labels toggle widget."
        #result = widgets.Button(description="labels", value=False)
        result = widgets.Checkbox(description=description, value=value)
        #result.on_click(self.labels_click)
        if callback is not None:
            result.on_trait_change(callback, "value")
        return result

    def make_layout_dropdown(self):
        "Make a layout selection widget."
        options = list(LAYOUTS)
        for method_name in dir(igraph.Graph):
            if method_name.startswith("layout_"):
                layout_name = method_name[7:]
                if layout_name not in BROKEN_LAYOUTS:
                    options.append(layout_name)
        value = "fruchterman_reingold"
        assert value in options
        w = widgets.Dropdown(options=options, value=value)
        w.layout.width = "150px"
        return w

    def make_button(self, description, on_click, disabled=False, width="150px"):
        "Create a button."
        result = widgets.Button(description=description)
        result.on_click(on_click)
        result.disabled = disabled
        result.layout.width = width
        return result

    def make_threshhold_assembly(self):
        "Create widget area related to thresholding."
        self.threshhold_slider = widgets.FloatSlider(value=-0.1, min=-0.1, max=100.0,
                                                    step=0.1, width="200px")
        self.threshhold_slider.layout.width = "200px"
        #self.apply_button = widgets.Button(description="threshhold")
        #self.apply_button.on_click(self.apply_click)
        # makd the local variable "threshhold" an alias for the slider valut
        traitlets.link((self.threshhold_slider, "value"), (self, "threshhold"))
        self.apply_button = self.make_button("threshold", self.apply_click)
        sign_options = ["+- all", "- only", "+ only"]
        sign_default = sign_options[0]
        self.threshhold_sign_dropdown = widgets.Dropdown(options=sign_options, value=sign_default, width="50px")
        self.threshhold_sign_dropdown.layout.width = "50px"
        assembly = widgets.HBox(
            children=[self.apply_button, self.threshhold_slider, self.threshhold_sign_dropdown])
        return assembly

    def make_settings_assembly(self):
        # label size sliders
        font_sl = self.font_size_slider = widgets.IntSlider(
            description="labels",
            value=7, min=0, max=20, width="50px")
        font_fsl = self.tf_font_size_slider = widgets.IntSlider(
            description="tf labels",
            value=7, min=5, max=20, width="50px")
        self.label_outline_checkbox = locb = self.make_checkbox("outlined", self.outlined_click, value=True)
        font_sl.layout.width = "200px"
        font_fsl.layout.width = "200px"
        # colorize area
        cb = self.colorize_checkbox = self.make_checkbox("manual colorize", self.colorize_click)
        cp = self.color_picker = color_widget.ColorPicker()
        uc = self.undo_colorize_button = self.make_button("reset default", self.uncolorize_click)
        cp.draw()
        #cp.svg.visible = False
        set_visibility(cp.svg, False)
        #traitlets.directional_link((cb, "value"), (cp.svg, "visible"))
        cp.on_trait_change(self.colorize_click, "color")
        colorize_area = widgets.VBox(children=[cb, cp.svg, uc])
        # node and edge color choosers
        ncc = self.node_color_chooser = color_widget.ColorChooser()
        ncc.title = "nodes"
        ecc = self.edge_color_chooser = color_widget.ColorChooser()
        ecc.title = "edges"
        w = "150px"
        rect_color_tb = self.rectangle_color_textbox = widgets.Text(value="#edefef", description="cluster boundary color")
        traitlets.link((rect_color_tb, "value"), (self, "rectangle_color"))
        # file save area
        self.filename_button = self.make_button("save/load file name", self.filename_click, width=w)
        self.save_button = self.make_button("save", self.save_click, width=w)
        self.load_button = self.make_button("load", self.load_click, width=w)
        self.upload_button = self.make_button("upload/download", self.upload_click, width=w)
        self.filename_text = widgets.Text(value='')
        labels_sliders = widgets.HBox(children=[font_sl, font_fsl, locb])
        color_choosers = widgets.HBox(children=[ncc.svg, ecc.svg, colorize_area])
        fmt = self.format_dropdown = widgets.Dropdown(options=["PNG", "TIFF"], value="PNG")
        fmt.layout.width = "50px"
        iss = self.image_side_slider = widgets.IntSlider(
            description="side", value=1000, min=500, max=4000, width="100px")
        sfn = self.snapshot_filename_text = widgets.Text(
            description="Snapshot filename:", value=self.title_html.value)
        snp = self.snapshot_button = self.make_button("snapshot", self.snapshot_click)
        pcb = self.preview_checkbox = self.make_checkbox('show preview', None)
        pcb.value = False
        snap_file_area = widgets.HBox(children=[sfn, pcb])
        file_input = widgets.HBox(children=[
            self.filename_button, self.filename_text])
        file_buttons = widgets.HBox(children=[
            self.save_button, self.load_button, self.upload_button])
        snapshot_area = widgets.HBox(children=[fmt, iss, snp])
        assembly = widgets.VBox(children=[
            labels_sliders, 
            color_choosers,
            rect_color_tb,
            file_input,
            file_buttons,
            snap_file_area,
            snapshot_area])
        #assembly = widgets.VBox(children=[font_sl, font_fsl, ncc.svg, ecc.svg])
        #assembly.visible = False # default
        set_visibility(assembly, False)
        return assembly

    def outlined_click(self, *args):
        if self.label_outline_checkbox.value:
            self.label_style = OUTLINE_LABEL_STYLE
        else:
            self.label_style = NO_OUTLINE_LABEL_STYLE

    def uncolorize_click(self, *args):
        self.color_overrides = {}
        self.reset_node_weights()
        self.display_graph.reset_colorization()
        self.draw()

    def colorize_click(self, *args):
        checked = self.colorize_checkbox.value
        set_visibility(self.color_picker.svg, checked)
        set_visibility(self.node_color_chooser.svg, not checked)
        set_visibility(self.edge_color_chooser.svg, not checked)
        if checked:
            #self.color_picker.svg.visible = True
            #self.node_color_chooser.svg.visible = False
            #self.edge_color_chooser.svg.visible = False
            self.colorize_cursor(self.color_picker.color)
        else:
            #self.color_picker.svg.visible = False
            #self.node_color_chooser.svg.visible = True
            #self.edge_color_chooser.svg.visible = True
            self.uncolorize_cursor()

    def filename_click(self, b=None):
        # XXXX this may leak memory? Does it matter?
        self.info_area.value = "filename click"
        chooser = file_chooser_widget.FileChooser(
            upload=False, message="choose folder and filename", folders=True)
        fn = self.filename_text
        traitlets.directional_link((chooser, "file_path"), (fn, "value"))
        chooser.show()

    def get_network_container(self):
        choice = self.container_dropdown.value
        if choice == SVG:
            return self.svg
        elif choice == CANVAS:
            return self.canvas
        else:
            raise ValueError("invalid container choice " + repr(choice))

    def snapshot_click(self, b=None):
        from jp_svg_canvas import fake_svg
        self.info_area.value = "snapshot click"
        title = self.snapshot_filename_text.value
        file_prefix = title
        if not title or "<" in title:
            file_prefix = "gene_network"
        format = self.format_dropdown.value.lower()
        filename = file_prefix
        if "." not in file_prefix:
            filename = file_prefix + "." + format
        mime_type = "image/" + format
        svg = self.svg
        dimension = self.image_side_slider.value
        container = self.get_network_container()
        fsvg = fake_svg.FakeCanvasWidget(container.viewBox, filename, mime_type, dimension)
        self.draw(fit=False, svg=fsvg)
        preview = self.preview_checkbox.value
        # XXXX for debugging!!!
        #open("embedding.js", "w").write(fsvg.embedding())
        fsvg.embed(preview=preview)

    def save_click(self, b=None):
        self.info_area.value = "save click"
        filename = self.filename_text.value
        try:
            f = open(filename, "wb")
        except Exception:
            return self.alert("could not write filename: " + repr(filename))
        json = self.as_json()
        zjson = zlib.compress(json)
        f.write(zjson)
        f.close()
        msg = "saved %s bytes as zipped JSON to %s" % (len(zjson), repr(filename))
        self.alert(msg)

    def load_click(self, b=None):
        self.info_area.value = "restore click"
        filename = self.filename_text.value
        try:
            f = open(filename, "rb")
        except Exception:
            return self.alert("could not read filename: " + repr(filename))
        zjson = f.read()
        try:
            json_string = zlib.decompress(zjson)
        except Exception:
            return self.alert("could not unzip " + repr(filename))
        try:
            json_object = json.loads(json_string)
        except Exception:
            return self.alert("could not parse as JSON " + repr(filename))
        try:
            self.from_json_value(json_object)
            pass
        except Exception:
            self.alert("error loading JSON value " + repr(filename))
            raise
        self.draw()
        msg = "loaded JSON value " + repr(filename)
        self.alert(msg)
        self.info_area.value = msg

    def upload_click(self, b=None):
        # XXXX this may leak memory? Does it matter?
        self.info_area.value = "upload click"
        chooser = file_chooser_widget.FileChooser(
            upload=True, message="choose folder and filename")
        chooser.enable_downloads()
        chooser.show()

    def draw_click(self, b=None):
        #self.svg.empty()
        self.draw()

    def apply_click(self, b=None):
        "Apply threshhold value to the viewable network."
        self.reset_interactive_bookkeeping()
        self.do_threshhold()
        #self.svg.empty()
        self.draw()

    def nodes_click(self, b=None):
        "display nodes information in the info area."
        nw = self.display_graph.node_weights
        L = []
        for (n,w) in sorted(nw.items()):
            L.append("\t".join([n, str(w)]))
        self.info_area.value = "NODES\n" + "\n".join(L)

    def edges_click(self, b=None):
        ew = self.display_graph.edge_weights
        L = []
        for ((f,t), w) in sorted(ew.items()):
            L.append("\t".join([f,t,str(w)]))
        self.info_area.value = "EDGES\n" + "\n".join(L)

    def do_threshhold(self, value=None):
        "Restrict viewable edges to have abs(weight) greater than value (respect sign dropdown)."
        if value is None:
            value = self.threshhold_slider.value
        add_positives = add_negatives = True
        sign_dropdown_value = self.threshhold_sign_dropdown.value
        if "+" not in sign_dropdown_value:
            add_positives = False
        elif "-" not in sign_dropdown_value:
            add_negatives = False
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
        # find edges between viewable nodes that satisfy threshhold and sign constraint.
        ewG = {}
        for e in ew:
            w = ew[e]
            if w > 0 and not add_positives:
                continue
            if w < 0 and not add_negatives:
                continue
            (f, t) = e
            if f in nw and t in nw and abs(w) >= value:
                ewG[e] = w
        G.edge_weights = ewG
        self.display_graph = G
        self.set_node_weights()

    def load_data(self, graph, positions=None, draw=True):
        "Load and draw a graph and positions to the network display."
        if positions is None:
            self.info_area.value = "Computing default layout: " + repr(graph.sizes())
            fit = self.fit_heuristic(graph)
            positions = dLayout.group_layout(graph, fit=fit)
        else:
            # match names ignoring case
            nodes = list(graph.node_weights.keys())
            lcmap = getData.lower_case_map(graph.node_weights.keys())
            fix = {}
            for name in positions:
                location = positions[name]
                fix_name = lcmap.get(name.lower(), name)
                fix[fix_name] = location
            positions = fix
        self.data_positions = positions
        #self.display_positions = positions.copy()
        self.set_layout(positions.copy())
        self.data_graph = graph
        self.display_graph = graph.clone()
        self.override_node_colors = None
        self.override_node_weights = None
        ew = graph.edge_weights
        if ew:
            maxw = max(abs(ew[e]) for e in ew) + 1.0
            self.threshhold_slider.max = maxw
            self.do_threshhold()
        self.reset_interactive_bookkeeping()
        if draw:
            self.draw()

    def fit_heuristic(self, graph=None):
        "Guess an edge size for fitting network layout."
        if graph is None:
            graph = self.display_graph
        (esize, nsize) = graph.sizes()
        fit = max(200, min(1000, 2*(esize/4 + nsize)))
        return fit

    def loaded(self):
        "Test whether a network is loaded."
        return (self.display_graph is not None and 
                self.display_positions is not None)

    def draw(self, fit=True, svg=None):
        "Draw the network."
        G = self.display_graph
        P = self.display_positions
        rectangles = self.group_rectangles
        color_overrides = self.color_overrides
        if not self.loaded():
            self.info_area.value = "Cannot draw: no graph loaded."
            return
        if not G.node_weights:
            self.info_area.value = "No nodes to draw."
            return
        self.info_area.value = "Drawing graph: " + repr((G.sizes(), len(P)))
        if svg is None:
            #svg = self.svg
            svg = self.chosen_container()
            svg.empty()
        rcolor = self.rectangle_color.strip()
        if rcolor and rectangles is not None:
            for (x, y, w, h) in rectangles.values():
                xw = x + w
                yh = y + h
                svg.line("group_border", x, y, xw, y, rcolor)
                svg.line("group_border", xw, y, xw, yh, rcolor)
                svg.line("group_border", xw, yh, x, yh, rcolor)
                svg.line("group_border", x, yh, x, y, rcolor)
        self.svg_origin = G.draw(svg, P, 
            fit=fit, color_overrides=color_overrides, send=False)
        self.cancel_selection()
        self.info_area.value = "Done drawing: " + repr((G.sizes(), len(P)))
        font_size = self.font_size_slider.value
        tf_font_size = self.tf_font_size_slider.value
        #style0 = {"font-size": font_size, "text-anchor": "middle"}
        style0 = self.label_style.copy()
        style0["font-size"] = font_size
        #color = "black"
        if self.labels_button.value:
            nw = G.node_weights
            sources = set(G.get_node_to_descendants())
            self.info_area.value = "Adding labels."
            # find the max position
            #max_x = max(position[0] for position in [P[n] for n in nw])
            #left_x = max_x * 0.25
            #right_x = max_x * 0.75
            overrides = self.label_position_overrides
            for node in nw:
                if node in P:
                    (x, y) = P[node]
                    if node in overrides:
                        (x, y) = overrides[node]
                    style = style0.copy()
                    if node in sources and tf_font_size > font_size:
                        style["font-size"] = tf_font_size
                    lname = self.label_name(node)
                    color = color_overrides.get(lname, "black")
                    # If font-size is zero, don't show the text
                    if style["font-size"] != 0:
                        svg.text(lname, x, y-4, node, color, **style)
            if fit:
                # async: get svg bounding box
                svg.fit(False)
            self.info_area.value = "Labels added."
        svg.send_commands()
        if is_visible(self.settings_assembly):
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

    def match_click(self, b=None):
        "Restrict viewable graph to nodes matching text input."
        self.info_area.value = "match click"
        patterns = self.pattern_text.value.lower().split()
        #print ("patterns", patterns)
        if not patterns:
            self.info_area.value = "No patterns to match."
            return
        nodes = list(self.data_graph.node_weights.keys())
        lowernodes = [s.lower() for s in nodes]
        selected_nodes_lower = set()
        for pattern in patterns:
            selected_nodes_lower.update(fnmatch.filter(lowernodes, pattern))
        selected_nodes = getData.caseless_intersection_list(nodes, selected_nodes_lower)
        #print ("found", len(selected_nodes), "of", len(nodes))
        (Gfocus, Pfocus) = self.select_nodes(selected_nodes,
            self.data_graph, self.data_positions)
        self.display_graph = Gfocus
        self.set_node_weights()
        #self.display_positions = Pfocus
        self.set_layout(Pfocus)
        self.reset_interactive_bookkeeping()
        self.do_threshhold()
        #self.svg.empty()
        self.draw()

    def limit_edges(self, limit):
        ew = self.data_graph.edge_weights
        order = sorted((abs(ew[e]), e) for e in ew)
        dG = dGraph.WGraph()
        for (count, (weight, edge)) in enumerate(reversed(order)):
            (a, b) = edge
            dG.add_edge(a, b, ew[edge])
            if count > limit:
                break
        self.display_graph = dG
        minw = min(abs(x) for x in dG.edge_weights.values())
        self.threshhold_slider.value = minw
        self.do_threshhold()
        self.draw()

    def labels_click(self, b=None):
        "Label button click: toggle drawing of labels."
        self.info_area.value = "labels click " + repr(self.labels_button.value)
        #self.svg.empty()
        self.draw()

    def settings_click(self, b=None):
        checked = self.settings_button.value
        set_visibility(self.settings_assembly, checked)
        #self.svg.empty()
        self.draw()
        self.info_area.value = "settings " + repr(checked)

    def show_motifs(self, b=None):
        # do nothing
        pass

    def split_click(self, b=None):
        """
        Split nodes with positive end points above, negative below, interior middle.
        """
        self.layout_click(draw=False)
        layout_positions = self.display_positions
        dG = self.display_graph
        height = self.fit_heuristic(dG)
        ew = dG.edge_weights
        sources = set(s for (s, d) in ew)
        total_weights = {}
        for edge in ew:
            (s, d) = edge
            total_weights[d] = total_weights.get(d, 0) + ew[edge]
        negative_destinations = set(d for d in total_weights if total_weights[d] < 0) - sources
        positive_destinations = set(total_weights) - (sources | negative_destinations)
        scale = 1.0/3.0
        negative_shift = 2 * scale * height
        interior_shift = scale * height
        positive_shift = 0
        split_positions = {}
        for s in sources:
            p = layout_positions[s]
            split_positions[s] = dGraph.pos(p[0], p[1] * scale + interior_shift)
        for d in positive_destinations:
            p = layout_positions[d]
            split_positions[d] = dGraph.pos(p[0], p[1] * scale + positive_shift)
        for d in negative_destinations:
            p = layout_positions[d]
            split_positions[d] = dGraph.pos(p[0], p[1] * scale + negative_shift)
        #self.display_positions = split_positions
        self.set_layout(split_positions)
        self.svg.empty()
        self.draw()

    def apply_layout(self, layout, rectangles=None):
        self.info_area.value = "applying layout"
        #self.display_positions = layout
        self.set_layout(layout, rectangles)
        self.draw()

    def set_layout(self, layout, rectangles=None):
        self.reset_interactive_bookkeeping()
        self.display_positions = layout
        self.group_rectangles = rectangles

    def layout_click(self, b=None, draw=True):
        "Apply the current layout to the viewable graph."
        self.reset_interactive_bookkeeping()
        self.info_area.value = "layout clicked"
        if not self.loaded:
            self.info_area.value = "Cannot layout: no graph loaded"
        dG = self.display_graph
        fit = self.fit_heuristic(dG)
        layout_selection = self.layout_dropdown.value
        rectangles = {}
        try:
            if layout_selection in LAYOUT_METHODS:
                method = LAYOUT_METHODS[layout_selection]
                (display_positions, rectangles) = method(dG, fit=fit, 
                    node_categories=self.node_categories)
            else:
                display_positions = dLayout.iGraphLayout(dG, layout_selection, fit)
        except Exception as e:
            self.info_area.value = repr(layout_selection) + " layout failed: " + repr(e)
        else:
            self.set_layout(display_positions, rectangles)
            if draw:
                self.svg.empty()
                self.draw()
            #self.svg.empty()

    def regulates_click(self, b=None):
        return self.expand_click(b, incoming=False, outgoing=True, crosslink=True)

    def regulates_edges_click(self, b=None):
        return self.expand_click(b, incoming=False, outgoing=True, crosslink=False)

    def targeted_click(self, b=None):
        return self.expand_click(b, incoming=True, outgoing=False, crosslink=True)

    def expand_click(self, b, incoming=True, outgoing=True, crosslink=True):
        "Add nodes for incoming or outgoing edges from current nodes."
        self.info_area.value = "expand clicked"
        if not self.loaded():
            self.info_area.value = "Cannot expand: no graph loaded."
            return
        dG = self.display_graph
        ew = self.data_graph.edge_weights
        dew = dG.edge_weights.copy()
        dnw = dG.node_weights.copy()
        nodes = set(dnw)
        threshhold = self.threshhold_slider.value
        # find nodes for expansion
        for e in ew:
            # observe threshhold
            w = ew[e]
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
                        dG.add_edge(f, t, w)
        # position new nodes
        P = self.data_positions
        dP = self.display_positions
        for n in nodes:
            if n not in dP and n in P:
                dP[n] = P[n]
        if crosslink:
            self.do_threshhold()
        self.set_node_weights()
        #self.svg.empty()
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
        # use square area
        maxx = minx + maxdiff
        maxy = miny + maxdiff
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

    def alert_no_selection(self, operation):
        self.info_area.value = "no selection for " + operation
        self.alert("Please shift-click then click to select region for " + operation)

    def focus_click(self, b=None):
        "View network restricted to nodes under the selection."
        self.info_area.value = "focus clicked"
        selected = self.nodes_in_selection()
        if selected is not None:
            self.select_and_draw(selected)
        else:
            self.alert_no_selection("focus")

    def ignore_click(self, b=None):
        "Remove selected nodes from view."
        self.info_area.value = "ignore clicked"
        selected = self.nodes_in_selection()
        if selected is not None:
            G = self.display_graph
            unselected = list(set(G.node_weights.keys()) - selected)
            self.select_and_draw(unselected)
        else:
            self.alert_no_selection("ignore")

    def tf_only_click(self, b=None):
        "restrict nodes the transcription factors (nodes with outgoing edges, visible or not)."
        dG = self.data_graph
        G = self.display_graph
        sources = set(dG.get_node_to_descendants())
        visible = set(G.node_weights)
        visible_tfs = sources & visible
        if not visible_tfs:
            self.alert("no transcription factors are visible")
        else:
            self.select_and_draw(list(visible_tfs))

    def connected_only_click(self, b=None):
        "remove from view nodess not connected to any other visible node"
        G = self.display_graph
        n2d = G.get_node_to_descendants()
        sources = set(n2d)
        destinations = set()
        for node in n2d:
            destinations.update(n2d[node])
        connected = destinations | sources
        if not connected:
            self.alert("no connected nodes are visible")
        else:
            self.select_and_draw(list(connected))

    def select_and_draw(self, nodes):
        G = self.display_graph
        P = self.display_positions
        (Gfocus, Pfocus) = self.select_nodes(nodes, G, P)
        self.display_graph = Gfocus
        self.set_node_weights()
        #self.svg.empty()
        self.draw()

    def get_selection(self):
        "Get nodes list for currently viewable nodes."
        return sorted(self.display_graph.node_weights.keys())

    def get_data_nodes(self, matching_nodes=None):
        dnodes = set(self.data_graph.node_weights.keys())
        if matching_nodes is None:
            return sorted(dnodes)
        else:
            return getData.caseless_intersection_list(matching_nodes, dnodes, use_left=False)

    def select_nodes(self, nodes, from_graph, from_positions):
        "Get network restricted to nodes list and positions for nodes."
        nodes = set(self.get_data_nodes(nodes))
        if self.display_graph is None:
            Gfocus = dGraph.WGraph()
        else:
            Gfocus = self.display_graph.same_colors()
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

    def restrict_edges(self, edge_restriction):
        "Show only nodes and edges listed in edge_restriction."
        # adjust name cases to match local conventions
        lcmap = getData.lower_case_map(self.get_data_nodes())
        edge_restriction = set((lcmap.get(a.lower(), a), lcmap.get(b.lower(), b)) for (a,b) in edge_restriction)
        dG = self.display_graph
        edge_weights = dG.edge_weights
        node_weights = dG.node_weights
        current_edges = set(edge_weights.keys())
        keep_edges = edge_restriction & current_edges
        keep_nodes = set([x[0] for x in keep_edges] +
            [x[1] for x in keep_edges])
        dG.edge_weights = dict((e, edge_weights[e])
            for e in edge_weights if e in keep_edges)
        dG.node_weights = dict((n, node_weights[n])
            for n in node_weights if n in keep_nodes)
        self.set_node_weights()
        self.draw()

    def visible_edges(self):
        return set(self.display_graph.edge_weights.keys())

    def set_selection(self, nodes):
        "Restrict network to the nodes sequence and edges between them."
        (Gfocus, Pfocus) = self.select_nodes(nodes, self.data_graph, self.data_positions)
        self.display_graph = Gfocus
        self.display_positions = Pfocus
        self.do_threshhold()
        #self.svg.empty()
        self.draw()

    def zoom_click(self, b=None):
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
            self.alert_no_selection("zoom")
        # Don't cancel the selection in case the user really wants to focus instead.
        #self.cancel_selection()

    def restore_click(self, b=None):
        "Restore button click: restore data to loaded state."
        new_display_graph = self.data_graph.clone()
        new_display_graph.reset_colorization(self.display_graph)
        self.display_graph = new_display_graph
        #self.display_positions = self.data_positions.copy()
        self.set_layout(self.data_positions.copy())
        self.do_threshhold()
        #self.svg.empty()
        self.draw()

    def trim_click(self, b=None):
        "Trim button click: delete nodes without outgoing edges."
        #print "trim"
        self.info_area.value = "trim clicked"
        G = self.display_graph
        if G is None:
            self.info_area.value = "Cannot trim: no graph loaded."
            return
        self.display_graph = dGraph.trim_leaves(G)
        self.set_node_weights()
        #self.svg.empty()
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
            self.info_area.value = name + pprint.pformat(info)
            split = name.split("_")
            L = []
            if len(split) == 2:
                [indicator, data] = split
                if indicator == "NODE":
                    L.append(self.node_detail(data))
                    self.close_dialog()
                elif indicator == "EDGE":
                    e = json.loads(data)
                    L.append(self.edge_detail(e))
                    if not (self.selecting or self.moving_node or self.moving_label):
                        self.edge_dialog(e, info)
                else:
                    L.append("name " + repr(name))
                if indicator != "EDGE":
                    self.check_dialog()
            self.info_area.value = "\n".join(L)

    def check_dialog(self):
        dt = self.dialog_time
        if dt is not None:
            elapsed = time.time() - dt
            if elapsed > self.dialog_timeout:
                self.close_dialog()

    def close_dialog(self):
        self.dialog_time = None
        d = self.dialog
        elt = d.element()
        # set the focus to the parent of the dialog
        d(elt.parent().focus())
        d(elt.dialog("close"))
        d.flush()

    def edge_dialog(self, edge, info):
        # Only show the dialog if a motif collection is attached to the network.
        if self.motif_collection is None:
            return
        #self.motifs_button.visible = True
        set_visibility(self.motifs_button, True)
        if not self.motifs_button.value:
            return
        edge = tuple(edge)
        dg = self.data_graph
        atts = dg.edge_attributes.get(edge)
        motif_displays = []
        if atts is None:
            html = "No such edge? " + repr(edge)
        else:
            R = atts.get("Regulator", edge[0])
            T = atts.get("Target", edge[1])
            html = "%s -> %s" % (R, T)
            motifs = comma_separated(atts.get("Motifs", ""))
            if not motifs:
                html += "<br> no motifs."
            else:
                mc = self.motif_collection
                if not mc:
                    html += "<br> motifs=" + repr(motifs)
                else:
                    for motif_name in motifs:
                        # drop the suffix, like "_hg19"
                        motif_prefix = motif_name.rsplit("_", 1)[0]
                        motif_data = mc.get(motif_prefix)
                        if motif_data is None:
                            html += "<br> not found " + repr(motif_prefix)
                        else:
                            motif_displays.append((motif_prefix, motif_data))
        d = self.dialog
        elt = d.element()
        x = info["pageX"] + 5
        y = info["pageY"] + 5
        d(elt.empty)
        d(elt.dialog("option", {"position": [x, y]}).
            html(html))
        d(elt.dialog("open"))
        d.flush()
        for (prefix, data) in motif_displays:
            names = prefix
            if data.names:
                names = " ".join(data.names)
            d(elt.append("<div> %s </div>" % names))
            data.add_canvas(d, elt, dwidth=12, dheight=14)
        self.dialog_time = time.time()

    def alert(self, message):
        "Use the dialog to present a javascript alert."
        d = self.dialog
        d(d.window().alert(message))
        d.flush()

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
        if self.moving_label:
            self.update_moving_label(info)
        self.check_dialog()

    def update_moving_label(self, info):
        moving_label = self.moving_label
        svgX = info["svgX"]
        svgY = info["svgY"]
        svg = self.svg
        overrides = self.label_position_overrides
        overrides[moving_label] = (svgX, svgY + 4)
        attributes = {"x": svgX, "y": svgY}
        name = self.label_name(moving_label)
        svg.change_element(name, attributes)
        svg.send_commands()

    def label_name(self, node):
        return "LABEL_" + node

    def update_moving_node(self, info):
        moving_node = self.moving_node
        svgX = info["svgX"]
        svgY = info["svgY"]
        svg = self.svg
        positions = self.display_positions
        dG = self.display_graph
        depth = self.depth_slider.value
        dG.move_descendants(svg, positions, moving_node, svgX, svgY, depth)

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
        # if the colorize checkbox is set then only do colorization
        if self.colorize_checkbox.value:
            name = info.get("name", "")
            if name:
                color = self.color_picker.color
                self.color_overrides[name] = str(color)
                # change the color of the object selected
                atts = {"stroke": color, "fill": color}
                self.svg.change_element(name, atts)
                svg.send_commands()
            # don't respond to any other behavior if colorizing.
            return
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
            if self.moving_node or self.moving_label:
                self.moving_node = None
                self.moving_label = None
                self.draw()
            elif name.startswith("NODE_"):
                # otherwords if it's a node, start moving it
                nodename = name[5:]
                self.moving_node = nodename
                self.display_graph.uncache()
            elif name.startswith("LABEL_"):
                nodename = name[6:]
                self.moving_label = nodename

    def cancel_selection(self):
        "Remove the circular selection area, if present."
        svg = self.svg
        if self.selection_id:
            svg.delete_names([self.selection_id])
        self.selection_id = self.select_start = self.select_end = None
        svg.send_commands()
        self.zoom_button.disabled = True
        self.selecting = False

    def set_node_weights(self, weights=None, colors=None):
        if weights is None:
            weights = self.override_node_weights
        else:
            self.override_node_weights = weights
        if colors is None:
            colors = self.override_node_colors
        else:
            self.override_node_colors = colors
        if weights is not None:
            nw = self.display_graph.node_weights
            for node in list(nw):
                nw[node] = weights.get(node, 0)
        #self.display_graph.reset_colorization()
        if colors is not None:
            self.display_graph.set_node_color_interpolator(colors)

    def reset_node_weights(self, weights=None, colors=None):
        self.override_node_weights = None
        self.override_node_colors = None
        #self.display_graph.reset_colorization()
        self.set_node_weights()

    def handle_bounding_box_change(self, att_name, old, new):
        "Adjust the svg view box to include the bounding box for the network."
        if new:
            svg = self.svg  # XXXXX ???? what about the canvas?
            h = new["height"]
            w = new["width"]
            x = new["x"]
            y = new["y"]
            hw = max(100, h, w) + 10
            svg.set_view_box(x - 5, y - 5, hw, hw)

    def handle_maximize_change(self, att_name, old, new):
        set_visibility(self.hideable_right, self.maximize)
        set_visibility(self.inputs, self.maximize)


def display_network(filename, N=None, threshhold=20.0, save_layout=True, show=True, size_limit=2000):
    from jp_gene_viz import dLayout
    assert os.path.exists(filename)
    print ("Reading network", filename)
    G = getData.read_network(filename)
    size = len(G.node_weights) + len(G.edge_weights)
    layoutpath = filename + ".layout.json"
    if os.path.exists(layoutpath):
        print ("Loading saved layout", layoutpath)
        layout = dLayout.load(layoutpath)
    else:
        print ("Computing layout")
        if size < size_limit:
            # Use the slow but prettier method
            layout = dLayout.group_layout(G)
        else:
            print ("Using fast layout because the network is large.")
            (layout, rectangles) = grid_forest.forest_layout(G)
            assert type(layout) is dict, type(layout)
        if save_layout:
            print ("Saving layout", layoutpath)
            dLayout.dump(layout, layoutpath)
    if N is None:
        N = NetworkDisplay()
    if threshhold:
        N.threshhold_slider.value = threshhold
    N.load_data(G, layout, draw=show)
    if size > size_limit:
        print("Omitting edges, using canvas, and fast layout default because the network is large")
        N.container_dropdown.value = CANVAS
        N.layout_dropdown.value = SPOKE
        N.limit_edges(size_limit)
    if show:
        N.show()
    return N

def comma_separated(s):
    no_whitespace = "".join(s.split())
    return filter(None, no_whitespace.split(","))
