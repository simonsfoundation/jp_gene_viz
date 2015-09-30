
"""
Logic for manipulating and interpolating colors.
"""

import numpy


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


class ColorInterpolator(object):

	def __init__(self):
		pass