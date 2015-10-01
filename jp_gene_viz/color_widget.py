
import color_scale
import ipywidgets as widgets
from IPython.display import display
from jp_svg_canvas import canvas
import traitlets

# call once
from jp_svg_canvas.canvas import load_javascript_support


class ColorChooser(traitlets.HasTraits):

    margin = 15
    bar_region = 20
    histogram_region = 40
    dx = dy = 16
    ncolors = 8
    palette_side = dx * ncolors
    bar_height = 10

    def __init__(self, *args, **kwargs):
        super(ColorChooser, self).__init__(*args, **kwargs)
        svg = self.svg = canvas.SVGCanvasWidget()
        svg.width = self.margin * 2 + self.palette_side
        middle = self.palette_side + self.histogram_region + self.bar_region
        svg.height = self.margin * 2 + middle
        svg.set_view_box(- self.margin,
                         - self.margin,
                         self.palette_side + 2 * self.margin,
                         middle + 2 * self.margin)
        self.scale = color_scale.ColorInterpolator()
        svg.watch_event = "click mousemove"
        svg.default_event_callback = self.svg_callback
        self.drag_color = None
        self.drag_circle = None

    def svg_callback(self, info):
        name = info.get("name", "")
        typ = info.get("type")
        x = info.get("svgX")
        y = info.get("svgY")
        drag_circle = self.drag_circle
        drag_color = self.drag_color
        svg = self.svg
        if typ == "click":
            if name.startswith("R"):
                self.cancel_drag()
                dcolor = self.drag_color = name[1:]
                cname = self.drag_circle = "drag" + dcolor
                self.add_circle(cname, x, y, dcolor)
                svg.send_commands()
            else:
                bary_start = self.palette_side
                bary_end = bary_start + self.bar_region
                if y > bary_start and y < bary_end:
                    # click on the interpolation bar
                    xvalue = self.interpolation_value(x)
                    if drag_circle is not None:
                        drag_clr = color_scale.color2clr(drag_color)
                        self.scale.add_color(xvalue, drag_clr)
                        self.cancel_drag()
                        self.draw()
                else:
                    self.cancel_drag()
        elif typ == "mousemove":
            if drag_circle is not None:
                atts = {"cx": x, "cy": y}
                svg.change_element(drag_circle, atts)
                svg.send_commands()

    def cancel_drag(self):
        drag_circle = self.drag_circle
        if drag_circle is not None:
            svg = self.svg
            self.drag_circle = self.drag_color = None
            svg.delete_names([drag_circle])
            svg.send_commands()

    def show(self):
        display(self.svg)
        self.draw()

    def interpolation_value(self, x):
        normalized = float(x) / self.palette_side
        return self.scale.denormalized_value(normalized)

    def draw(self):
        svg = self.svg
        svg.empty()
        for i in xrange(self.ncolors):
            for j in xrange(self.ncolors):
                color = color_scale.color(color_scale.color64(i, j))
                svg.rect("R" + color, i * self.dx, j * self.dy, self.dx, self.dy, color)
        bary = self.palette_side + self.bar_region / 2 - self.bar_height / 2
        for i in xrange(self.palette_side):
            color_value = self.interpolation_value(i)
            color = self.scale.interpolate_color(color_value)
            svg.rect("V" + color, i, bary, 1, self.bar_height, color)
        circley = self.palette_side + self.bar_region / 2
        #circler = self.bar_height/2 + 2
        m = self.scale.minvalue
        M = self.scale.maxvalue
        for (value, clr) in self.scale.breakpoints:
            color = color_scale.color(clr)
            circlex = (value - m)/(M - m) * self.palette_side
            #svg.circle("breakpoint_" + color, circlex, circley, circler, color)
            name = "breakpoint_" + color
            self.add_circle(name, circlex, circley, color)
        svg.send_commands()

    def add_circle(self, name, circlex, circley, color):
        svg = self.svg
        circler = self.bar_height/2 + 2
        svg.circle(name, circlex, circley, circler, color, stroke="white", stroke_width=2)
