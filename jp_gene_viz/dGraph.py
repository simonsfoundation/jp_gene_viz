import numpy
import heapq
import json

from jp_gene_viz.color_scale import (clr, clr_check, weighted_color, color)
from jp_gene_viz import color_scale
from jp_gene_viz.json_mixin import JsonMixin
from jp_gene_viz import grid_forest
from jp_svg_canvas import canvas as svg_canvas


def trim_leaves(Gin):
    #Gout = WGraph()
    Gout = Gin.same_colors()
    ew = Gin.edge_weights
    sources = set([a for (a,b) in ew])
    for e in ew:
        (a,b) = e
        if a in sources and b in sources:
            w = ew[e]
            Gout.add_edge(a, b, w)
    return Gout


def primary_influence(Gin, connect=False, connect_weight=1):
    #Gout = WGraph()
    Gout = Gin.same_colors()
    nw = Gin.node_weights
    ew = Gin.edge_weights
    influences = {}
    influencers = {}
    for e in ew:
        w = ew[e]
        (f, t) = e
        for (a,b) in ((f,t), (t,f)):
            influence = influences.get(b)
            if influence is None or abs(influence) < abs(w):
                influences[b] = w
                influencers[b] = a
    for a in influences:
        b = influencers[a]
        w = influences[b]
        Gout.add_edge(b, a, w)
    if connect:
        influenced = {}
        for a in influences:
            b = influencers[a]
            bset = influenced.setdefault(b, set())
            bset.add(a)
        for bset in influenced.values():
            if len(bset) > 1:
                blist = sorted(bset)
                last = first = None
                for current in blist:
                    if first is None:
                        last = first = current
                    else:
                        Gout.add_edge(last, current, connect_weight)
                        last = current
                Gout.add_edge(last, first, connect_weight)
    # preserve all nodes
    Gout.node_weights = nw.copy()
    return Gout

#skeleton = primary_influence

def skeleton(Gin):
    """
    Maximal spanning forest of Gin (?)
    """
    visited_edges = set()
    ew = Gin.edge_weights
    #nw = Gin.node_weights
    # "skeleton in", len(ew), len(nw)
    Gout = WGraph()
    # preserve all nodes.
    Gout.node_weights = Gin.node_weights.copy()
    neighbors = Gin.neighbors_dict()
    added = set()
    edges = sorted([(abs(ew[e]), e) for e in ew])
    #count = 0
    limit = len(ew)
    while edges:
        next_edge = None
        (weight, next_edge) = edges.pop()
        (a, b) = next_edge
        if a not in added or b not in added:
            H = [(-weight, weight, e)]
            #Gout.add_edge(a, b, ew[next_e])
            while H:
                #print "H", H
                #print "added", added
                (abs_weight, next_weight, next_e) = heapq.heappop(H)
                assert len(H) < limit, repr((len(H), limit))
                (a, b) = next_e
                if a not in added or b not in added:
                    #visited_edges.add(next_e)
                    for c in next_e:
                        for cn in neighbors[c]:
                            (cw, ce) = Gin.unordered_weight(c, cn)
                            if ce not in visited_edges:
                                heapq.heappush(H, (-abs(cw), cw, ce))
                                visited_edges.add(ce)
                    Gout.add_edge(a, b, ew[next_e])
                    added.add(a)
                    added.add(b)
    #Gout.node_weights = nw.copy()
    return Gout


class edgeDictConverter(object):

    @staticmethod
    def to_json_value(adict):
        return list(adict.items())

    @staticmethod
    def from_json_value(alist):
        return dict((tuple(key), value) for (key, value) in alist)


class WGraph(JsonMixin):

    arrow_ratio = 0.75  # how far down an arc to position an arrowhead mark
    
    def __init__(self, node_color_interpolator=None, edge_color_interpolator=None):
        self.edge_weights = {}
        self.node_weights = {}
        self.node_radius = {}
        self.edge_attributes = {}
        # populate on demand
        self._node_to_descendents = None
        self._edge_color_interpolator = edge_color_interpolator
        self._node_color_interpolator = node_color_interpolator

    def same_colors(self):
        return WGraph(self._node_color_interpolator, self._edge_color_interpolator)

    json_atts = ["node_weights"]
    json_objects = {
        "edge_weights": edgeDictConverter,
        "edge_attributes": edgeDictConverter,
        "_node_color_interpolator": color_scale.ColorInterpolator, 
        "_edge_color_interpolator": color_scale.ColorInterpolator,
        }

    def uncache(self):
        "clear all caching data structures (for safety)."
        self._node_to_descendents = None

    def get_node_to_descendants(self):
        result = self._node_to_descendents
        if result is None:
            result = {}
            for (f, t) in self.edge_weights.keys():
                result.setdefault(f, set()).add(t)
            self._node_to_descendents = result
        return result

    def clone(self):
        result = WGraph()
        result.edge_weights = self.edge_weights.copy()
        result.node_weights = self.node_weights.copy()
        result.node_radius = self.node_radius.copy()
        # share edge attributes for now
        result.edge_attributes = self.edge_attributes
        result.reset_colorization(self)
        return result
        
    def unordered_weight(self, a, b):
        ew = self.edge_weights
        for e in ((a,b), (b,a)):
            if e in ew:
                return (ew[e], e)
        return None
        
    def neighbors_dict(self):
        result = {}
        ew = self.edge_weights
        for e in ew:
            (f, t) = e
            for (a, b) in (e, (t, f)):
                aset = result.setdefault(a, set())
                aset.add(b)
        return result
        
    def sizes(self):
        return (len(self.edge_weights), len(self.node_weights))
        
    def add_edge(self, from_node, to_node, weight, attributes=None):
        # reset descendants structure
        self._node_to_descendents = None
        # ignore self edges (?)
        if from_node == to_node:
            return
        if attributes is None:
            attributes = {}
        e = self.edge_weights
        n = self.node_weights
        edge = (from_node, to_node)
        # add the edge
        e[edge] = weight
        # extend or add attributes
        atts = self.edge_attributes.get(edge, {})
        atts.update(attributes)
        self.edge_attributes[edge] = atts
        a = abs(weight)
        for node in edge:
            n[node] = n.get(node, 0) + a
            
    def weights_extrema(self):
        ew = self.edge_weights.values()
        nw = self.node_weights.values()
        mn = Mn = me = Me = 0
        if ew:
            me = min(ew)
            Me = max(ew)
        if nw:
            mn = min(nw)
            Mn = max(nw)
        return (Me, me, Mn, mn)

    positive_edge_color = color_scale.medRed
    zero_edge_color = color_scale.lightGrey
    negative_edge_color = color_scale.medBlue

    _edge_color_interpolator = None

    def get_edge_color_interpolator(self):
        result = self._edge_color_interpolator
        if result is None:
            (Mv, mv, _, _) = self.weights_extrema()
            mc = self.negative_edge_color
            Mc = self.positive_edge_color
            result = color_scale.ColorInterpolator(mc, Mc, mv, Mv)
            if mv < 0 and Mv > 0:
                result.add_color(0, self.zero_edge_color)
            #result.count_values(self.edge_weights.values(), True)
            self._edge_color_interpolator = result
        return result

    positive_node_color = color_scale.medRed
    zero_node_color = color_scale.lightGrey
    negative_node_color = color_scale.medBlue

    _node_color_interpolator = None

    def get_node_color_interpolator(self):
        result = self._node_color_interpolator
        if result is None:
            (_, _, Mv, mv) = self.weights_extrema()
            Mc = self.positive_node_color
            mc = self.negative_node_color
            result = color_scale.ColorInterpolator(mc, Mc, mv, Mv)
            if mv < 0 and Mv > 0:
                result.add_color(0, self.zero_node_color)
            #result.count_values(self.node_weights.values(), True)
            self._node_color_interpolator = result
        return result

    def reset_colorization(self, fromGraph=None):
        if fromGraph is None:
            self._node_color_interpolator = None
            self._edge_color_interpolator = None
        else:
            self._node_color_interpolator = fromGraph._node_color_interpolator
            self._edge_color_interpolator = fromGraph._edge_color_interpolator

    def set_node_color_interpolator(self, color_interpolator):
        # probably should clone XXXX
        self._node_color_interpolator = color_interpolator
    
    def draw(self, canvas, positions, edgewidth=1, nodesize=3, fit=True, styling_overrides=None, send=True):
        import dNetwork
        if styling_overrides is None:
            styling_overrides = dNetwork.StylingOverrides(None)
        (Me, me, Mn, mn) = self.weights_extrema()
        # layout edges
        ew = self.edge_weights
        ea = self.edge_attributes
        # only layout positioned edges
        pos_e = [(abs(ew[e]), e) 
                 for e in ew if e[0] in positions and e[1] in positions]
        # "heavier" edges on top
        pos_e.sort()
        #print ("pos_e", pos_e)
        #markradius = (edgewidth+1)/2
        outdegree = {}
        eci = self.get_edge_color_interpolator()
        arrow_ratio = self.arrow_ratio
        for (absw, e) in pos_e:
            w = ew[e]
            a = ea[e] or {}
            (f, t) = e
            name = self.edge_name(f, t)  # "EDGE_" + json.dumps([f,t])
            edge_overrides = styling_overrides.get_overrides(name)
            other_atts = {}
            for att in svg_canvas.STROKE_ATTRIBUTES:
                value = edge_overrides.get(att) or a.get(att)
                if value and str(value).upper()!="NONE":
                    other_atts[att] = value
            outdegree[f] = outdegree.get(f, 0) + 1
            fp = positions[f]
            tp = positions[t]
            n = towards(fp, tp)
            d = distance(fp, tp)
            no = orthogonal(n)
            # shift positions so reverse edges don't overlap
            edgeshift = (edgewidth/2.0) * no
            # don't modify arrays in place
            fp = fp + edgeshift
            tp = tp + edgeshift
            #ecolor = self.edge_color(w, me, Me)
            ecolor = eci.interpolate_color(w)
            #name = self.edge_name(f, t)  # "EDGE_" + json.dumps([f,t])
            #ecolor = color_overrides.get(name, ecolor)
            ecolor = edge_overrides.get("color", ecolor)
            canvas.line(name, fp[0], fp[1], tp[0], tp[1], ecolor, edgewidth, **other_atts)
            # add a mark to indicate target
            #p = tp - (2 * nodesize) * n
            p = fp + arrow_ratio * (tp - fp)
            markname = "mark" + name
            if w>0:
                m = p - edgewidth * 5 * (n + no)
                canvas.line(markname, p[0], p[1], m[0], m[1], ecolor, edgewidth, **other_atts)
                #canvas.circle(None, m[0], m[1], markradius, pcolor)
            else:
                m = p - edgewidth * 5 * no
                canvas.line(markname, p[0], p[1], m[0], m[1], ecolor, edgewidth, **other_atts)
                #canvas.rect(None, m[0]-markradius, m[1]-markradius, 
                #            markradius*2, markradius*2, ncolor)
        # layout nodes (after edges)
        nw = self.node_weights
        node_radius = self.node_radius
        if not nw:
            return
        pos_n = [(nw[n], n) for n in self.node_weights if n in positions]
        pos_n.sort()
        example_pos = positions[pos_n[0][1]]
        # keep track of min/max position in order to adjust view box later to include all nodes.
        minimum = maximum = example_pos
        nci = self.get_node_color_interpolator()
        for n in nw:
            if n in positions:
                p = positions[n]
                (x,y) = p
                minimum = numpy.minimum(minimum, p)
                maximum = numpy.maximum(maximum, p)
                w = nw[n]
                #ncol = self.node_color(w, Mn)
                #ncol = weighted_color(pnode, znode, Mn, w)
                ncol = nci.interpolate_color(w)
                name = self.node_name(n)  # "NODE_" + str(n) 
                node_overrides = styling_overrides.get_overrides(name)
                #ncol = color_overrides.get(name, ncol)
                ncol = node_overrides.get("color", ncol)
                degree = min(outdegree.get(n, 1) - 1, 4)
                radius = nodesize + degree
                # use node radius override if defined for this node
                #radius = node_radius.get(n, radius)
                radius = node_overrides.get("radius", radius)
                shape = "circle"
                if n in outdegree:
                    shape = "rect"
                shape = node_overrides.get("shape", shape)
                if shape=="rect":
                    canvas.rect(name, x-radius, y-radius, 2*radius, 2*radius, ncol)
                else:
                    assert shape=="circle"
                    canvas.circle(name, x, y, radius, ncol) 
        if send:
            canvas.send_commands()
        # adjust the viewBox
        (minx, miny) = map(int, minimum)
        (maxx, maxy) = map(int, maximum)
        width = maxx-minx+20
        height = maxy-miny+20
        #view_scale = 500.0/max(height, 1)
        dimension = max(width, height)
        #view_scale = 500.0/max(dimension, 1)
        #canvas.width = int(width * view_scale)
        #canvas.height = int(height * view_scale)
        (originx, originy) = (minx-10, miny-10)
        if fit:
            canvas.set_view_box(originx, originy, dimension, dimension)
        #print ("canvas positioned at", (originx, originy))
        return pos(originx, originy)

    def edge_name(self, f, t):
        return "EDGE_" + json.dumps([f,t])

    def node_name(self, n):
        return "NODE_" + str(n)

    def descendant_set(self, n, level, accumulator=None):
        if accumulator is None:
            accumulator = set()
        if n not in accumulator:
            accumulator.add(n)
            if level is None or level > 0:
                next_level = None
                if level is not None:
                    next_level = level - 1
                n2d = self.get_node_to_descendants()
                descendants = n2d.get(n, ())
                for d in descendants:
                    self.descendant_set(d, next_level, accumulator)
        return accumulator

    def move_descendants(self, canvas, positions, n, x, y, depth=0, add_edges=True):
        descendants = self.descendant_set(n, int(depth))
        offset = pos(x, y) - positions[n]
        for d in descendants:
            positions[d] = positions[d] + offset
        # move edges attached to descendants
        if add_edges:
            for (f, t) in self.edge_weights:
                for (n0, xname, yname) in ((f, "x1", "y1"), (t, "x2", "y2")):
                    if n0 in descendants:
                        (x0, y0) = positions[n0]
                        name0 = self.edge_name(f, t)
                        markname = "mark" + name0
                        attributes = {xname: x0, yname: y0}
                        canvas.change_element(name0, attributes)
                        canvas.delete_names([markname])
        # move the nodes
        for d in descendants:
            (xd, yd) = positions[d]
            dname = self.node_name(d)
            attributes = {"cx": xd, "cy": yd, "x": xd, "y": yd}
            canvas.change_element(dname, attributes)
        canvas.send_commands()

    def move_node(self, canvas, positions, n, x, y):
        # deprecate in favor of move_descendents?
        positions[n] = pos(x, y)
        ew = self.edge_weights
        for (f, t) in ew:
            if f == n:
                # move x1 y1 for edge
                name = self.edge_name(f, t)
                markname = "mark" + name
                attributes = {}
                attributes["x1"] = x
                attributes["y1"] = y
                canvas.change_element(name, attributes)
                canvas.delete_names([markname])
            elif t == n:
                # move x2 y2 for edge
                name = self.edge_name(f, t)
                markname = "mark" + name
                attributes = {}
                attributes["x2"] = x
                attributes["y2"] = y
                canvas.change_element(name, attributes)
                canvas.delete_names([markname])
        name = self.node_name(n)
        attributes = {}
        attributes["cx"] = x
        attributes["cy"] = y
        attributes["x"] = x
        attributes["y"] = y
        canvas.change_element(name, attributes)
        canvas.send_commands()


def draw_heat_map(canvas, a, dx, dy):
    lowclr = clr(200, 255, 255)
    highclr = clr(255, 200, 0)
    maxval = numpy.max(a)
    minval = numpy.min(a)
    diff = maxval - minval
    if diff<0.1:
        return
    for i in range(len(a)):
        rowi = a[i]
        for j in range(len(rowi)):
            val = rowi[j]
            intensity = (val - minval)/diff
            iclr = (1-intensity)*lowclr + intensity*highclr
            canvas.rect(None, i*dx, j*dy, dx, dy, color(iclr))
    canvas.send_commands()
            

def pos(x, y):
    return numpy.array([x*1.0, y*1.0])


def towards(a, b, nonzero=True):
    diff = b - a
    norm = numpy.linalg.norm(diff)
    if norm < 0.01:
        if nonzero:
            # arbitrary
            return numpy.array([1,1])
        else:
            return numpy.array([0,0])
    return diff/norm


def orthogonal(v):
    [x,y] = v
    return pos(-y, x)


def distance(a,b):
    return numpy.linalg.norm(b-a)
