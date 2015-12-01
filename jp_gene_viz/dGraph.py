import numpy
import heapq
import json

from color_scale import (clr, clr_check, weighted_color, color)
import color_scale

def trim_leaves(Gin):
    Gout = WGraph()
    ew = Gin.edge_weights
    sources = set([a for (a,b) in ew])
    for e in ew:
        (a,b) = e
        if a in sources and b in sources:
            w = ew[e]
            Gout.add_edge(a, b, w)
    return Gout


def primary_influence(Gin, connect=False, connect_weight=1):
    Gout = WGraph()
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
    return Gout


def skeleton(Gin):
    ew = Gin.edge_weights
    nw = Gin.node_weights
    Gout = WGraph()
    neighbors = Gin.neighbors_dict()
    added = set()
    edges = sorted([(abs(ew[e]), e) for e in ew])
    while edges:
        (weight, next_edge) = edges.pop()
        (a, b) = next_edge
        if a not in added or b not in added:
            H = [(-weight, weight, e)]
            while H:
                #print H[0]
                (abs_weight, next_weight, next_e) = heapq.heappop(H)
                (a, b) = next_e
                if a not in added or b not in added:
                    for c in next_e:
                        for cn in neighbors[c]:
                            (cw, ce) = Gin.unordered_weight(c, cn)
                            heapq.heappush(H, (-abs(cw), cw, ce))
                    Gout.add_edge(a, b, ew[next_e])
                    added.add(a)
                    added.add(b)
    #Gout.node_weights = nw.copy()
    return Gout


class WGraph(object):
    
    def __init__(self):
        self.edge_weights = {}
        self.node_weights = {}
        self.edge_attributes = {}

    def clone(self):
        result = WGraph()
        result.edge_weights = self.edge_weights.copy()
        result.node_weights = self.node_weights.copy()
        # share edge attributes for now
        result.edge_attributes = self.edge_attributes
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

    positive_edge_color = clr(0, 211, 0)
    zero_edge_color = clr(230, 230, 230)
    negative_edge_color = clr(255, 0, 0)

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

    positive_node_color = clr(255, 100, 100)
    zero_node_color = clr(200, 200, 230)

    _node_color_interpolator = None

    def get_node_color_interpolator(self):
        result = self._node_color_interpolator
        if result is None:
            (_, _, Mv, mv) = self.weights_extrema()
            Mc = self.positive_node_color
            mc = self.zero_node_color
            result = color_scale.ColorInterpolator(mc, Mc, mv, Mv)
            #result.count_values(self.node_weights.values(), True)
            self._node_color_interpolator = result
        return result

    def reset_colorization(self):
        self._node_color_interpolator = None
        self._edge_color_interpolator = None

    def set_node_color_interpolator(self, color_interpolator):
        # probably should clone XXXX
        self._node_color_interpolator = color_interpolator
    
    def draw(self, canvas, positions, edgewidth=1, nodesize=3):
        (Me, me, Mn, mn) = self.weights_extrema()
        # layout edges
        ew = self.edge_weights
        # only layout positioned edges
        pos_e = [(abs(ew[e]), e) 
                 for e in ew if e[0] in positions and e[1] in positions]
        # "heavier" edges on top
        pos_e.sort()
        #print ("pos_e", pos_e)
        markradius = (edgewidth+1)/2
        outdegree = {}
        eci = self.get_edge_color_interpolator()
        for (absw, e) in pos_e:
            w = ew[e]
            (f, t) = e
            outdegree[f] = outdegree.get(f, 0) + 1
            fp = positions[f]
            tp = positions[t]
            n = towards(fp, tp)
            no = orthogonal(n)
            # shift positions so reverse edges don't overlap
            edgeshift = (edgewidth/2.0) * no
            # don't modify arrays in place
            fp = fp + edgeshift
            tp = tp + edgeshift
            #ecolor = self.edge_color(w, me, Me)
            ecolor = eci.interpolate_color(w)
            name = self.edge_name(f, t)  # "EDGE_" + json.dumps([f,t])
            canvas.line(name, fp[0], fp[1], tp[0], tp[1], ecolor, edgewidth)
            # add a mark to indicate target
            p = tp - (2 * nodesize) * n
            markname = "mark" + name
            if w>0:
                m = p - edgewidth * 5 * (n + no)
                canvas.line(markname, p[0], p[1], m[0], m[1], ecolor, edgewidth)
                #canvas.circle(None, m[0], m[1], markradius, pcolor)
            else:
                m = p - edgewidth * 5 * no
                canvas.line(markname, p[0], p[1], m[0], m[1], ecolor, edgewidth)
                #canvas.rect(None, m[0]-markradius, m[1]-markradius, 
                #            markradius*2, markradius*2, ncolor)
        # layout nodes (after edges)
        nw = self.node_weights
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
                degree = min(outdegree.get(n, 1) - 1, 4)
                canvas.circle(name, x, y, nodesize + degree, ncol) 
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
        canvas.set_view_box(originx, originy, dimension, dimension)
        #print ("canvas positioned at", (originx, originy))
        return pos(originx, originy)

    def edge_name(self, f, t):
        return "EDGE_" + json.dumps([f,t])

    def node_name(self, n):
        return "NODE_" + str(n)

    def move_node(self, canvas, positions, n, x, y):
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
    for i in xrange(len(a)):
        rowi = a[i]
        for j in xrange(len(rowi)):
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
