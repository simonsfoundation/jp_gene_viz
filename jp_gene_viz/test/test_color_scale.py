
import unittest
from .. import color_scale


class TestColor64(unittest.TestCase):

    def ints(self, x, y):
        return map(int, color_scale.color64(x,y))

    def test_black(self):
        self.assertEqual([0, 0, 0], self.ints(0,0))

    def test_white(self):
        self.assertEqual([255, 255, 255], self.ints(7, 7))


class TestBasicInterps(unittest.TestCase):

    minimum = 0
    maximum = 1

    def setUp(self):
        m = self.minimum
        M = self.maximum
        self.ci = color_scale.ColorInterpolator(minvalue=m, maxvalue=M)

    def test_min(self):
    	c = self.ci.interpolate_color(self.minimum)
    	self.assertEqual(c, "#000000")

    def test_max(self):
    	c = self.ci.interpolate_color(self.maximum)
    	self.assertEqual(c, "#ff0000")

    def test_middle(self):
    	c = self.ci.interpolate_color((self.minimum + self.maximum) * 0.5)
    	self.assertEqual(c, "#7f0000")

class testShift(TestBasicInterps):

	minimum = -120.0
	maximum = 35.0

class TestBreakPoint(unittest.TestCase):

    def setUp(self):
    	ci = self.ci = color_scale.ColorInterpolator()
    	ci.add_color(0, color_scale.clr(100, 100, 100))
    	ci.add_color(1, color_scale.clr(100, 0, 100))
    	ci.add_color(0.5, color_scale.clr(0, 0, 0))

    def test_min(self):
    	c = self.ci.interpolate_color(0)
    	self.assertEqual(c, "#646464")

    def test_max(self):
    	c = self.ci.interpolate_color(1)
    	self.assertEqual(c, "#640064")

    def test_middle(self):
    	c = self.ci.interpolate_color(0.5)
    	self.assertEqual(c, "#000000")

    def test_quarter(self):
    	c = self.ci.interpolate_color(0.25)
    	self.assertEqual(c, "#323232")

class TestColor2Clr(unittest.TestCase):

    def test_123456(self, hex="#123456"):
        forward = color_scale.color2clr(hex)
        backward = color_scale.color(forward)
        self.assertEqual(hex, backward)

    def test_456789(self, hex="#456789"):
        return self.test_123456(hex)
