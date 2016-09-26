"""
A substitute for jp_svg_canvas.canvas.SVGCanvasWidget
which supports draw and re-draw operations
on an HTML5 canvas representation of SVGCanvasWidget.
It is intended that this substitute can present larger
visualizations with better performance than SVGCanvasWidget can.
"""

from jp_gene_viz import js_proxy
import traitlets
import math
import json

# this loads the proxy widget javascript "view" implementation
js_proxy.load_javascript_support()

# XXXX Very similar to jp_svg_canvas.fake_svg...

ASSIGN = 'A'
CALL = 'C'
PI2 = 6.29
SIDE_DEFAULT = 500.0

class HTML5CanvasProxy(traitlets.HasTraits):

    # Canvas width
    svg_width = traitlets.Float(SIDE_DEFAULT, sync=True)
    
    # Canvas height
    svg_height = traitlets.Float(SIDE_DEFAULT, sync=True)

    def __init__(self, viewBox="0 0 500 500", dimension=SIDE_DEFAULT, *pargs, **kwargs):
        super(HTML5CanvasProxy, self).__init__(*pargs, **kwargs)
        self.viewBox = viewBox
        self.svg_width = dimension
        self.svg_height = dimension
        self.on_trait_change(self.change_dimensions, "svg_width")
        self.on_trait_change(self.change_dimensions, "svg_height")
        self.font = "Arial"  # default
        self.font_size = 10
        self.font_weight = "normal"
        self.operations = []
        self.assignments = {}
        w = self.widget = js_proxy.ProxyWidget()
        self.element = w.element()
        self.empty()

    def set_view_box(self, x, y, w, h):
        #p "viewbox", (x,y,w,h)
        self.viewBox = "%s %s %s %s" % (x, y, w, h)

    def change_dimensions(self):
        # XXXX this clears the canvas for now!
        self.empty()

    def empty(self):
        self.operations = []
        self.assignments = {}
        w = self.widget
        elt = self.element
        w(elt.empty())
        w(elt.width(self.svg_width).height(self.svg_height))
        w.flush()
        self.is_empty = True

    def fit(self, *args):
        pass  # ???

    def _add(self, command, *args):
        self.operations.append(self.call_cmd(command, *args))

    def call_cmd(self, command, *args):
        return [CALL, command, list(args)]

    def _assign(self, lhs, rhs):
        assn = self.assignments
        if assn.get(lhs) == rhs:
            # duplicate assignment, skip
            return
        assn[lhs] = rhs
        self.operations.append(self.assignment_cmd(lhs, rhs))

    def assignment_cmd(self, lhs, rhs):
        return [ASSIGN, lhs, rhs]

    def send_commands(self):
        w = self.widget
        elt = self.element
        command_prefix = []
        if self.is_empty:
            # Initialize the canvas
            [x0, y0, width, height] = map(float, self.viewBox.split())
            #dimension = self.dimension
            minside = min(width, height)
            wscale = self.svg_width * 1.0/minside
            swidth = wscale * width
            hscale = self.svg_height * 1.0/minside
            sheight = hscale * height
            window = w.window()
            jQuery = window.jQuery
            tag = '<canvas width="%s" height="%s" style="border:1px solid #d3d3d3;"/>' % (
                swidth, sheight
            )
            #p "tag is", (tag, self.svg_width, self.svg_height, self.viewBox)
            w(elt._set("canvas", jQuery(tag).appendTo(elt)))
            w.save_function("context_execute",
                ["context", "sequence_json"],
                """ debugger;
                var sequence = JSON.parse(sequence_json);
                for (var i=0; i < sequence.length; i++) {
                    var command = sequence[i];
                    var indicator = command[0];
                    if (indicator == "%s") {
                        var method_name = command[1];
                        var args = command[2];
                        var method = context[method_name];
                        method.apply(context, args)
                    } else if (indicator == "%s") {
                        var slot_name = command[1];
                        var value = command[2];
                        context[slot_name] = value;
                    } else {
                        console.warn("bad indicator " + indicator);
                    }
                }
                """ % (CALL, ASSIGN))
            command_prefix.append(self.call_cmd("scale", wscale, hscale))
            command_prefix.append(self.call_cmd("translate", -x0, -y0))
        self.is_empty = False
        all_commands = command_prefix + self.operations
        #p "encoding JSON", len(all_commands)
        all_commands_json = json.dumps(all_commands)
        #p "encoded", len(all_commands_json)
        w(elt.context_execute(elt.canvas._get(0).getContext("2d"), all_commands_json))
        w.flush()

    def rect(self, name, x, y, width, height, fill="black", event_cb=None, style_dict=None,
            **other_attributes):
        if not style_dict:
            style_dict = {}
        self._add("beginPath")
        self._assign("fillStyle", fill)
        self._add("rect", x, y, width, height)
        self._add("fill")

    def circle(self, name, cx, cy, r, fill="black", event_cb=None, style_dict=None,
              **other_attributes):
        if not style_dict:
            style_dict = {}
        self._add("beginPath")
        self._assign("fillStyle", fill)
        self._add("arc", cx, cy, r, 0, PI2)
        self._add("fill")
  
    def text(self, name, x, y, text, fill="black", event_cb= None, style_dict=None, **other_attributes):
        if not style_dict:
            style_dict = {}
        style_dict = style_dict.copy()
        style_dict.update(other_attributes)
        f = self.font = style_dict.get("font", self.font)
        w = self.font_weight = style_dict.get("font-weight", self.font_weight)
        s = self.font_size = style_dict.get("font-size", self.font_size)
        self._assign("font", "%s %spx %s" % (w, s, f))
        self._assign("fillStyle", fill)
        ta = style_dict.get("text-anchor", "start")
        if ta == "middle":
            ta = "center"
        self._assign("textAlign", ta)
        self._add("fillText", text, x, y)
        stroke = style_dict.get("stroke")
        stroke_width = style_dict.get("stroke-width")
        if stroke and stroke_width:
            self._assign("lineWidth", stroke_width)
            self._assign("strokeStyle", stroke)
            self._add("strokeText", text, x, y)

    def line(self, name, x1, y1, x2, y2, color="black", width=1, 
             event_cb=None, style_dict=None, **other_attributes):
        if not style_dict:
            style_dict = {}
        self._add("beginPath")
        self._assign("strokeStyle", color)
        self._assign("lineWidth", width)
        self._add("moveTo", x1, y1)
        self._add("lineTo", x2, y2)
        self._add("stroke")

