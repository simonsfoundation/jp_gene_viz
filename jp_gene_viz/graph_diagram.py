"""
Experimental tool for creating a graph diagram
"""

import os

from jp_gene_viz import js_proxy
from jp_gene_viz import js_context
from jp_gene_viz.json_mixin import JsonMixin
import traitlets
import pprint

import ipywidgets as widgets
from IPython.display import display

js_context.load_if_not_loaded(["cytoscape.js"])
js_proxy.load_javascript_support()


class GraphDiagramWidget(traitlets.HasTraits, JsonMixin):

    json_atts = []

    json_objects = []

    filename = traitlets.Unicode("", sync=True)

    widget = None

    def __init__(self, filename, *pargs, **kwargs):
        super(GraphDiagramWidget, self).__init__(*pargs, **kwargs)
        self.filename = filename
        self.history = []
        self.count = 0
        self.selected_edge = None
        self.selected_node = None
        self.label_id = None
        w = self.configure_widget()
        lt = self.label_text = widgets.Text(value="")
        lt.on_trait_change(self.label_change, "value")
        n = self.new_button = widgets.Button(description="*")
        ly = self.layout_button = widgets.Button(description="layout")
        dl = self.delete_button = widgets.Button(description="X")
        dl.on_click(self.delete_click)
        dl.width = "50px"
        n.width = "50px"
        n.on_click(self.new_click)
        ly.on_click(self.layout_click)
        info = self.info_area = widgets.Textarea(description="status")
        top = widgets.HBox(children=[n, lt, ly, dl])
        a = self.assembly = widgets.VBox(children=[top, w, info])
        # make the assembly big enough
        a.height = 650

    def show(self):
        display(self.assembly)
        self.widget.flush()

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

    def delete_click(self, b):
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

    def new_click(self, b):
        # create a new node
        self.info_area.value = "new click " + str(self.count)
        selected = self.selected_node
        D = {}
        D["group"] = "nodes"
        data = {}
        self.count += 1
        data["id"] = self.label_id = str(self.count)
        data["label"] = ""
        self.label_text.value = ""
        if selected:
            data["parent"] = selected
        D["data"] = data
        return self.add(D)

    def add(self, D):
        w = self.widget
        cy = self.cy
        w(cy.add(D))
        return self.layout_click(None)

    def add_edge(self, source, target):
        D = {}
        D["group"] = "edges"
        self.count += 1
        data = {}
        data["id"] = self.label_id = str(self.count)
        data["label"] = ""
        data["source"] = source
        data["target"] = target
        self.label_text.value = ""
        D["data"] = data
        return self.add(D)

    def layout_click(self, b):
        w = self.widget
        cy = self.cy
        w(cy.layout())
        w.flush()

    def configure_widget(self):
        if self.widget is None:
            self.widget = js_proxy.ProxyWidget()
        w = self.widget
        element = w.element()
        w(element.empty())
        # set up an event callback helper
        w.save_function("event_cb", ["callback"], """
            debugger;
            return function(evt) {
                debugger;
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
                   height(600).
                   width(800).
                   #html("cytoscape target div").
                   appendTo(element)
                  ))
        #nodes = [{"data": {"id": "n", "label": "cytoscape"}}]
        nodes = []
        edges = []
        elements = {"nodes": nodes, "edges": edges}
        descriptor = {
            "container": element.target._get(0),
            "style": STYLE,
            "elements": elements,
            "layout": {"name": "cose", "padding": 5}
        }
        w(element._set("cy", cytoscape(descriptor)))
        w(element.height(900).width(800))
        self.cy = cy = element.cy
        clickcallback = element.event_cb(w.callback(self.clickhandler, data="click", level=3))
        self.getter = cy._get("$")
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

    def to_json_value(self):
        result = {}
        result["history"] = [item.to_json_value() for item in self.history]
        result["count"] = self.count
        return result

    def from_json_value(self, json_value):
        self.history = json_value.get("history", [])
        self.count = json_value.get("count", 0)

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
        'color': 'white',
        'text-outline-width': 2,
        'text-outline-color': '#888',
            "background-color": "cyan"
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
        'text-halign': 'left',
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
        'source-arrow-color': 'black'
      }
    }]

