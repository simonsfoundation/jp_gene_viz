import unittest
import numpy
import pprint

#from .. import LAS_fit
from jp_gene_viz import LAS_fit

class TestMaximum(unittest.TestCase):

    def test_0(self, penalty=0, tolerance=0):
        U = numpy.zeros((1,1))
        v = numpy.zeros((1,))
        fit = LAS_fit.l1_fit(U, v)
        m = fit["m"]
        k = fit["k"]
        self.assertEqual(list(m), [0])
        self.assertEqual(k, 0)

    def test_0_1(self):
        return self.test_0(1.0)

    def test_0_1_1(self):
        return self.test_0(1.0, 1.0)

    def test_no_solution(self):
        U = numpy.zeros((1,1))
        v = numpy.ones((1,))
        fit = LAS_fit.l1_fit(U, v)
        pprint.pprint(fit)
