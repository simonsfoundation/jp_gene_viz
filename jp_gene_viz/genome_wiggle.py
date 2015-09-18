
from jp_gene_viz import genome_guide
from jp_svg_canvas import canvas
from jp_gene_viz import bindings
from IPython.display import display
import pprint
from ipywidgets import widgets
from jp_svg_canvas.canvas import load_javascript_support
import traitlets

class GenomeWiggle(traitlets.HasTraits):

    def __init__(self, width=500, height=100, *args, **kwargs):
        super(GenomeWiggle, self).__init__(*args, **kwargs)
        guide = self.guide = genome_guide.ExonExplorer()
        wig = self.wig_data = bindings.WigData()
        svg = self.wig_svg = canvas.SVGCanvasWidget()
        svg.width = width
        svg.height = height
        svg.set_view_box(0, 0, width, height)
        self.assembly = widgets.VBox(children=[svg, self.guide.assembly])
        traitlets.link((guide, "start_position"), (wig, "start_position"))
        traitlets.link((guide, "end_position"), (wig, "end_position"))
        wig.on_trait_change(self.draw, "start_position")

    def draw(self):
        self.wig_data.draw(self.wig_svg)

    def show(self):
        display(self.assembly)

    def load_files(self, gtf_file_name, wig_file_name):
        self.wig_data.load_filename(wig_file_name)
        self.guide.load_gtf(gtf_file_name)
        self.draw()
