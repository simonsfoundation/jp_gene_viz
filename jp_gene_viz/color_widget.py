
from jp_gene_viz import color_scale
import ipywidgets as widgets
from IPython.display import display
from jp_svg_canvas import canvas
import traitlets

# call once
from jp_svg_canvas.canvas import load_javascript_support


class ColorMixin:

    ncolors = 8
    dx = dy = 16
    palette_side = dx * ncolors

    def draw_colors(self, svg):
        for i in range(self.ncolors):
            for j in range(self.ncolors):
                color = color_scale.color(color_scale.color64(i, j))
                svg.rect("R_" + color, i * self.dx, j * self.dy, self.dx, self.dy, color)


class ColorPicker(traitlets.HasTraits, ColorMixin):

    color = traitlets.Unicode("")

    def __init__(self, *args, **kwargs):
        super(ColorPicker, self).__init__(*args, **kwargs)
        svg = self.svg = canvas.SVGCanvasWidget()
        svg.svg_height = self.palette_side + 2 * self.dy
        svg.svg_width = self.palette_side
        svg.set_view_box(0, 0, svg.svg_width, svg.svg_height)
        svg.watch_event = "click"
        svg.default_event_callback = self.svg_callback
        #self.color = color_scale.color(color_scale.color64(0, 0))
        self.on_trait_change(self.show_color_choice, "color")

    def svg_callback(self, info):
        name = info.get("name", "")
        typ = info.get("type")
        if typ == "click":
            if name.startswith("R_"):
                color = name.split("_")[-1]
                self.unshow_color_choice(self.color)
                self.color = color
                self.show_color_choice()
                self.svg.send_commands()

    def draw(self):
        svg = self.svg
        svg.empty()
        self.draw_colors(svg)
        self.show_color_choice()
        #svg.send_commands()

    def show_color_choice(self):
        color = self.color
        #print "show color choice", color
        svg = self.svg
        marker = "color_choice"
        tmarker = "color_text"
        # display the color
        atts = {"stroke-width": 2, "stroke": "rgb(100,100,100)"}
        svg.delete_names([marker, tmarker])
        if color:
            choice = color
        else:
            choice = "no choice"
        if color:
            svg.rect(marker, 0, self.palette_side + self.dy, self.palette_side, self.dy, color, **atts)
        svg.text(tmarker, 0, self.palette_side + self.dy, choice, "black")
        # outline the chosen element of the palette
        if color:
            svg.change_element("R_" + color, atts)
        svg.send_commands()

    def unshow_color_choice(self, color):
        svg = self.svg
        atts = {"stroke-width": 0}
        svg.change_element("R_" + color, atts)

    def show(self):
        display(self.svg)
        self.draw()


class ColorChooser(traitlets.HasTraits, ColorMixin):
    """
    Interactive widget for choosing color interpolation.
    """

    margin = 15
    bar_region = 40
    histogram_region = 40
    dx = dy = 16
    ncolors = 8
    palette_side = dx * ncolors
    bar_height = 10
    title = "Colors"

    def __init__(self, *args, **kwargs):
        super(ColorChooser, self).__init__(*args, **kwargs)
        svg = self.svg = canvas.SVGCanvasWidget()
        svg.svg_width = self.margin * 2 + self.palette_side
        middle = self.palette_side + self.histogram_region + self.bar_region
        svg.svg_height = self.margin * 2 + middle
        svg.set_view_box(- self.margin,
                         - self.margin,
                         self.palette_side + 2 * self.margin,
                         middle + 2 * self.margin)
        self.scale = color_scale.ColorInterpolator(minvalue=-3.33323, maxvalue=1.3432)
        svg.watch_event = "click mousemove"
        svg.default_event_callback = self.svg_callback
        self.drag_color = None
        self.drag_circle = None
        self.histogram = None

    def count_values(self, values, reset=False):
        h = self.histogram
        if reset or h is None:
            h = self.histogram = {}
        for v in values:
            h[v] = h.get(v, 0) + 1

    def svg_callback(self, info):
        name = info.get("name", "")
        typ = info.get("type")
        x = info.get("svgX")
        y = info.get("svgY")
        drag_circle = self.drag_circle
        drag_color = self.drag_color
        svg = self.svg
        if typ == "click":
            if name.startswith("R_") or name.startswith("breakpoint_"):
                self.cancel_drag()
                (_, dcolor) = name.split("_")
                # remove the color from the scale and redraw
                dclr = color_scale.color2clr(dcolor)
                self.scale.remove_color(dclr)
                self.draw()
                self.drag_color = dcolor
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
                    #self.draw()
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

    def display_value(self, interpolation_x):
        normalized = self.scale.normalized_value(interpolation_x)
        return int(normalized * (self.palette_side - 1))

    def display_histogram(self):
        result = {}
        h = self.histogram
        if h is not None:
            for value in h:
                count = h[value]
                dvalue = self.display_value(value)
                result[dvalue] = result.get(dvalue, 0) + count
        return result

    def draw(self):
        svg = self.svg
        svg.empty()
        self.draw_colors(svg)
        #for i in range(self.ncolors):
        #    for j in range(self.ncolors):
        #        color = color_scale.color(color_scale.color64(i, j))
        #        svg.rect("R_" + color, i * self.dx, j * self.dy, self.dx, self.dy, color)
        bary = self.palette_side + self.bar_region / 2 - self.bar_height / 2
        dhistogram = self.display_histogram()
        maxcount = 1
        if dhistogram:
            maxcount = float(max(dhistogram.values()))
        for i in range(self.palette_side):
            color_value = self.interpolation_value(i)
            color = self.scale.interpolate_color(color_value)
            adjustment = (dhistogram.get(i, 0) / maxcount) * self.histogram_region
            #print i, adjustment
            svg.rect("V" + color,
                     i, bary,
                     1, adjustment + self.bar_height, color)
        circley = self.palette_side + self.bar_region / 2
        m = self.scale.minvalue
        M = self.scale.maxvalue
        for (value, clr) in self.scale.breakpoints:
            color = color_scale.color(clr)
            circlex = (value - m)/(M - m) * self.palette_side
            name = "breakpoint_" + color
            self.add_circle(name, circlex, circley, color)
        svg.text(None, 0, 0, self.title, "black")
        svg.text(None, 0, bary, "%3.1f" % m, "black")
        atts = {"text-anchor": "end"}
        svg.text(None, self.palette_side, bary, "%3.1f" % M, "black", **atts)
        if m < 0 and M > 0:
            zvalue = self.display_value(0)
            svg.text(None, zvalue, bary, "0", "black")
        svg.send_commands()

    def add_circle(self, name, circlex, circley, color):
        svg = self.svg
        circler = self.bar_height/2 + 2
        svg.circle(name, circlex, circley, circler, color, stroke="white", stroke_width=2)
