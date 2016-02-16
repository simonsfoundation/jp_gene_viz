"""
Experimental tool for creating a graph diagram
"""

import os
import copy

from jp_gene_viz import js_proxy
from jp_gene_viz import js_context
#from jp_gene_viz.json_mixin import JsonMixin
import traitlets
import pprint

import ipywidgets as widgets
from IPython.display import display

js_context.load_if_not_loaded(["cytoscape.js"])
js_proxy.load_javascript_support()


class GraphDiagramWidget(traitlets.HasTraits):

    #json_atts = []

    #json_objects = []

    filename = traitlets.Unicode("", sync=True)

    widget = None

    def __init__(self, addenda, key, default_key=None, *pargs, **kwargs):
        super(GraphDiagramWidget, self).__init__(*pargs, **kwargs)
        self.addenda = addenda
        self.key = key
        self.default_key = default_key
        self.history = []
        self.count = 0
        self.selected_edge = None
        self.selected_node = None
        self.label_id = None
        w = self.configure_widget()
        lt = self.label_text = widgets.Text(value="")
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
        dl.width = "50px"
        n.width = "50px"
        n.on_click(self.new_click)
        ly.on_click(self.layout_click)
        info = self.info_area = widgets.Textarea(description="status")
        info.visible = False
        top = widgets.HBox(children=[n, lt, ly, dl, sn, sv, rv])
        hideable = widgets.VBox(children=[top, w, info])
        hcb = widgets.Checkbox(description="view", value=True)
        traitlets.link((hcb, "value"), (hideable, "visible"))
        a = self.assembly = widgets.VBox(children=[hcb, hideable])
        # make the assembly big enough
        hideable.height = 650
        # restore from addenda if archived
        addenda.reset(self, key, default_key)

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

    def to_json_value(self):
        w = self.widget
        cy = self.cy
        # dump the data from the viaualization
        json_value = w.evaluate(cy.json(), level=5)
        json_value["count"] = self.count
        return json_value

    def from_json_value(self, json_value):
        self.count = json_value.get("count", 100)
        self.configure_widget(self.widget, layout="cose", descriptor=json_value)

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

