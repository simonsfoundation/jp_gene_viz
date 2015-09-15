
import numpy
import dGraph

def checked_names(subset, superset, strict=False):
    ss = set(subset)
    sp = set(superset)
    proper = ss & sp
    if strict and proper != ss:
        raise ValueError("extra names not allowed: " + repr(ss-sp))
    result = [name for name in subset if name in sp]
    return result

def index_dict(L):
    return dict((e, i) for (i, e) in enumerate(L))

class HeatMap(object):

    max_clr = dGraph.clr(255, 0, 0)
    min_clr = dGraph.clr(0, 255, 255)
    zero_clr = dGraph.clr(0, 0, 0)

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
        rows = self.row_names
        cols = self.col_names
        data = self.data
        col_index = cols.index(col_name)
        result = {}
        for (row_index, row) in enumerate(rows):
            result[row] = data[row_index, col_index]
        return result

    def set_data(self, row_names, col_names, data):
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
        return "R_%s_%s" % (i, j)

    def rectName2ij(self, rectName):
        if not rectName.startswith("R_"):
            return None
        sij = rectName[2:]
        (i,j) = [int(x) for x in sij.split("_")]
        return (i,j)

    def rectName2RowCol(self, rectName):
        ij = self.rectName2ij(rectName)
        if ij is None:
            return None
        (i,j) = ij
        row = self.row_names[i]
        col = self.col_names[j]
        return (row, col)

    def color(self, value):
        if value < 0:
            result = dGraph.weighted_color(self.min_clr, self.zero_clr, abs(self.dmin), abs(value))
        else:
            result = dGraph.weighted_color(self.max_clr, self.zero_clr, self.dmax, value)
        return result

    def draw(self, canvas, dx, dy):
        for rowi in xrange(self.nrows):
            for colj in xrange(self.ncols):
                dataij = self.data[rowi,colj]
                nameij = self.rectName(rowi, colj)
                colorij = self.color(dataij)
                canvas.rect(nameij, colj*dx, rowi*dy, dx, dy, colorij)

    def fit(self, canvas, dx, dy):
        if self.ncols == 0 or self.nrows == 0:
            return
        width = dx * self.ncols
        height = dy * self.nrows
        canvas.set_view_box(0, 0, width, height)

    def highlight(self, canvas, rowi, colj, dx, dy):
        x = colj * dx
        y = rowi * dy
        maxx = self.ncols * dx
        maxy = self.nrows * dy
        style = None
        style = {"fill-opacity": 0.4}
        clr = "white"
        for (n, x0, y0, w, h) in [("ll", 0, 0, x, y),
                                  ("ul", x+dx, 0, maxx-x-dx, y),
                                  ("lr", x+dx, y+dy, maxx-x-dx, maxy-y-dy),
                                  ("ur", 0, y+dy, x, maxy-y-dy),
                                 ]:
            canvas.rect(n, x0, y0, w, h, clr, style_dict=style)
            #print (n, x0, y0, w, h, clr)
        canvas.send_commands()

    def unhighlight(self, canvas):
        canvas.delete_names("ll ul lr ur".split())
        canvas.send_commands()

