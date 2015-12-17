
import traitlets

class GenomeBar(traitlets.HasTraits):

    minLocation = traitlets.Float(500, sync=True)

    maxLocation = traitlets.Float(1000, sync=True)

    def __init__(self, height=10, width=500, *args, **kwargs):
        super(GenomeBar, self).__init__(*args, **kwargs)
        self.height = height
        self.width = width
        self.minLocation = 500
        self.maxLocation = 1000
        self.nameToFeature = {}
        self.color = "blue"
        self.linewidth = 2

    def empty(self):
        self.nameToFeature = {}

    def add_feature(self, name, feature):
        self.nameToFeature[name] = feature

    def fit(self, canvas, shrink=True, relax=True):
        n2f = self.nameToFeature
        features = n2f.values()
        maxFeature = max(f["end"] for f in features)
        if shrink:
            self.maxLocation = maxFeature
            self.minLocation = min(f["start"] for f in features)
        else:
            self.minLocation = 0
            self.maxLocation = max(self.maxLocation, maxFeature)
        if relax:
            # add 10% on each side
            percent10 = (self.maxLocation - self.minLocation) * 0.1
            self.maxLocation = self.maxLocation + percent10
            self.minLocation = max(0, self.minLocation - percent10)
        self.adjust_canvas(canvas)

    def adjust_canvas(self, canvas):
        canvas.set_view_box(0, 0, self.width, self.height)
        canvas.width = self.width
        canvas.height = self.height
        canvas.add_style("background-color", "yellow")

    def canvas_x(self, location):
        minL = self.minLocation
        offset = location - minL
        return (self.width * offset)/(self.maxLocation - minL)

    def location_x(self, svgX):
        minL = self.minLocation
        return minL + (svgX * (self.maxLocation - minL))/self.width

    def set_limits(self, location1, location2):
        minLocation = min(location1, location2)
        maxLocation = max(location1, location2)
        maxLocation = max(maxLocation, minLocation+100) # sanity check
        self.minLocation = minLocation
        self.maxLocation = maxLocation

    def draw(self, canvas):
        canvas.empty()
        height = self.height
        midheight = height/2
        color = self.color
        canvas.line("guide_line", 0, midheight,
                    self.width, midheight,
                    color, self.linewidth)
        n2f = self.nameToFeature
        for name in n2f:
            feature = n2f[name]
            xstart = self.canvas_x(feature["start"])
            xend = self.canvas_x(feature["end"])
            #print (name, xstart, xend, xend-xstart)
            width = max(1, xend - xstart)
            if xstart >= 0 and xend <= self.width:
                #print (name, xstart, xend, xend-xstart)
                canvas.rect(name, xstart, 0, width, height, color)
                # add a line in case tthe rectangle is invisible
                canvas.line(name, xstart, 0, xstart, height, color)
        canvas.send_commands()

def test0():
    import pprint
    import gtf_format
    from jp_svg_canvas import canvas
    canvas.load_javascript_support()
    GB = GenomeBar()
    f = open("genes.gtf")
    print ("reading file")
    if 0:
        L = list(gtf_format.gtf_lines_to_dicts(f))
        L = [d for d in L if d.get("feature") == "exon"]
    else:
        D = gtf_format.GTFData()
        D.load(f)
        GF = D.get_gene_features(["tmc6"])
        #pprint.pprint(sorted(D.gene_id_to_dicts.keys()))
        pprint.pprint(GF)
        L = GF["tmc6"]
    print ("loading", len(L))
    for feature in L:
        atts = feature["attribute"]
        kind = feature.get("feature")
        gene_id = atts.get("gene_id")
        if kind == "exon" and gene_id:
            name = gene_id + str(feature["start"])
            GB.add_feature(name, feature)
    svg = canvas.SVGCanvasWidget()
    GB.fit(svg)
    print ("drawing")
    GB.draw(svg)
    print ("done")
    return svg

    
