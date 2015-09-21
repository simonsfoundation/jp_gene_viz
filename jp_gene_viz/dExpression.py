import HMap
import pprint
import ipywidgets as widgets
from IPython.display import display
from jp_svg_canvas import canvas
import traitlets

class ExpressionDisplay(traitlets.HasTraits):

    rows = traitlets.Any()

    def __init__(self, *args, **kwargs):
        super(ExpressionDisplay, self).__init__(*args, **kwargs)
        svg = self.svg = canvas.SVGCanvasWidget()
        svg.add_style("background-color", "cornsilk")
        svg.watch_event = "click mousemove"
        #svg.watch_event = "click"
        svg.default_event_callback = self.svg_callback
        #self.feedback = widgets.Text(value="")
        #self.feedback.width = "300px"
        self.text_assembly = self.make_text_displays()
        self.info_area = widgets.Textarea(description="status")
        self.assembly = widgets.VBox(children=[self.svg, #self.feedback, 
                                               self.text_assembly, self.info_area])
        self.dx = 10
        self.dy = 2
        self.data_heat_map = None
        self.display_heat_map = None
        self.row = self.col = None
        # Maybe not needed.
        #self.on_trait_change(self.rows_changed, "rows")
        self.drawing = False

    #def rows_changed(self, name, rows):
    #    print self, "rows_changed", rows
    #    return # TEMP
    #    self.select_rows()

    def load_data(self, heat_map, dx=10, dy=5):
        self.data_heat_map = heat_map
        # project to at most 200 rows and columns
        rows = heat_map.row_names[:200]
        cols = heat_map.col_names[:200]
        self.dx = dx
        self.dy = dy
        return self.display_data(rows, cols)

    def display_data(self, rows, cols):
        if rows is not None:
            self.rows = rows
        else:
            rows = self.rows
        heat_map = self.display_heat_map = self.data_heat_map.projection(rows, cols)
        heat_map.fit(self.svg, self.dx, self.dy)
        self.row = self.col = None
        self.svg.empty()
        return self.draw()

    def select_rows(self, rows=None):
        return self.display_data(rows, self.data_heat_map.col_names[:200])

    def column_weights(self):
        if self.col is None:
            return None
        return self.display_heat_map.column_weights(self.col)

    def make_text_displays(self):
        self.row_text = widgets.Text(description="row", value="")
        self.row_text.width = "150px"
        self.col_text = widgets.Text(description="col", value="")
        self.col_text.width = "150px"
        assembly = widgets.HBox(children=[self.row_text, self.col_text])
        return assembly

    def svg_callback(self, info):
        self.info_area.value = pprint.pformat(info)
        name = info.get("name", "")
        typ = info.get("type", "")
        svg = self.svg
        heat_map = self.display_heat_map
        if heat_map is None:
            return
        dx = self.dx
        dy = self.dy
        x = info["svgX"]
        y = info["svgY"]
        i = int(y/dy)
        j = int(x/dx)
        if i >= 0 and j >= 0 and i < heat_map.nrows and j < heat_map.ncols:
            r = heat_map.row_names[i]
            c = heat_map.col_names[j]
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
        heat_map.draw(svg, self.dx, self.dy)
        svg.send_commands()
        self.drawing = False

    def show(self):
        display(self.assembly)


def display_heat_map(filename, dexpr=None):
    from jp_gene_viz import getData
    H = HMap.HeatMap()
    (r, c, d) = getData.read_tsv(filename)
    H.set_data(r, c, d)
    if dexpr is None:
        dexpr = ExpressionDisplay()
    dexpr.load_data(H)
