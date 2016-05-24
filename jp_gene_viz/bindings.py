
"""
This is an experimental class for holding WIG format data.
At the moment it only supports files containing one track
which uses the "variableStep" format:

track type=wiggle_0 name="SL1041_SL972_treat_chrX" description="Extended bp"
variableStep chrom=chrX span=10
3000011 1
3000021 1
3000031 1
"""
import numpy
import gzip
import traitlets


class WigData(traitlets.HasTraits):

    """
    Encapsulate data from a Wig file.
    """

    start_position = traitlets.Float(0, sync=True)

    end_position = traitlets.Float(1000, sync=True)

    def __init__(self, *args, **kwargs):
        super(WigData, self).__init__(*args, **kwargs)
        self.locations = None
        self.heights = None
        self.maxheight = 0
        self.numelts = 0
        self.color = "green"
        self.header1 = self.header2 = None
        self.span = None
        self.chrom = None
        # SVG canvas for drawing, if provided.
        svg = None

    def load_file(self, f, filename=None):
        """
        Load data from a WIG file object.
        """
        self.filename = filename
        # skip 2 lines
        self.header1 = f.readline()
        header2 = self.header2 = f.readline()
        hs = header2.split()
        # parse and validate header info
        try:
            assert hs[0] == "variableStep", ("not in variableStep format: " +
                                             repr((filename, header2)))
            assert len(hs) == 3, ("unexpected header format: " +
                                  repr((filename, header2)))
            for (attr, chunk) in [("chrom", hs[1]), ("span", hs[2])]:
                [attr2, value] = chunk.split("=")
                assert attr2 == attr, ("bad variableStep format: " +
                                       repr((filename, header2, chunk)))
                setattr(self, attr, value)
            self.span = int(self.span)
        except Exception as e:
            if type(e) == AssertionError:
                raise
            raise ValueError("Bad header: " + repr((filename, e)))
        array_text = f.read()
        A = numpy.fromstring(array_text, numpy.float, sep=" ")
        (d,) = A.shape
        B = A.reshape((d/2, 2))
        self.locations = B[:, 0]
        self.heights = B[:, 1]
        self.maxheight = numpy.max(self.heights)
        self.numelts = len(self.heights)

    def load_filename(self, filename):
        """
        Load data using a file name.
        """
        if filename.endswith(".wig"):
            f = open(filename)
        elif filename.endswith(".wig.gz"):
            f = gzip.GzipFile(filename)
        else:
            raise ValueError("filename must end with .wig or .wig.gz")
        self.load_file(f, filename)

    def maximum(self, start_location, end_location):
        """
        Determine the maximum value within a start/end range in the data.
        """
        locations = self.locations
        heights = self.heights
        ss = numpy.searchsorted
        start_index = ss(locations, start_location)
        end_index = ss(locations, end_location)
        if start_index >= end_index:
            if start_index < self.numelts - 1:
                next_location = locations[start_index]
                if next_location < start_location:
                    next_location = locations[start_index + 1]
                if (next_location - start_location) <= self.span * 1.5:
                    return heights[start_index]
            return 0  # missing value means 0
        choices = heights[start_index: end_index]
        return numpy.max(choices)

    def draw(self, svg=None, start_location=None, end_location=None,
             svg_width=None, svg_height=None):
        """
        Draw the binding data to an SVG canvas.
        """
        if svg is None:
            svg = self.svg
        assert svg is not None, "No canvas: cannot draw."
        if start_location is None:
            start_location = self.start_position
        else:
            self.start_position = start_location
        if end_location is None:
            end_location = self.end_position
        else:
            self.end_position = end_location
        svg_width = int(svg_width or svg.svg_width)
        svg_height = int(svg_height or svg.svg_height)
        svg.empty()
        color = self.color
        maxheight = self.maximum(start_location, end_location)
        if maxheight < 1:
            maxheight = self.maxheight
        yscale = (1.0 * svg_height) / maxheight
        dlocation = (end_location - start_location) * 1.0 / svg_width
        for svgx in range(svg_width):
            locationx = start_location + dlocation * svgx
            maxh = self.maximum(locationx, locationx + dlocation)
            svgy = maxh * yscale
            svg.rect(repr((svgx, svgy)), svgx, svg_height - svgy,
                     1, svgy, color)
        svg.send_commands()


def test0(filename="example.wig"):
    f = open(filename)
    W = WigData()
    print ("loading: " + repr(filename))
    W.load_file(f)
    print ("loaded " + repr(W.numelts))
    print ("should be 2", W.maximum(61243301, 61243341))
    print ("should be 3", W.maximum(61243301, 61243541))


def test1(filename="ex2.wig.gz"):
    W = WigData()
    print ("loading: " + repr(filename))
    W.load_filename(filename)
    print ("loaded " + repr(W.numelts))
    print (W.locations[0], W.locations[-1])
    print ("???", W.maximum(61243301, 61243341))
    print ("???", W.maximum(61243301, 61243541))
    return W


def canvas_test(filename="ex2.wig.gz", width=500, height=100):
    from jp_svg_canvas import canvas
    canvas.load_javascript_support()
    svg = canvas.SVGCanvasWidget()
    svg.add_style("background-color", "cyan")
    svg.svg_width = width
    svg.svg_height = height
    svg.set_view_box(0, 0, width, height)
    W = WigData()
    print ("loading: " + repr(filename))
    W.load_filename(filename)
    print ("loaded " + repr(W.numelts) + " max " + repr(W.maxheight))
    W.draw(svg, 3010000, 3010200, width, height)
    return (svg, W)


if __name__ == "__main__":
    import time
    start = time.time()
    test1()
    elapsed = time.time() - start
    print ("elapsed", elapsed)
