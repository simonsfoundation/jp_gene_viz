
import numpy
import dGraph
import color_scale


def checked_names(subset, superset, strict=False):
    """
    Check that names in subset are in superset.  Return list of such names.
    Raise a ValueError if strict is set and the subset contains an element
    not in superset.
    """
    ss = set(subset)
    sp = set(superset)
    proper = ss & sp
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

    max_clr = dGraph.clr(255, 0, 0)
    min_clr = dGraph.clr(0, 255, 0)
    zero_clr = dGraph.clr(230, 230, 230)
    highlight_color = "black"

    def __init__(self, row_names=None, col_names=None, data=None):
        if data is None:
            # dummy example data
            nrows = 20
            ncols = 10
            row_names = ["r%s" % i for i in xrange(nrows)]
            col_names = ["c%s" % i for i in xrange(ncols)]
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
        data = self.data
        col_index = cols.index(col_name)
        result = {}
        for (row_index, row) in enumerate(rows):
            result[row] = data[row_index, col_index]
        return result

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
            v = self.data.flatten()
            M = numpy.max(v)
            m = numpy.min(v)
            mc = self.min_clr
            Mc = self.max_clr
            result = color_scale.ColorInterpolator(mc, Mc, m, M)
            if m < 0 and M > 0:
                result.add_color(0, self.zero_clr)
            self._color_interpolator = result
        return result

    def draw(self, canvas, dx, dy, labels_space=None):
        """
        Draw the heat map on an SVG canvas.
        """
        canvas.empty()
        ci = self.get_color_interpolator()
        for rowi in xrange(self.nrows):
            for colj in xrange(self.ncols):
                dataij = self.data[rowi, colj]
                nameij = self.rectName(rowi, colj)
                colorij = ci.interpolate_color(dataij)
                canvas.rect(nameij, colj*dx, rowi*dy, dx, dy, colorij)
        if labels_space is not None:
            label_color = "black"
            col_end = self.ncols * dx
            style = {"font-size": min(dy, 15), "text-anchor": "start"}
            for rowi in xrange(self.nrows):
                row_name = self.row_names[rowi]
                canvas.text(None, col_end, (rowi + 1) * dy,
                            row_name, label_color, **style)
            row_end = self.nrows * dy
            for colj in xrange(self.ncols):
                x = colj * dx
                transform = "rotate(90,%s,%s)" % (x, row_end)
                style = {"font-size": min(dx, 15),
                         "transform": transform,
                         "text-anchor": "start"}
                col_name = self.col_names[colj]
                canvas.text(None, x, row_end, col_name, label_color, **style)

    def fit(self, canvas, side_length, label_space=None):
        """
        Fit an svg canvas view box for the data in a heat map.
        """
        dx = max(1, side_length / self.ncols)
        dy = max(1, side_length / self.nrows)
        if label_space is None:
            additional = 0
        else:
            additional = label_space
        if self.ncols == 0 or self.nrows == 0:
            return
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
