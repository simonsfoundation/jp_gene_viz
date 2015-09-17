

import numpy
import gzip

class WigData(object):

	def __init__(self):
		self.locations = None
		self.heights = None
		self.maxheight = 0
		self.numelts = 0
		self.color = "green"

	def load_file(self, f):
		# skip 2 lines
		f.readline()
		f.readline()
		array_text = f.read()
		A = numpy.fromstring(array_text, numpy.float, sep=" ")
		(d,) = A.shape
		B = A.reshape((d/2, 2))
		self.locations = B[:,0]
		self.heights = B[:,1]
		self.maxheight = numpy.max(self.heights)
		self.numelts = len(self.heights)

	def load_filename(self, filename):
		if filename.endswith(".wig"):
			f = open(filename)
		elif filename.endswith(".wig.gz"):
			f = gzip.GzipFile(filename)
		else:
			raise ValueError("filename must end with .wig or .wig.gz")
		self.load_file(f)

	def maximum(self, start_location, end_location):
		locations = self.locations
		heights = self.heights
		ss = numpy.searchsorted
		start_index = ss(locations, start_location)
		if start_location == end_location:
			if start_location < self.numelts:
				return heights[numelts]
			else:
				return 0
		end_index = ss(locations, end_location)
		if start_index >= end_index:
			return 0
		choices = heights[start_index: end_index]
		return numpy.max(choices)

	def draw(self, svg, start_location, end_location, svg_width, svg_height):
		svg.empty()
		color = self.color
		maxheight = self.maximum(start_location, end_location)
		if maxheight < 1:
			maxheight = self.maxheight
		yscale = (1.0 * svg_height) / maxheight
		dlocation = (end_location - start_location) * 1.0 / svg_width
		for svgx in xrange(svg_width):
			locationx = start_location + dlocation * svgx
			maxh = self.maximum(locationx, locationx + dlocation)
			svgy = maxh * yscale
			print (map(int, (locationx, locationx + dlocation, svgx, maxh, svgy)))
			svg.rect(repr((svgx, svgy)), svgx, svg_height - svgy, 1, svgy, color)
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
	svg.width = width
	svg.height = height
	svg.set_view_box(0, 0, width, height)
	W = WigData()
	print ("loading: " + repr(filename))
	W.load_filename(filename)
	print ("loaded " + repr(W.numelts) + " max " + repr(W.maxheight))
	W.draw(svg, 3000011, 4074591, width, height)
	return (svg, W)


if __name__ == "__main__":
	import time
	start = time.time()
	test1()
	elapsed = time.time() - start
	print ("elapsed", elapsed)
