
from IPython.display import display
import pprint
from jp_gene_viz import genome_bar
from ipywidgets import widgets
from jp_svg_canvas import canvas
from jp_gene_viz import gtf_format
#import types
import traitlets

# This must be called once:
from jp_svg_canvas.canvas import load_javascript_support


class ExonExplorer(traitlets.HasTraits):

    genes = traitlets.Any()
    
    start_position = traitlets.Float(0, sync=True)
    
    end_position = traitlets.Float(1000, sync=True)
    
    def __init__(self, *args, **kwargs):
        super(ExonExplorer, self).__init__(*args, **kwargs)
        self.genome_zoom = genome_bar.GenomeBar()
        z = self.zoom_svg = self.canvas()
        z.watch_event = "mousemove"
        z.default_event_callback = self.zoom_callback
        self.genome_guide = genome_bar.GenomeBar()
        g = self.guide_svg = self.canvas()
        g.watch_event = "mousemove click"
        g.default_event_callback = self.guide_callback
        self.info = widgets.Text(value="", width=500)
        self.assembly = widgets.VBox(children=[self.zoom_svg,
                                               self.guide_svg,
                                               self.info])
        self.data = gtf_format.GTFData()
        self.name_to_feature = {}
        self.select_name = "SELECTION"
        self.selected_svg_x = None
        traitlets.link((self, "start_position"), (self.genome_zoom, "minLocation"))
        traitlets.link((self, "end_position"), (self.genome_zoom, "maxLocation"))
        #wig.on_trait_change(self.view_genes, "genes")
        
    def canvas(self):
        svg = canvas.SVGCanvasWidget()
        svg.add_style("background-color", "cyan")
        svg.width = 500
        svg.height = 10
        return svg

    def show(self):
        display(self.assembly)

    def zoom_callback(self, info):
        #self.info.value = "z " + repr(info)
        typ = info["type"]
        svgX = info["svgX"]
        name = info["name"]
        location = self.genome_zoom.location_x(svgX)
        self.info.value = repr(location) + " z " + repr((name, typ, svgX))

    def guide_callback(self, info):
        #self.info.value = "g " + repr(info)
        typ = info["type"]
        svgX = info["svgX"]
        name = info["name"]
        shift = info.get("shiftKey")
        location = self.genome_guide.location_x(svgX)
        self.info.value = repr(location) + " g " + repr((name, typ, svgX))
        selected_x = self.selected_svg_x
        svg = self.guide_svg
        sname = self.select_name
        if typ == "click":
            if shift:
                self.unzoom_guide()
            elif selected_x is None:
                # add/replace a selection rectangle
                svg.delete_names([sname])
                self.selected_svg_x = svgX
                style = {"fill-opacity": 0.3}
                svg.rect(sname, svgX, 0, 1, svg.height, "black", style_dict=style)
                svg.send_commands()
            else:
                # apply range selection.
                self.update_selection_rectangle(svg, svgX, selected_x, sname)
                location1 = self.genome_guide.location_x(svgX)
                location2 = self.genome_guide.location_x(selected_x)
                self.genome_zoom.set_limits(location1, location2)
                self.genome_guide.set_limits(location1, location2)
                self.selected_svg_x = None
                self.draw()
        elif typ == "mousemove":
            if selected_x is not None:
                self.update_selection_rectangle(svg, svgX, selected_x, sname)
                svg.send_commands()
        elif typ == "dblclick":
            self.unzoom_guide()

    def unzoom_guide(self):
        self.selected_svg_x = None
        self.genome_guide.fit(self.guide_svg)
        self.draw()

    def update_selection_rectangle(self, svg, svgX, selected_x, sname):
        x = min(svgX, selected_x)
        width = max(1, abs(svgX - selected_x))
        atts = {"x": x, "width": width}
        svg.change_element(sname, atts)

    def load_gtf(self, filename):
        f = open(filename)
        self.info.value = "loading GTF data from file " + repr(filename)
        self.data.load(f)
        self.info.value = "loaded " + repr(filename)

    def view_genes(self, gene_ids, old_gene_ids=None):
        self.info.value = "drawing genes " + repr(gene_ids)
        # save genes only if not a traitlets call
        if old_gene_ids is None:
            self.genes = gene_ids
        assert type(gene_ids) == list, "gene_ids must be a list. " + repr(gene_ids)[:100]
        n2f = self.name_to_feature = {}
        self.genome_zoom.empty()
        self.genome_guide.empty()
        gene_to_exons = self.data.get_gene_features(gene_ids)
        for gene_id in gene_to_exons:
            exons = gene_to_exons[gene_id]
            for exon_dict in exons:
                start = exon_dict["start"]
                exon_name = gene_id + "_" + str(start)
                self.add_feature(exon_name, exon_dict)
        self.genome_zoom.fit(self.zoom_svg)
        self.genome_guide.fit(self.guide_svg)
        self.draw()
        self.info.value = "viewing " + repr(gene_ids)

    def draw(self):
        self.genome_zoom.draw(self.zoom_svg)
        self.genome_guide.draw(self.guide_svg)

    def add_feature(self, name, info_dict):
        self.name_to_feature[name] = info_dict
        self.genome_zoom.add_feature(name, info_dict)
        self.genome_guide.add_feature(name, info_dict)