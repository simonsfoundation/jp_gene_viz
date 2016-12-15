
import numpy
from jp_gene_viz import dGraph
from jp_gene_viz import color_scale
from jp_gene_viz import getData
from scipy.cluster.hierarchy import linkage, leaves_list


def checked_names(subset, superset, strict=False):
    """
    Check that names in subset are in superset.  Return list of such names.
    Raise a ValueError if strict is set and the subset contains an element
    not in superset.
    """
    ss = set(subset)
    sp = set(superset)
    proper = set(getData.caseless_intersection_list(ss, sp))  # ss & sp
    if strict and proper != ss:
        raise ValueError("extra names not allowed: " + repr(ss-sp))
    result = [name for name in subset if name in sp]
    return result


def index_dict(L):
    """
    Return a dictionary mapping the members of sequence L to their
    indices in L.
    """
    return dict((e, i) for (i, e) in enumerate(L))


class HeatMap(object):

    """
    Encapsulate a heatmap consisting of named rows and named columns and
    a numeric data value for each row/column combination.
    """

    max_clr = color_scale.medRed
    min_clr = color_scale.blue
    zero_clr = color_scale.lightLightGrey
    highlight_color = "black"

    def __init__(self, row_names=None, col_names=None, data=None):
        if data is None:
            # dummy example data
            nrows = 20
            ncols = 10
            row_names = ["r%s" % i for i in range(nrows)]
            col_names = ["c%s" % i for i in range(ncols)]
            data = numpy.arange(nrows * ncols).reshape((nrows, ncols))
        self.set_data(row_names, col_names, data)

    def projection(self, rows=None, cols=None, strict=False):
        """
        Return a heat map restricted to listed row and column names.
        """
        row_names = self.row_names
        col_names = self.col_names
        if rows is None:
            rows = row_names[:]
        else:
            rows = checked_names(rows, row_names, strict)
        if cols is None:
            cols = col_names[:]
        else:
            cols = checked_names(cols, col_names, strict)
        if not rows:
            raise IndexError("no valid rows selected in projection")
        if not cols:
            raise IndexError("no valid columns selected in projection")
        data = self.data
        col_index = index_dict(col_names)
        row_index = index_dict(row_names)
        proj_data = []
        for row_name in rows:
            data_row = data[row_index[row_name]]
            proj_row = [data_row[col_index[col_name]] for col_name in cols]
            proj_data.append(proj_row)
        return HeatMap(rows, cols, proj_data)

    def column_weights(self, col_name):
        """
        Return a dictionary mapping row names to entry values for
        a column name.
        """
        rows = self.row_names
        cols = self.col_names
        data = self.display_data
        col_index = cols.index(col_name)
        result = {}
        for (row_index, row) in enumerate(rows):
            result[row] = data[row_index, col_index]
        return result

    def get_data(self):
        return (self.row_names, self.col_names, self.display_data)

    def set_data(self, row_names, col_names, data):
        """
        Store row names, column names and data entries.
        """
        self.row_names = row_names
        self.col_names = col_names
        A = self.data = numpy.array(data)
        self.dmax = self.dmin = self.nrows = 0
        self.ncols = len(self.col_names)
        if len(A):
            self.dmax = numpy.max(A)
            self.dmin = numpy.min(A)
            (self.nrows, self.ncols) = A.shape
        assert self.nrows == len(self.row_names)
        assert self.ncols == len(self.col_names)
        self.display_data = self.data
        self.row_order = None

    def visible_array(self):
        return self.display_data

    def transform_data(self, array_transform):
        save_data = self.display_data
        if array_transform is None:
            self.display_data = self.data
        else:
            self.display_data = array_transform(self.data)
        # zap any nan values
        self.display_data[numpy.isnan(self.display_data)] = 0
        # reset color interpolation if data has changed.
        if (save_data.shape != self.display_data.shape or
            not numpy.allclose(save_data, self.display_data)):
            self._color_interpolator = None
        self.row_order = None

    def cluster_rows(self, method="ward"):
        display_data = self.display_data
        rows = len(display_data)
        if rows < 2:
            # don't attempt to cluster less than 2 rows
            return
        Z = linkage(self.display_data, method)
        self.row_order = leaves_list(Z)

    def rectName(self, i, j):
        """
        Return a name for a data value (for cross referencesing svg events).
        """
        return "R_%s_%s" % (i, j)

    def rectName2ij(self, rectName):
        """
        return the (i, j) indices corresponding to an entry name.
        """
        if not rectName.startswith("R_"):
            return None
        sij = rectName[2:]
        (i, j) = [int(x) for x in sij.split("_")]
        return (i, j)

    def rectName2RowCol(self, rectName):
        """
        Return the column and row names corresponding to an entry name.
        """
        ij = self.rectName2ij(rectName)
        if ij is None:
            return None
        (i, j) = ij
        row = self.row_names[i]
        col = self.col_names[j]
        return (row, col)

    _color_interpolator = None

    def get_color_interpolator(self):
        result = self._color_interpolator
        if result is None:
            v = self.display_data.flatten()
            M = 1.0
            m = 0.0
            if len(v) > 0:
                M = numpy.max(v)
                m = numpy.min(v)
            # If min and max are same then do something arbitrary
            if M == m:
                M = m + 1
            mc = self.min_clr
            Mc = self.max_clr
            result = color_scale.ColorInterpolator(mc, Mc, m, M)
            if m < 0 and M > 0:
                result.add_color(0, self.zero_clr)
            self._color_interpolator = result
        return result

    def fix_data(self, default_value=0):
        "Replace invalid data values in display data."
        data = self.display_data
        for check in (numpy.isinf, numpy.isnan):
            check_indices = numpy.where(check(data))
            data[check_indices] = default_value

    def draw(self, canvas, dx, dy, labels_space=None, fit=True):
        """
        Draw the heat map on an SVG canvas.
        """
        canvas.empty()
        self.fix_data()
        ci = self.get_color_interpolator()
        row_order = self.row_order
        if row_order is None:
            row_order = list(range(self.nrows))
        for (rowp, rowi) in enumerate(row_order):
            for colj in range(self.ncols):
                dataij = self.display_data[rowi, colj]
                nameij = self.rectName(rowi, colj)
                colorij = ci.interpolate_color(dataij)
                canvas.rect(nameij, colj*dx, rowp*dy, dx, dy, colorij)
        if labels_space is not None:
            label_color = "black"
            col_end = self.ncols * dx
            style = {
                "font-size": min(dy, 15), 
                "text-anchor": "start",
                "alignment-baseline": "middle"
                }
            for (rowp, rowi) in enumerate(row_order):
                row_name = self.row_names[rowi]
                y = (rowp + 0.5) * dy
                canvas.text(None, col_end, y,
                            row_name, label_color, **style)
            row_end = self.nrows * dy
            for colj in range(self.ncols):
                x = (colj + 0.5) * dx
                transform = "rotate(90,%s,%s)" % (x, row_end)
                style = {"font-size": min(dx, 15),
                         "transform": transform,
                         "text-anchor": "start",
                         "alignment-baseline": "middle"}
                col_name = self.col_names[colj]
                canvas.text(None, x, row_end, col_name, label_color, **style)
        if fit:
            canvas.fit(True)

    def fit(self, canvas, side_length, label_space=None):
        """
        Fit an svg canvas view box for the data in a heat map.
        """
        ncols = max(1, self.ncols)
        nrows = max(1, self.nrows)
        dx = max(1, side_length / ncols)
        dy = max(1, side_length / nrows)
        if label_space is None:
            additional = 0
        else:
            additional = label_space
        width = dx * self.ncols + label_space
        height = dy * self.nrows + label_space
        side = max(width, height)
        canvas.set_view_box(0, 0, side, side)
        return (dx, dy)

    def highlight(self, canvas, rowi, colj, dx, dy):
        """
        Highlight the rowi and the colj on an svg canvas.
        """
        x = colj * dx
        y = rowi * dy
        maxx = self.ncols * dx
        maxy = self.nrows * dy
        style = None
        style = {"fill-opacity": 0.2}
        clr = self.highlight_color
        for (n, x0, y0, w, h) in [("ll", 0, 0, x, y),
                                  ("ul", x+dx, 0, maxx-x-dx, y),
                                  ("lr", x+dx, y+dy, maxx-x-dx, maxy-y-dy),
                                  ("ur", 0, y+dy, x, maxy-y-dy),
                                  ]:
            canvas.rect(n, x0, y0, w, h, clr, style_dict=style)
        canvas.send_commands()

    def unhighlight(self, canvas):
        """
        Remove any highlight from the canvas if present.
        """
        canvas.delete_names("ll ul lr ur".split())
        canvas.send_commands()
