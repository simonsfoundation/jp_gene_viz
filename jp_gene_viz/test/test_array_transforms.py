
from .. import array_transforms
import unittest
import numpy as np

class TestLog2(unittest.TestCase):

    def test_basic(self):
        a = np.array([
            [0, 1, 2], 
            [2, 3, 4]])
        t = array_transforms.log_2_fold_change_rt_mean(a)
        e = np.array([
            [-1.,          0.,          0.5849625 ],
            [-0.4150375,   0.,          0.32192809]])
        np.testing.assert_allclose(t, e)

class TestZScore(unittest.TestCase):

    def test_basic(self):
        a = np.array([
            [0, 1, 2], 
            [2, 3, 4]])
        t = array_transforms.z_score(a)
        e = np.array([
            [-1.22474487,  0.,          1.22474487],
            [-1.22474487,  0.,          1.22474487]])
        np.testing.assert_allclose(t, e)
