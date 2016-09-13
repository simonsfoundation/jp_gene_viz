"""
A substitute for jp_svg_canvas.canvas.SVGCanvasWidget
which supports draw and re-draw operations
on an HTML5 canvas representation of SVGCanvasWidget.
It is intended that this substitute can present larger
visualizations with better performance than SVGCanvasWidget can.
"""

from jp_gene_viz import js_proxy
import math
# this loads the proxy widget javascript "view" implementation
js_proxy.load_javascript_support()

# XXXX Very similar to jp_svg_canvas.fake_svg...

ASSIGN = 'A'
CALL = 'C'
PI2 = 6.29

class HTML5CanvasProxy(object):

    def __init__(self, viewBox, dimension=800.0):
        self.viewBox = viewBox
        self.dimension = dimension
        self.font = "Arial"  # default
        self.font_size = 10
        self.operations = []
        self.assignments = {}
        w = self.widget = js_proxy.ProxyWidget()
        self.element = w.element()
        self.empty()

    def empty(self):
        self.operations = []
        self.assignments = {}
        self.element.empty()
        self.is_empty = True

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
            dimension = self.dimension
            minside = min(width, height)
            scale = dimension * 1.0/minside
            swidth = scale * width
            sheight = scale * height
            window = w.window()
            jQuery = window.jQuery
            tag = '<canvas width="%s" height="%s" style="border:1px solid #d3d3d3;"/>' % (
                swidth, sheight
            )
            w(elt._set("canvas", jQuery(tag).appendTo(elt)))
            w.save_function("context_execute",
                ["context", "sequence"],
                """ debugger;
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
            command_prefix.append(self.call_cmd("scale", scale, scale))
            command_prefix.append(self.call_cmd("translate", -x0, -y0))
        self.is_empty = False
        all_commands = command_prefix + self.operations
        w(elt.context_execute(elt.canvas._get(0).getContext("2d"), all_commands))
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
        s = self.font_size = style_dict.get("font-size", self.font_size)
        self._assign("fillStyle", fill)
        self._assign("font", "%spx %s" % (s, f))
        self._assign("fillStyle", fill)
        ta = style_dict.get("text-anchor", "start")
        if ta == "middle":
            ta = "center"
        self._assign("textAlign", ta)
        self._add("fillText", text, x, y)

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

