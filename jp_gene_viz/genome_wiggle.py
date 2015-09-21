
from jp_gene_viz import genome_guide
from jp_svg_canvas import canvas
from jp_gene_viz import bindings
from IPython.display import display
import pprint
from ipywidgets import widgets
from jp_svg_canvas.canvas import load_javascript_support
import traitlets

class GenomeWiggle(traitlets.HasTraits):

    # XXXX refactor to allow multiple wiggles
    # XXXX connect guide traitlet to local traitlet, connectable to outside.

    def __init__(self, width=500, height=100, *args, **kwargs):
        super(GenomeWiggle, self).__init__(*args, **kwargs)
        self.wigs = []
        guide = self.guide = genome_guide.ExonExplorer()
        self.width = width
        self.height = height
        self.assembled = False

    def assemble(self):
        guide = self.guide
        wigs = self.wigs
        vertical = []
        for wig in wigs:
            svg = wig.svg = canvas.SVGCanvasWidget()
            vertical.append(svg)
            svg.width = self.width
            svg.height = self.height
            svg.set_view_box(0, 0, self.width, self.height)
            svg.add_style("background-color", "cyan")
            traitlets.link((guide, "start_position"), (wig, "start_position"))
            traitlets.link((guide, "end_position"), (wig, "end_position"))
        vertical.append(self.guide.assembly)
        self.assembly = widgets.VBox(children=vertical)
        wig.on_trait_change(self.draw, "start_position")
        self.assembled = True

    def draw(self):
        if not self.assembled:
            self.assemble()
        for wig in self.wigs:
            wig.draw(wig.svg)

    def show(self):
        if not self.assembled:
            self.assemble()
        self.draw()
        display(self.assembly)

    def load_gtf(self, gtf_file_name):
        #self.wig_data.load_filename(wig_file_name)
        print ("loading gtf", gtf_file_name)
        self.guide.load_gtf(gtf_file_name)
        print ("done", gtf_file_name)
        #self.draw()

    def load_wiggle(self, wig_file_name):
        wig = bindings.WigData()
        print ("loading", wig_file_name)
        wig.load_filename(wig_file_name)
        print ("done", wig_file_name)
        self.wigs.append(wig)
