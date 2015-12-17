
import unittest
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from .. import bindings

EXAMPLE_FILE = """
track type=wiggle_0 name="SL1041_SL972_treat_chrX"\
 description="Extended tag pileup from MACS version 1.4.0rc2 20110214 for every 10 bp"
variableStep chrom=chrX span=10
3000011 1
3000021 1
3000031 2
3000041 2
3000051 1
3000061 1
3000071 1
3000081 3
3000091 13
4000101 1
4000111 1
4000121 1
4000131 1
4000141 1
4000281 1
4000291 1
4000301 1
4000311 1
4000321 1
""".strip() + "\n"

from .. import bindings


class TestMaximum(unittest.TestCase):

    def parse_file(self):
        f = StringIO(EXAMPLE_FILE)
        result = bindings.WigData()
        result.load_file(f)
        return result

    def setUp(self):
        self.W = self.parse_file()

    def test_off_left(self):
        self.assertEqual(self.W.maximum(0, 1), 0)

    def test_off_right(self):
        self.assertEqual(self.W.maximum(5000000, 5000001), 0)

    def test_gap(self):
        self.assertEqual(self.W.maximum(3000191, 3400091 ), 0)

    def test_over1(self):
        self.assertEqual(self.W.maximum(3000085, 3000095), 13)

    def test_over_many(self):
        self.assertEqual(self.W.maximum(0, 3000039), 2)

    def test_over_all(self):
        self.assertEqual(self.W.maximum(0, 999999999), 13)

    def test_at_2(self):
        self.assertEqual(self.W.maximum(3000091, 4000101), 13)

