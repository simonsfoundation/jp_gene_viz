"""
Experimental tool for creating a graph diagram
"""

import os
import copy
import time

from jp_gene_viz import js_proxy
from jp_gene_viz import js_context
#from jp_gene_viz.json_mixin import JsonMixin
import traitlets
import pprint

import ipywidgets as widgets
from IPython.display import display
from jp_gene_viz import color_widget


def initialize():
    js_context.load_if_not_loaded(["cytoscape.js"])
    js_proxy.load_javascript_support()
    color_widget.load_javascript_support()


class GraphDiagramWidget(traitlets.HasTraits):

    #json_atts = []

    #json_objects = []

    filename = traitlets.Unicode("", sync=True)

    widget = None

    def __init__(self, addenda, key, default_key=None, *pargs, **kwargs):
        super(GraphDiagramWidget, self).__init__(*pargs, **kwargs)
        initialize()
        self.addenda = addenda
        self.key = key
        self.default_key = default_key
        self.history = []
        self.count = 0
        self.selected_edge = None
        self.selected_node = None
        self.label_id = None
        w = self.configure_widget()
        lt = self.label_text = widgets.Text(value="", width="200px")
        lt.layout.width = "200px"
        lt.on_trait_change(self.label_change, "value")
        n = self.new_button = widgets.Button(description="O")
        ly = self.layout_button = widgets.Button(description="layout")
        dl = self.delete_button = widgets.Button(description="X")
        sv = self.save_button = widgets.Button(description="save")
        rv = self.revert_button = widgets.Button(description="revert")
        sn = self.snap_button = widgets.Button(description="snap")
        sv.on_click(self.save_click)
        rv.on_click(self.revert_click)
        sn.on_click(self.snap_click)
        dl.on_click(self.delete_click)
        dl.layout.width = "50px"
        n.layout.width = "50px"
        n.on_click(self.new_click)
        ly.on_click(self.layout_click)
        info = self.info_area = widgets.Textarea(description="status")
        info.visible = False
        # node details
        ns = self.node_shape = widgets.Dropdown(description="shape", options=SHAPES, value="ellipse")
        ns.layout.width = "100px"
        #nbc = self.node_background_color = widgets.Text(description="color", width="200px")
        nbc_html = widgets.HTML("node color")
        nbc = self.node_background_color = color_widget.ColorPicker()
        nbc.draw()
        nbi = self.node_background_image = widgets.Text(description="image", width="200px")
        nbi.layout.width = "200px"
        # label details
        #lbc = self.label_color = widgets.Text(description="label color", width="200px")
        lbc_html = widgets.HTML("label color")
        lbc = self.label_color = color_widget.ColorPicker()
        lbc.draw()
        lfs = self.label_font_size = widgets.IntSlider(description="font size",
            value=0, min=0, max=50, width="50px")
        lfs.layout.width = "150px"
        lal = self.label_align = widgets.Dropdown(description="align",
            options=["", "top", "center", "bottom"], value="center")
        lal.layout.width = "150px"
        # edge details
        #edc = self.edge_color = widgets.Text(description="edge color", width="200px")
        edc_html = widgets.HTML("edge color")
        edc = self.edge_color = color_widget.ColorPicker()
        edc.draw()
        eds = self.edge_style = widgets.Dropdown(description="edge style",
            options=["", "solid", "dotted", "dashed"], value="solid")
        eds.width = "150px"
        # detail control buttons
        applyb = self.apply_button = widgets.Button(description="apply")
        resetb = self.reset_button = widgets.Button(description="reset")
        resetb.on_click(self.reset_inputs)
        applyb.on_click(self.apply_click)
        # scaffolding
        dcb = self.details_checkbox = widgets.Checkbox(description="details", value=False)
        top = widgets.HBox(children=[n, lt, ly, dl, sn, sv, rv, dcb])
        dlabel = widgets.VBox(children=[lbc_html, lbc.svg, lfs, lal])
        dnode = widgets.VBox(children=[ns, nbc_html, nbc.svg, nbi])
        dedge = widgets.VBox(children=[edc_html, edc.svg, eds])
        detail = widgets.VBox(children=[dlabel, dnode, dedge, applyb, resetb])
        detail.layout.visibility = "hidden"
        self.detail = detail
        #traitlets.link((detail, "visible"), (dcb, "value"))
        self.visibility_link(dcb, detail)
        middle = widgets.HBox(children=[w, detail])
        hideable = widgets.VBox(children=[top, middle, info])
        self.view_checkbox = vcb = widgets.Checkbox(description="view", value=True)
        #traitlets.link((vcb, "value"), (hideable, "visible"))
        self.visibility_link(vcb, hideable)
        a = self.assembly = widgets.VBox(children=[vcb, hideable])
        # make the assembly big enough
        hideable.height = 650
        # restore from addenda if archived
        #addenda.reset(self, key, default_key)

    def visibility_link(self, checkbox, toggle_component):
        def checkbox_change(name, old, new):
            if checkbox.value:
                toggle_component.layout.visibility = "visible"
            else:
                toggle_component.layout.visibility = "hidden"
        checkbox.on_trait_change(checkbox_change, "value")

    def reset_inputs(self, b=None):
        self.edge_style.value = ""
        self.edge_color.color = ""
        self.label_font_size.value = 0
        # Don't reset the label text
        #self.label_text.value = ""
        self.node_shape.value = ""
        self.node_background_color.color = ""
        self.node_background_image.value = ""
        self.label_color.color = ""
        self.label_align.value = ""

    def apply_click(self, b=None):
        self.info_area.value = "apply click"
        identifier = self.label_id
        if identifier is None:
            self.info_area.value = "nothing selected to apply " + repr((old, new))
            return
        return self.apply_details(identifier)

    def apply_details(self, identifier):
        # really should only apply pertinent styles to edges, nodes
        style = {}
        if self.label_align.value:
            style["text-valign"] = self.label_align.value
        if self.label_color.color:
            style["color"] = self.label_color.color
        if self.node_background_image.value:
            style["background-image"] = self.node_background_image.value
        if self.node_background_color.color:
            style["background-color"] = self.node_background_color.color
        if self.node_shape.value:
            style["shape"] = self.node_shape.value
        if self.label_font_size.value:
            style["font-size"] = self.label_font_size.value
        if self.edge_color.color:
            color = self.edge_color.color
            style["line-color"] = color
            style["target-arrow-color"] = color
        if self.edge_style.value:
            style["line-style"] = self.edge_style.value
        if style:
            selector = "#" + str(identifier)
            return self.set_style(selector, style)
        else:
            self.info_area.value = "No style options to apply"

    def set_style(self, selector, style):
        w = self.widget
        cy = self.cy
        w(cy.style().selector(selector).css(style).update())
        w.flush()

    def show(self):
        display(self.assembly)
        self.revert_click(None)

    def label_change(self, att_name, old, new):
        # change the label of the currently selected object.
        self.info_area.value = "label change " + repr((old, new))
        identifier = self.label_id
        if identifier is None:
            self.info_area.value = "nothing selected to label " + repr((old, new))
            return
        w = self.widget
        cy = self.cy
        getter = self.getter
        selector = "#" + identifier
        selected = getter(selector)
        w(selected.data("label", new))
        w.flush()

    def to_json_value(self):
        w = self.widget
        cy = self.cy
        # dump the data from the viaualization
        json_value = w.evaluate(cy.json(), level=5)
        json_value["count"] = self.count
        json_value["layout"] = {
            "name": "preset", 
            "padding": 5
        }
        return json_value

    def from_json_value(self, json_value):
        self.count = json_value.get("count", 100)
        self.configure_widget(self.widget, layout="preset", descriptor=json_value)

    def save_click(self, b=None):
        addenda = self.addenda
        addenda.set(self.key, self)
        addenda.save()
        self.info_alert("saved " + self.addenda.path)

    def info_alert(self, message):
        self.label_id = None
        self.label_text.value = message

    def revert_click(self, b=None):
        addenda = self.addenda
        addenda.reset(self, self.key, self.default_key)
        self.widget.flush()
        self.info_alert("reverted")

    def snap_click(self, b=None):
        w = self.widget
        cy = self.cy
        json = self.to_json_value()
        snap = js_proxy.ProxyWidget()
        self.configure_widget(snap, layout="preset", descriptor=json)
        snap.embed(True, await=["cytoscape"])

    def delete_click(self, b=None):
        self.info_area.value = "delete " + str(self.label_id)
        identifier = self.label_id
        if identifier is None:
            self.info_area.value = "nothing selected to delete "
        w = self.widget
        cy = self.cy
        getter = self.getter
        selector = "#" + identifier
        selected = getter(selector)
        w(cy.remove(selected))
        w.flush()

    def new_click(self, b=None):
        # create a new node
        self.info_area.value = "new click " + str(self.count)
        selected = self.selected_node
        D = {}
        D["group"] = "nodes"
        data = {}
        self.count += 1
        identifier = data["id"] = self.label_id = str(self.count)
        data["label"] = ""
        self.label_text.value = ""
        if selected:
            data["parent"] = selected
        D["data"] = data
        return self.add(D, identifier)

    def add(self, D, identifier=None, layout=True):
        w = self.widget
        cy = self.cy
        w(cy.add(D))
        if identifier is not None:
            self.apply_details(identifier)
        if layout:
            self.layout_click(None)
        else:
            w(cy.forceRender())
            w.flush()

    def add_edge(self, source, target):
        D = {}
        D["group"] = "edges"
        self.count += 1
        data = {}
        identifier = data["id"] = self.label_id = str(self.count)
        data["label"] = ""
        data["source"] = source
        data["target"] = target
        self.label_text.value = ""
        D["data"] = data
        return self.add(D, identifier, layout=False)

    def link_labels(self, source_label, target_label):
        source = self.get_identity_by_label(source_label)
        target = self.get_identity_by_label(target_label)
        #source = "1"
        #target = "2"
        self.add_edge(source, target)

    def get_identity_by_label(self, label):
        selector = "[label='%s']" % label
        w = self.widget
        cy = self.cy
        identity = w.evaluate(cy["$"](selector).data()["id"])
        # hack for testing
        time.sleep(0.1)
        return identity

    def layout_click(self, b):
        w = self.widget
        cy = self.cy
        options = {
            "name": "cose", 
            "padding": 5
        }
        w(cy.layout(options))
        w.flush()

    def configure_widget(self, w=None, layout="cose", descriptor=None):
        if w is None:
            self.widget = js_proxy.ProxyWidget()
            w = self.widget
        element = w.element()
        w(element.empty())
        # set up an event callback helper
        w.save_function("event_cb", ["callback"], """
            //debugger;
            return function(evt) {
                //debugger;
                var cyTarget = evt.cyTarget;
                if (cyTarget && cyTarget.data) {
                    var result = evt.cyTarget.data();
                    if (result) {
                        result.type = evt.type;
                        result.shiftKey = evt.originalEvent.shiftKey;
                        result.isNode = cyTarget.isNode();
                        result.isEdge = cyTarget.isEdge();
                        return callback(result);
                    }
                }
                return callback({});
            }
        """)
        self.element = element = w.element()
        window = w.window()
        cytoscape = window.cytoscape
        jQuery = window.jQuery
        w(element._set("target", 
                   jQuery("<div></div>").
                   height("600px").
                   width("800px").
                   #html("cytoscape target div").
                   appendTo(element)
                  ))
        #nodes = [{"data": {"id": "n", "label": "cytoscape"}}]
        if descriptor is None:
            nodes = []
            edges = []
            elements = {"nodes": nodes, "edges": edges}
            descriptor = {
                "container": element.target._get(0),
                "style": STYLE,
                "elements": elements,
                "layout": {"name": layout, "padding": 5}
            }
        else:
            descriptor = copy.deepcopy(descriptor)
            descriptor["container"] = element.target._get(0)
            descriptor["layout"]["name"] = layout
        w(element._set("cy_container", cytoscape(descriptor)))
        w(element.height("600px").width("800px"))
        self.cy = cy = element.cy_container
        clickcallback = element.event_cb(w.callback(self.clickhandler, data="click", level=3))
        self.getter = cy._get("$")
        # only add events in live mode
        if w == self.widget:
            w(cy.on('click', clickcallback))
        return w

    def clickhandler(self, identifier, arguments):
        self.info_area.value = "click\n" + pprint.pformat(arguments)
        arg0 = arguments["0"]
        identity = arg0.get("id")
        isEdge = arg0.get("isEdge")
        isNode = arg0.get("isNode")
        label = arg0.get("label", "")
        parent = arg0.get("parent")
        shiftKey = arg0.get("shiftKey")
        source = arg0.get("source")
        target = arg0.get("target")
        typ = arg0.get("type")
        selected = self.selected_node
        if isNode:
            if shiftKey and selected:
                # add an edge
                self.add_edge(selected, identity)
            else:
                self.selected_node = identity
                self.label_id = identity
                self.label_text.value = label
                self.selected_edge = None
        elif isEdge:
            self.selected_node = None
            self.selected_edge = identity
            self.label_id = identity
            self.label_text.value = label
        else:
            self.selected_edge = None
            self.selected_node = None

    def save(self):
        f = open(self.filename, "w")
        f.write(self.as_json())
        f.close()

    def load(self):
        f = open(self.filename)
        json_str = f.read()
        self.load_json(json_str)

# cytoscape styling for nodes and edges and parent nodes.
STYLE = [
    {
      "selector": 'node',
      "css": {
        'content': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-wrap': 'wrap',
        'text-max-width': 80,
        'text-valign': 'center',
        'color': '#aaa',
        #'text-outline-width': 2,
        #'text-outline-color': '#888',
            "background-color": "cyan",
            "background-fit": "cover"
      }
    },
    {
      "selector": '$node > node',
      "css": {
        'padding-top': '10px',
        'padding-left': '10px',
        'padding-bottom': '10px',
        'padding-right': '10px',
        'text-valign': 'top',
        'text-halign': 'center',
        'background-color': '#bbb'
      }
    },
    {
      "selector": 'edge',
      "css": {
        'target-arrow-shape': 'triangle',
        #'source-arrow-shape': 'triangle',
        'content': 'data(label)',
        "line-color": "red",
        'target-arrow-color': 'red',
        'edge-text-rotation': 'autorotate',
      }
    },
    {
      "selector": ':selected',
      "css": {
        'background-color': 'black',
        'line-color': 'black',
        'target-arrow-color': 'black',
        'source-arrow-color': 'black',
        'background-blacken': 0.5,
      }
    }]

SHAPES = [""] + ("""
rectangle roundrectangle ellipse triangle pentagon hexagon 
heptagon octagon star diamond vee rhomboid""").split()
