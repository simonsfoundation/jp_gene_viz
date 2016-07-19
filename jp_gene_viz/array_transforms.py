"""
Heat map array transforms.
"""

import numpy as np
import scipy.stats as stats

class TransformError(ValueError):
    """
    Invalid value for transform.
    """

def log_2_fold_change_rt_mean(array):
    """
    Apply a log2 fold change relative to mean for all rows of array.
    """
    if not np.all(array >= 0):
        raise TransformError("Array may not contain negative values.")
    if not np.any(array > 0):
        raise TransformError("Array must contain some non-zeros.")
    array1 = 1 + array
    mean = np.mean(array1, 1)
    normalized = array1/mean[..., np.newaxis]
    return np.log2(normalized)

def z_score(array):
    return stats.zscore(array, 1)
