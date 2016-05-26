import HMap
import pprint
import ipywidgets as widgets
from IPython.display import display
from jp_svg_canvas import canvas
from jp_gene_viz.widget_utils import set_visibility, is_visible
import traitlets
import fnmatch
import color_scale
import color_widget


class ExpressionDisplay(traitlets.HasTraits):

    labels_space = traitlets.Any(100, sync=True)

    rows = traitlets.Any()

    def __init__(self, *args, **kwargs):
        super(ExpressionDisplay, self).__init__(*args, **kwargs)
        svg = self.svg = canvas.SVGCanvasWidget()
        svg.add_style("background-color", "cornsilk")
        svg.svg_width = 550
        svg.svg_height = 550
        svg.watch_event = "click mousemove"
        svg.default_event_callback = self.svg_callback
        cc = self.color_chooser = color_widget.ColorChooser()
        #cc.svg.visible = False   # default
        set_visibility(cc.svg, False)

        self.text_assembly = self.make_text_displays()
        self.match_assembly = self.make_match_assembly()
        self.info_area = widgets.Textarea(description="status")
        self.assembly = widgets.VBox(children=[self.text_assembly,
                                               self.svg,
                                               self.color_chooser.svg,
                                               self.match_assembly,
                                               self.info_area])
        self.dx = 10
        self.dy = 2
        self.data_heat_map = None
        self.display_heat_map = None
        self.row = self.col = None
        self.drawing = False

    def load_data(self, heat_map, side_length):
        self.data_heat_map = heat_map
        # project to at most 200 rows and columns
        rows = heat_map.row_names[:200]
        cols = heat_map.col_names[:200]
        self.side_length = side_length
        self.display_data(rows, cols, side_length)

    def display_data(self, rows, cols, side_length=None):
        if side_length is None:
            side_length = self.side_length
        if rows is not None:
            self.rows = rows
        else:
            rows = self.rows
        heat_map = self.display_heat_map = self.data_heat_map.projection(rows, cols)
        (self.dx, self.dy) = heat_map.fit(self.svg, side_length, self.labels_space)
        self.row = self.col = None
        self.svg.empty()
        return self.draw()

    def select_rows(self, rows=None):
        return self.display_data(rows, self.data_heat_map.col_names[:200])

    def column_weights(self):
        if self.col is None:
            return None
        return self.data_heat_map.column_weights(self.col)

    def make_text_displays(self):
        self.row_text = widgets.Text(description="row", value="")
        self.row_text.layout.width = "100px"
        self.col_text = widgets.Text(description="col", value="")
        self.col_text.layout.width = "100px"
        sslider = self.size_slider = widgets.FloatSlider(value=550, min=550, max=3000,
            step=10, readout=False, width="100px")
        sslider.layout.width = "150px"
        svg = self.svg
        traitlets.directional_link((sslider, "value"), (svg, "svg_width"))
        traitlets.directional_link((sslider, "value"), (svg, "svg_height"))
        assembly = widgets.HBox(children=[self.row_text, self.col_text, sslider])
        return assembly

    def make_match_assembly(self):
        b = self.match_button = widgets.Button(description="match", width="50px")
        b.layout.width = "50px"
        b.on_click(self.match_click)
        t = self.match_text = widgets.Text(width="300px")
        t.layout.width = "300px"
        d = self.draw_button = widgets.Button(description="draw", width="50px")
        d.layout.width = "50px"
        d.on_click(self.draw_click)
        c = self.color_checkbox = widgets.Checkbox(description="colors", value=False)
        c.on_trait_change(self.colors_click, "value")
        assembly = widgets.HBox(children=[b, t, d, c])
        return assembly

    def colors_click(self, b):
        #self.color_chooser.svg.visible = self.color_checkbox.value
        set_visibility(self.color_chooser.svg, self.color_checkbox.value)
        self.draw()

    def draw_click(self, b):
        self.draw()

    def match_click(self, b):
        patterns = self.match_text.value.split()
        column_set = set()
        columns = self.data_heat_map.col_names
        for pattern in patterns:
            column_set.update(fnmatch.filter(columns, pattern))
        if not column_set:
            self.info_area.value = "No columns selected."
        else:
            columns = sorted(column_set)[:200]
            rows = self.display_heat_map.row_names
            self.display_data(rows, columns)

    def svg_callback(self, info):
        self.info_area.value = pprint.pformat(info)
        name = info.get("name", "")
        typ = info.get("type", "")
        svg = self.svg
        heat_map = self.display_heat_map
        if heat_map is None:
            return
        dx = self.dx
        if not dx:
            dx = 1
        dy = self.dy
        if not dy:
            dy = 1
        x = info["svgX"]
        y = info["svgY"]
        i = int(y/dy)
        j = int(x/dx)
        if i >= 0 and j >= 0 and i < heat_map.nrows and j < heat_map.ncols:
            try:
                r = heat_map.row_names[i]
                c = heat_map.col_names[j]
            except IndexError:
                pass  # XXXX Shouldn't happen, but does.
            else:
                intensity = heat_map.data[i, j]
                self.info_area.value = "%s :: %s, %s -> %s" % (name, r, c, intensity)
                if typ == "click":
                    heat_map.unhighlight(svg)
                    heat_map.highlight(svg, i, j, dx, dy)
                    self.row = r
                    self.col = c
                    self.row_text.value = r
                    self.col_text.value = c

    def draw(self):
        if self.drawing:
            raise ValueError, "too many draws"
        self.drawing = True
        heat_map = self.display_heat_map
        if heat_map is None:
            return
        svg = self.svg
        svg.empty()
        heat_map.draw(svg, self.dx, self.dy, self.labels_space)
        cc = self.color_chooser
        if is_visible(cc.svg):
            self.info_area.value = "displaying color chooser."
            cc.scale = heat_map.get_color_interpolator()
            cc.count_values(heat_map.data.flatten())
            cc.draw()
        svg.send_commands()
        self.drawing = False

    def color_interpolator(self):
        return self.display_heat_map.get_color_interpolator()

    def show(self):
        display(self.assembly)


def display_heat_map(filename, dexpr=None, side_length=550):
    from jp_gene_viz import getData
    H = HMap.HeatMap()
    (r, c, d) = getData.read_tsv(filename)
    H.set_data(r, c, d)
    if dexpr is None:
        dexpr = ExpressionDisplay()
    dexpr.load_data(H, side_length=side_length)
