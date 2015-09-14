
import unittest
from .. import HMap
from .. import dGraph

class TestCheckedNames(unittest.TestCase):

    def test_not_strict(self):
        superset = "alpha beta gamma".split()
        subset = "beta gamma delta".split()
        result = HMap.checked_names(subset, superset)
        self.assertEqual(result, "beta gamma".split())

    def test_strict(self):
        superset = "alpha beta gamma".split()
        subset = "beta gamma delta".split()
        with self.assertRaises(ValueError):
            result = HMap.checked_names(subset, superset, strict=True)

    def test_all(self):
        superset = "alpha beta gamma".split()
        subset = "alpha beta gamma".split()
        result = HMap.checked_names(subset, superset)
        self.assertEqual(result, subset)

    def test_strict_ok(self):
        superset = "alpha beta gamma delta phi".split()
        subset = "beta gamma delta".split()
        result = HMap.checked_names(subset, superset, strict=True)
        self.assertEqual(subset, result)


class TestIndexDict(unittest.TestCase):

    def test_abc(self):
        L = list("abc")
        D = HMap.index_dict(L)
        self.assertEqual({"a": 0, "b": 1, "c":2}, D)


class TestProjection(unittest.TestCase):

    def test_basic(self):
        row_names = "A B C".split()
        col_names = "X Y".split()
        data = [ [0, 1], [2, 3], [4, 5] ]
        H = HMap.HeatMap(row_names, col_names, data)
        rn = "A B".split()
        cn = "Y X".split()
        Hp = H.projection(rn, cn)
        self.assertEqual(Hp.row_names, rn)
        self.assertEqual(Hp.col_names, cn)
        Hpdata = Hp.data
        self.assertEqual([[1, 0], [3, 2]], Hpdata.tolist())
        


class Test0(unittest.TestCase):

    pass


class Test0(unittest.TestCase):

    pass


class Test0(unittest.TestCase):

    pass

