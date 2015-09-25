import numpy
import heapq
import json

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


def clr(r, g, b):
    result = numpy.array([r*1.0, g*1.0, b*1.0])
    clr_check(result)
    return result


    
def clr_check(clr):
    assert max(clr) < 256
    assert min(clr) >= 0


class WGraph(object):
    
    def __init__(self):
        self.edge_weights = {}
        self.node_weights = {}

    def clone(self):
        result = WGraph()
        result.edge_weights = self.edge_weights.copy()
        result.node_weights = self.node_weights.copy()
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
        
    def add_edge(self, from_node, to_node, weight):
        # ignore self edges (?)
        if from_node == to_node:
            return
        e = self.edge_weights
        n = self.node_weights
        e[(from_node, to_node)] = weight
        a = abs(weight)
        for node in (from_node, to_node):
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

    def edge_color(self, weight, min_weight, max_weight):
        if weight >= 0:
            return weighted_color(self.positive_edge_color, self.zero_edge_color,
                max_weight, weight)
        else:
            return weighted_color(self.negative_edge_color, self.zero_edge_color,
                abs(min_weight), abs(weight))

    positive_node_color = clr(255, 100, 100)
    zero_node_color = clr(200, 200, 230)

    def node_color(self, weight, max_weight):
        return weighted_color(self.positive_node_color, self.zero_node_color,
            max_weight, weight)
    
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
            ecolor = self.edge_color(w, me, Me)
            name = "EDGE_" + json.dumps([f,t])
            canvas.line(name, fp[0], fp[1], tp[0], tp[1], ecolor, edgewidth)
            # add a mark to indicate target
            p = tp - (2 * nodesize) * n
            if w>0:
                m = p - edgewidth * 5 * (n + no)
                canvas.line(None, p[0], p[1], m[0], m[1], ecolor, edgewidth)
                #canvas.circle(None, m[0], m[1], markradius, pcolor)
            else:
                m = p - edgewidth * 5 * no
                canvas.line(None, p[0], p[1], m[0], m[1], ecolor, edgewidth)
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
        for n in nw:
            if n in positions:
                p = positions[n]
                (x,y) = p
                minimum = numpy.minimum(minimum, p)
                maximum = numpy.maximum(maximum, p)
                w = nw[n]
                ncol = self.node_color(w, Mn)
                #ncol = weighted_color(pnode, znode, Mn, w)
                name = "NODE_" + str(n)
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

def weighted_color(maxclr, minclr, maxvalue, value):
    assert value <= maxvalue
    assert value >= 0
    if maxvalue==0:
        clr = minclr
    else:
        lm = value/float(maxvalue)
        clr = (lm * maxclr) + ((1 - lm) * minclr)
    return color(clr)

def color(clr):
    clr_check(clr)
    ints = map(int, clr)
    hexs = ["%02x" % x for x in ints]
    return "#" + "".join(hexs)

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
