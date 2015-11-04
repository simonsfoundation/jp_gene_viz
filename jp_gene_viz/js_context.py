"""
Utility for ensuring that each javascript file is loaded exactly once for a Jupyter
python interpreter.
"""

from __future__ import print_function

import os
from IPython.display import display, Javascript

my_dir = os.path.dirname(__file__)

LOADED_JAVASCRIPT = set()

def load_if_not_loaded(filenames, verbose=False):
    """
    Load a javascript file to the Jupyter notebook context,
    unless it was already loaded.
    """
    for filename in filenames:
        if os.path.exists(filename):
            js_filename = filename
        else:
            js_filename = os.path.join(my_dir, filename)
        assert os.path.exists(js_filename), "no such file " + repr(js_filename)
        if not js_filename in LOADED_JAVASCRIPT:
            if verbose:
                print("loading javascript file", js_filename)
            display(Javascript(js_filename))
            LOADED_JAVASCRIPT.add(js_filename)
        else:
            if verbose:
                print ("not reloading javascript file", js_filename)