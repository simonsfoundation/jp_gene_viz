
"""
Logic for manipulating and interpolating colors.
"""

import numpy
from jp_gene_viz.json_mixin import JsonMixin


def clr(r, g, b):
    result = numpy.array([r*1.0, g*1.0, b*1.0])
    clr_check(result)
    return result


def clr_check(clr):
    assert max(clr) < 256
    assert min(clr) >= 0


def weighted_color(maxclr, minclr, maxvalue, value):
    assert value <= maxvalue
    assert value >= 0
    if maxvalue==0:
        clr = minclr
    else:
        lm = value/float(maxvalue)
        clr = (lm * maxclr) + ((1 - lm) * minclr)
    return color(clr)


def color(clr):
    clr_check(clr)
    ints = map(int, clr)
    hexs = ["%02x" % x for x in ints]
    return "#" + "".join(hexs)


def color2clr(color):
    assert color.startswith("#")
    rhex = color[1:3]
    ghex = color[3:5]
    bhex = color[5:7]
    return clr(int(rhex, 16), int(ghex, 16), int(bhex, 16))


levels4 = [0, 85, 170, 255]


def color64(x, y):
    assert x >= 0 and x < 8
    assert y >= 0 and y < 8
    n = x * 8 + y
    (n, r0) = divmod(n, 4)
    (n, b0) = divmod(n, 4)
    (n, g0) = divmod(n, 4)
    assert n == 0, repr((n, r0, b0, g0))
    r = levels4[r0]
    g = levels4[g0]
    b = levels4[b0]
    return clr(r, g, b)


class colorConverter(object):

    @staticmethod
    def to_json_value(color):
        return color.tolist()

    @staticmethod
    def from_json_value(alist):
        return clr(*alist)


class breakpointConverter(object):

    @staticmethod
    def to_json_value(alist):
        return [(v, c.tolist()) for (v, c) in alist]

    @staticmethod
    def from_json_value(alist):
        return [(v, clr(*c)) for (v, c) in alist]


class ColorInterpolator(JsonMixin):

    json_atts = "minvalue maxvalue".split()
    json_objects = {
        "minclr": colorConverter,
        "maxclr": colorConverter,
        "breakpoints": breakpointConverter,
    }

    def __init__(self, minclr=clr(0,0,0), maxclr=clr(255,0,0),
                minvalue=0.0, maxvalue=1.0):
        assert minvalue <= maxvalue, (
            "bad extrema " + repr((minvalue, maxvalue)))
        # avoid div by zero issues.
        if minvalue == maxvalue:
            maxvalue = minvalue + 1
        self.minclr = minclr
        self.maxclr = maxclr
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.breakpoints = [(minvalue, minclr), (maxvalue, maxclr)]

    def set_color_mapping(self, value_to_color):
        """
        Re-initialize from a dictionary mapping values to color arrays.
        """
        values_colors = sorted(value_to_color.items())
        (minvalue, minclr) = values_colors[0]
        (maxvalue, maxclr) = values_colors[-1]
        self.__init__(minclr, maxclr, minvalue, maxvalue)
        for (v, c) in values_colors[1:-1]:
            self.add_color(v, c)

    def remove_color(self, clr):
        return self.add_color(None, clr)

    def add_color(self, value, clr):
        col = color(clr)
        b = [(v, c) for (v, c) in self.breakpoints
             if v != value and color(c) != col]
        if value is not None:
            b += [(value, clr)]
            b = sorted(b)
            if value == self.minvalue:
                self.minclr = clr
            if value == self.maxvalue:
                self.maxclr = clr
        if b[0][0] > self.minvalue:
            b.insert(0, (self.minvalue, self.minclr))
        if b[-1][0] < self.maxvalue:
            b.append((self.maxvalue, self.maxclr))
        self.breakpoints = b

    def normalized_value(self, value):
        lowvalue = self.minvalue
        highvalue = self.maxvalue
        result = (value - lowvalue) * 1.0 / (highvalue - lowvalue)
        return max(0.0, min(1.0, result))

    def denormalized_value(self, nvalue):
        nvalue = max(0.0, min(1.0, nvalue))
        lowvalue = self.minvalue
        highvalue = self.maxvalue
        return lowvalue + (highvalue - lowvalue) * nvalue

    def interpolate_color(self, value):
        lowvalue = self.minvalue
        highvalue = self.maxvalue
        if value < lowvalue:
            value = lowvalue  # ???
        if value > highvalue:
            value = highvalue  # ???
        lowcolor = self.minclr
        highcolor = self.maxclr
        for (v,c) in self.breakpoints:
            if v < value:
                lowvalue = v
                lowcolor = c
            else:
                highvalue = v
                highcolor = c
                break
        result = weighted_color(highcolor, lowcolor, highvalue - lowvalue, value - lowvalue)
        return result

# Standard color choices.
blue = clr(0,0,255)
medBlue = clr(0,85,255)
medRed = clr(228,26,28)
lightGrey = clr(217,217,217)
lightLightGrey = clr(235,235,235)