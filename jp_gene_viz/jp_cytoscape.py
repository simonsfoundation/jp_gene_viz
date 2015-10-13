from __future__ import print_function # For py 2.7 compat

from IPython.display import display, Javascript
import ipywidgets as widgets
from traitlets import Unicode, Float, List, Dict
import json
import os
import pprint

def load_javascript_support(verbose=False):
    """
    Install javascript support required for this module into the notebook.
    """
    my_dir = os.path.dirname(__file__)
    for filename in ["cytoscape.js", "jp_cytoscape.js"]:
        js_filename = os.path.join(my_dir, filename)
        assert os.path.exists(js_filename)
        if verbose:
            print("loading javascript from", repr(js_filename))
        display(Javascript(js_filename))

class CytoscapeWidget(widgets.DOMWidget):
    """
    Jupyter notebook widget which presents a Cytoscope.js visualization.
    """

    _view_name = Unicode("CytoScapeView", sync=True)

