
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


class ColorInterpolator(object):

	def __init__(self, minclr=clr(0,0,0), maxclr=clr(255,0,0),
		        minvalue=0.0, maxvalue=1.0):
		assert minvalue < maxvalue
		self.minclr = minclr
		self.maxclr = maxclr
		self.minvalue = minvalue
		self.maxvalue = maxvalue
		self.breakpoints = [(minvalue, minclr), (maxvalue, maxclr)]

	def add_color(self, value, clr):
		breakpoints = [(v, c) for (v, c) in self.breakpoints if v != value]
		breakpoints += [(value, clr)]
		self.breakpoints = sorted(breakpoints)
		if value == self.minvalue:
			self.minclr = clr
		if value == self.maxvalue:
			self.maxclr = clr

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

