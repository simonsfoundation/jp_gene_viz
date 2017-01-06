from jp_gene_viz import HMap
import pprint
import ipywidgets as widgets
from IPython.display import display
from jp_svg_canvas import canvas
from jp_gene_viz.widget_utils import set_visibility, is_visible
import traitlets
import fnmatch
from jp_gene_viz import color_scale
from jp_gene_viz import color_widget
from jp_gene_viz import getData
from jp_svg_canvas.canvas import load_javascript_support
from jp_gene_viz import array_transforms

NO_TRANSFORM = "no transform"
LOG2_TRANSFORM = 'log 2 fold change'
ZSCORE_TRANSFORM = "Z score"
TRANSFORM_TEXTS = [NO_TRANSFORM, LOG2_TRANSFORM, ZSCORE_TRANSFORM]
TRANSFORM_MAP = {
    LOG2_TRANSFORM: array_transforms.log_2_fold_change_rt_mean,
    ZSCORE_TRANSFORM: array_transforms.z_score,
}

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
        tdd = self.transform_dropdown = widgets.Dropdown(
            options=TRANSFORM_TEXTS,
            value=NO_TRANSFORM
        )
        tdd.on_trait_change(self.draw_click, "value")
        tdd.layout.width = "100px"
        self.title_html = widgets.HTML("Expression Heat Map")
        self.text_assembly = self.make_text_displays()
        self.match_assembly = self.make_match_assembly()
        self.genes_assembly = self.make_genes_assembly(tdd)
        self.info_area = widgets.Textarea(description="status")
        self.assembly = widgets.VBox(children=[self.title_html,
                                               self.text_assembly,
                                               self.svg,
                                               self.color_chooser.svg,
                                               self.match_assembly,
                                               self.genes_assembly,
                                               self.info_area])
        self.dx = 10
        self.dy = 2
        self.data_heat_map = None
        self.display_heat_map = None
        self.row = self.col = None
        self.drawing = False

    def load_data(self, heat_map, side_length=None):
        self.data_heat_map = heat_map
        # project to at most 200 rows and columns
        rows = heat_map.row_names[:200]
        cols = heat_map.col_names[:200]
        if side_length is not None:
            self.side_length = side_length
        self.display_data(rows, cols, side_length)

    def display_data(self, rows, cols, side_length=None):
        (data_rows, data_cols, data) = self.data_heat_map.get_data()
        if side_length is None:
            side_length = self.side_length
        if rows is not None:
            rows = getData.caseless_intersection_list(rows, data_rows, use_left=False)
            self.rows = rows
        else:
            rows = self.rows
        if cols is not None:
            cols = getData.caseless_intersection_list(cols, data_cols, use_left=False)
        heat_map = self.display_heat_map = self.data_heat_map.projection(rows, cols)
        (self.dx, self.dy) = heat_map.fit(self.svg, side_length, self.labels_space)
        self.row = self.col = None
        self.svg.empty()
        return self.draw()

    def get_observations(self):
        (rows, cols, data) = self.display_heat_map.get_data()
        return (rows, data)

    def select_rows(self, rows=None):
        return self.display_data(rows, self.display_heat_map.col_names[:200])

    def column_weights(self):
        if self.col is None:
            return None
        return self.display_heat_map.column_weights(self.col)

    def make_text_displays(self):
        self.row_text = widgets.Text(description="row", value="")
        self.row_text.layout.width = "200px"
        self.col_text = widgets.Text(description="col", value="")
        self.col_text.layout.width = "200px"
        sslider = self.size_slider = widgets.FloatSlider(value=550, min=550, max=3000,
            step=10, readout=False, width="100px")
        sslider.layout.width = "150px"
        svg = self.svg
        traitlets.directional_link((sslider, "value"), (svg, "svg_width"))
        traitlets.directional_link((sslider, "value"), (svg, "svg_height"))
        assembly = widgets.HBox(children=[self.row_text, self.col_text, sslider])
        return assembly

    def make_match_assembly(self):
        b = self.match_button = widgets.Button(description="conditions", width="50px")
        b.layout.width = "80px"
        b.on_click(self.match_click)
        t = self.match_text = widgets.Text(width="300px")
        t.layout.width = "300px"
        d = self.draw_button = widgets.Button(description="draw", width="50px")
        d.layout.width = "50px"
        d.on_click(self.draw_click)
        l = self.list_conditions_button = widgets.Button(description="list", width="50px")
        l.layout.width = "50px"
        l.on_click(self.list_conditions_click)
        c = self.color_checkbox = widgets.Checkbox(description="colors", value=False)
        c.on_trait_change(self.colors_click, "value")
        cl = self.cluster_checkbox = widgets.Checkbox(description="cluster", value=True)
        cl.on_trait_change(self.colors_click, "value")
        assembly = widgets.HBox(children=[b, t, l, d, c, cl])
        return assembly

    def make_genes_assembly(self, transform_dropdown):
        b = self.genes_button = widgets.Button(description="genes", width="50px")
        b.layout.width = "70px"
        b.on_click(self.genes_click)
        t = self.genes_text = widgets.Text(width="300px")
        t.layout.width = "300px"
        r = self.reset_button = widgets.Button(description="reset")
        r.layout.width = "50px"
        r.on_click(self.reset_click)
        l = self.list_genes_button = widgets.Button(description="list")
        l.layout.width = "50px"
        l.on_click(self.list_genes_click)
        assembly = widgets.HBox(children=[b, t, l, r, transform_dropdown])
        return assembly

    def reset_click(self, b=None):
        self.load_data(self.data_heat_map)

    def colors_click(self, b=None):
        #self.color_chooser.svg.visible = self.color_checkbox.value
        set_visibility(self.color_chooser.svg, self.color_checkbox.value)
        self.draw()

    def apply_transform(self):
        transform_text = self.transform_dropdown.value
        transform = TRANSFORM_MAP.get(transform_text)
        try:
            self.display_heat_map.transform_data(transform)
        except array_transforms.TransformError:
            self.info_area.value = "Invalid values for transform " + repr(transform_text)

    def draw_click(self, b=None):
        self.draw()

    def list_conditions_click(self, b=None):
        conditions = self.display_heat_map.col_names
        self.info_area.value = "\t".join(conditions)

    def list_genes_click(self, b=None):
        genes = self.display_heat_map.row_names
        self.info_area.value = "\t".join(genes)

    def genes_click(self, b=None):
        patterns = [x.lower() for x in self.genes_text.value.lower().split()]
        row_set = set()
        rows = [x.lower() for x in self.data_heat_map.row_names]
        for pattern in patterns:
            row_set.update(fnmatch.filter(rows, pattern))
        if not row_set:
            self.info_area.value = "No rows selected"
        else:
            rows = sorted(row_set)[:200]
            columns = self.display_heat_map.col_names
            self.display_data(rows, columns)

    def match_click(self, b=None):
        patterns = [x.lower() for x in self.match_text.value.split()]
        column_set = set()
        columns = [x.lower() for x in self.data_heat_map.col_names]
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
                intensity = heat_map.visible_array()[i, j]
                self.info_area.value = "%s :: %s, %s -> %s" % (name, r, c, intensity)
                if typ == "click":
                    heat_map.unhighlight(svg)
                    heat_map.highlight(svg, i, j, dx, dy)
                    self.row = r
                    self.col = c
                    self.row_text.value = r
                    self.col_text.value = c

    def draw(self):
        try:
            if self.drawing:
                raise ValueError, "too many draws"
            heat_map = self.display_heat_map
            if heat_map is None:
                return
            self.apply_transform()
            self.drawing = True
            if self.cluster_checkbox.value:
                heat_map.cluster_rows()
            svg = self.svg
            svg.empty()
            heat_map.draw(svg, self.dx, self.dy, self.labels_space)
            cc = self.color_chooser
            if is_visible(cc.svg):
                self.info_area.value = "displaying color chooser."
                cc.scale = heat_map.get_color_interpolator()
                cc.count_values(heat_map.visible_array().flatten())
                cc.draw()
            svg.send_commands()
        finally:
            self.drawing = False

    def color_interpolator(self):
        return self.display_heat_map.get_color_interpolator()

    def show(self):
        display(self.assembly)


def display_heat_map(filename, dexpr=None, side_length=550, show=False):
    from jp_gene_viz import getData
    H = HMap.HeatMap()
    (r, c, d) = getData.read_tsv(filename)
    H.set_data(r, c, d)
    if dexpr is None:
        dexpr = ExpressionDisplay()
    dexpr.load_data(H, side_length=side_length)
    if show:
        dexpr.show()
    return dexpr
