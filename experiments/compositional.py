"""
Experiments in compositional geometry (Aitchison geometry).
"""

import numpy as np
import math
import traitlets
from jp_gene_viz import js_proxy
import traitlets
import ipywidgets as widgets
from IPython.display import display

#display(HTML(load_three))
from jp_gene_viz import js_context

js_context.load_if_not_loaded(["three.js"])
js_context.load_if_not_loaded(["three_curve.js"])
js_proxy.load_javascript_support()

def closure(vector):
    return vector / (1.0*vector.sum(0))

def strictly_positive(vectors):
    return vectors[(vectors > 0).all(1)]

def closures(vectors):
    vectors = strictly_positive(vectors)
    (n,d) = vectors.shape
    sums = 1.0 * vectors.sum(1).reshape(n, 1)
    return vectors / sums

def clr(vector):
    (d,) = vector.shape
    product_root = vector.prod(0) ** (1.0/d)
    return np.log(vector / product_root)

def invclr(vector):
    return closure(np.exp(vector))

def clrs(vectors):
    "clr where vectors with zero components are dropped."
    vectors = strictly_positive(vectors)
    (n, d) = vectors.shape
    product_roots0 = (vectors.prod(1) ** (1.0/d))
    not_zeros = (product_roots0 > 0)
    nz_product_roots = product_roots0[not_zeros]
    nz_vectors = vectors[not_zeros]
    nz = len(nz_product_roots)
    return np.log(nz_vectors / nz_product_roots.reshape(nz, 1))

def invclrs(vectors):
    return closures(np.exp(vectors))

def xpoints3d(xmin, xmax, num, y, z):
    xs = np.linspace(xmin, xmax, num)
    result = np.zeros((num, 3))
    result[:, 0] = xs
    result[:, 1] = y
    result[:, 2] = z
    return result

def ypoints3d(ymin, ymax, num, x, z):
    result = xpoints3d(ymin, ymax, num, x, z)
    ys = np.array(result[:, 0]).copy()
    result[:, 0] = x
    result[:, 1] = ys
    result[:, 2] = z
    return result

def xyrotations(points, angle):
    result = points.copy()
    xs = points[:, 0]
    ys = points[:, 1]
    cosa = np.cos(angle)
    sina = np.sin(angle)
    result[:, 0] = xs * cosa - ys * sina
    result[:, 1] = ys * cosa + xs * sina
    return result

def xzrotations(points, angle):
    result = points.copy()
    xs = points[:, 0]
    zs = points[:, 2]
    cosa = np.cos(angle)
    sina = np.sin(angle)
    result[:, 0] = xs * cosa - zs * sina
    result[:, 2] = zs * cosa + xs * sina
    return result

def yzrotations(points, angle):
    result = points.copy()
    ys = points[:, 1]
    zs = points[:, 2]
    cosa = np.cos(angle)
    sina = np.sin(angle)
    result[:, 1] = ys * cosa - zs * sina
    result[:, 2] = zs * cosa + ys * sina
    return result

def xygridlines(minimum, maximum, nlines, npoints, z):
    result = []
    dlines = (maximum - minimum) * 1.0/nlines
    for i in range(nlines):
        w = i * dlines + minimum
        xp = xpoints3d(minimum, maximum, npoints, w, z)
        yp = ypoints3d(minimum, maximum, npoints, w, z)
        result.append(xp)
        result.append(yp)
    return result

def great_circles(offset, radius, n=100):
    angles = np.linspace(0, 2 * math.pi, n)
    sines = offset + radius * np.sin(angles)
    cosines = offset + radius * np.cos(angles)
    result = []
    for (i, j) in [(0, 1), (1, 2), (2, 0)]:
        a = np.zeros((n, 3))
        a[:] = offset
        a[:, i] = sines
        a[:, j] = cosines
        result.append(a)
    return result

def globe(offset, radius, n=50, m=8):
    result = []
    angles = np.linspace(0, 2*math.pi, n)
    sines = np.sin(angles)
    cosines = np.cos(angles)
    zangles = np.linspace(0, math.pi, m+2)
    for zangle in zangles[1:-1]:
        z = math.cos(zangle) * radius + offset
        subradius = radius * math.sin(zangle)
        a = np.zeros((n, 3))
        a[:, 2] = z
        a[:, 0] = subradius * sines + offset
        a[:, 1] = subradius * cosines + offset
        result.append(a)
    return result

# A subspace basis for hyperplane x+y+z+w = 0
basis = np.array([
        (1, 0, 0, -1),
        (0, 1, -1, 0),
        (0.5, -0.5, -0.5, 0.5)
    ])

inv_basis = np.linalg.inv(basis[:, :-1])

def to4d(vectors3d):
    "project 3d vectors onto hyperplane x+y+z+w=0"
    return vectors3d.dot(basis)

def to3d(hyperplane_vectors4d):
    "reverse project hyperplane vectors to 3d"
    return hyperplane_vectors4d[:, :-1].dot(inv_basis)

class Diagram(traitlets.HasTraits):

    cleanup = None
    do_draw = True

    xy_rotation = traitlets.Float(0)
    xz_rotation = traitlets.Float(0)
    yz_rotation = traitlets.Float(0)
    offset = traitlets.Float(4.0)
    max_angle = traitlets.Float(0.4)
    delta_angle = traitlets.Float(0.02)

    def __init__(self, *args, **kwargs):
        super(Diagram, self).__init__(*args, **kwargs)
        mx = self.max_angle * 2
        d = self.diagram = js_proxy.ProxyWidget()
        xy = self.xy_slider = widgets.FloatSlider(
            description="XY rotation", min=-mx, max=mx)
        xz = self.xy_slider = widgets.FloatSlider(
            description="XZ rotation", min=-mx, max=mx)
        yz = self.xy_slider = widgets.FloatSlider(
            description="YZ rotation", min=-mx, max=mx)
        traitlets.link((self, "xy_rotation"), (xy, "value"))
        traitlets.link((self, "xz_rotation"), (xz, "value"))
        traitlets.link((self, "yz_rotation"), (yz, "value"))
        self.on_trait_change(self.draw_diagram, "xy_rotation")
        self.on_trait_change(self.draw_diagram, "xz_rotation")
        self.on_trait_change(self.draw_diagram, "yz_rotation")
        self.assembly = widgets.VBox(children=[xy, xz, yz, d])

    def show(self):
        self.draw_diagram()
        display(self.assembly)

    def loop_animation(self):
        import time
        theta = 0
        while True:
            theta += self.delta_angle
            mx = self.max_angle
            self.do_draw = False
            self.xz_rotation = np.cos(theta)*mx
            self.xy_rotation = np.sin(theta*1.1)*mx
            self.do_draw = True
            self.yz_rotation = np.sin(theta*0.4)*mx
            time.sleep(0.1)

    def draw_simplex(self, d, scene, THREE):
        last = [0, 0, 1]
        origin = [0, 0, 0]
        for next in [[1, 0, 0], [0, 1, 0], [0, 0, 1]]:
            d(THREE.simple_curve(scene, [origin, next], 0xdddddd))
            d(THREE.simple_curve(scene, [last, next], 0xff0000))
            last = next

    def draw_diagram(self):
        if not self.do_draw:
            return
        if self.cleanup:
            self.cleanup()
        d = self.diagram
        element = d.element()
        window = d.window()
        THREE = window.THREE
        new = d.save_new
        scene = new("scene", THREE.Scene, [])
        camera = new("camera", THREE.PerspectiveCamera, [55, 1.0, 1, 100000])
        offset = self.offset
        d(camera.position._set("x", offset*2/3.)._set("y", offset)._set("z", offset*3/2.))
        d(camera.lookAt(scene.position))
        renderer = new("renderer", THREE.WebGLRenderer, [])
        d(renderer.setSize(800, 800))
        d(element.append(renderer.domElement))
        # Draw the diagram
        self.draw_simplex(d, scene, THREE)
        #lines = xygridlines(0.1, 1.5, 10, 20, 1.5)
        #lines = great_circles(1.2, 1.1)
        self.draw_curves(d, scene, THREE)
        d(renderer.render(scene, camera))
        d.flush()
        def cleanup():
            "three.js cleanup -- finalize the scene, etcetera"
            d(THREE.simple_curve.dispose_all(scene))
            d(element.empty())
            #d.flush()
        # defint a cleanup action
        self.cleanup = cleanup

    def draw_curves(self, d, scene, THREE):
        lines = globe(2, 1)
        for line in lines:
            line = xzrotations(line, self.xz_rotation)
            line = xyrotations(line, self.xy_rotation)
            line = yzrotations(line, self.yz_rotation)
            line = strictly_positive(line)
            curve = line.tolist()
            d(THREE.simple_curve(scene, curve, 0xffffff))
            cline = closures(line)
            curve = cline.tolist()
            d(THREE.simple_curve(scene, curve, 0x55ff55))
            ccline = clrs(line)
            curve = ccline.tolist()
            d(THREE.simple_curve(scene, curve, 0x55aaaa))

class InvDiagram(Diagram):
    
    offset = traitlets.Float(2.0)
    max_angle = traitlets.Float(6.0)

    def draw_curves(self, d, scene, THREE):
        lines = globe(1, 0.5)
        for line in lines:
            line = xzrotations(line, self.xz_rotation)
            line = xyrotations(line, self.xy_rotation)
            line = yzrotations(line, self.yz_rotation)
            curve = line.tolist()
            d(THREE.simple_curve(scene, curve, 0x55aaaa))
            line4 = to4d(line)
            lineinv = invclrs(line4)
            #line3 = to3d(lineinv)
            line3 = lineinv[:, :-1]  # just throw out the last dimension...
            curve = line3.tolist()
            d(THREE.simple_curve(scene, curve, 0x55ff55))

