

import traitlets
from jp_gene_viz import js_proxy
from jp_gene_viz import js_context
import numpy as np
import math


class ScatterPlot3D(traitlets.HasTraits):

    def __init__(self, *pargs, **kwargs):
        super(ScatterPlot3D, self).__init__(*pargs, **kwargs)
        js_context.load_if_not_loaded(["three_scatter.js"])
        js_context.load_if_not_loaded(["three_rotator.js"])
        js_context.load_if_not_loaded(["TextGeometry.js"])
        js_context.load_if_not_loaded(["three_simple_text.js"])
        js_proxy.load_javascript_support()
        self.series_list = []

    def add_series(self, marker, color, points, marker_size=None):
        series = Series3D()
        series.marker = marker
        series.color = color
        series.add_points(points)
        if marker_size is not None:
            series.marker_view_size = marker_size
        self.series_list.append(series)

    def plot(self, radius, widget, scene, marker_size=None, names=None):
        assert radius > 0
        if marker_size is None:
            marker_size = 0.01 * radius
        series_list = self.series_list
        assert len(series_list) > 0
        series0 = series_list[0]
        min_point = series0.min_point
        max_point = series0.max_point
        for series in self.series_list:
            min_point = np.minimum(min_point, series.min_point)
            max_point = np.maximum(max_point, series.max_point)
        view_scale_function = radius_scale(radius, min_point, max_point)
        for series in self.series_list:
            series.plot_points(view_scale_function, widget, scene, marker_size)
        if names:
            draw_axis_names(names, radius, widget, scene)

def draw_axis_names(names, radius, widget, scene, size=30):
    #return
    options = {
        "size": size,
        "height": size/20.0
    }
    THREE = widget.window().THREE
    x = y = z = - radius / 2.0
    (xname, yname, zname) = names
    pi2 = math.pi/2.0
    offset = size * 2
    widget(THREE.simple_text(xname, [x + offset, y, z], scene, [0, 0, 0], options))
    widget(THREE.simple_text(yname, [x, y + offset, z], scene, [0, 0, pi2], options))
    widget(THREE.simple_text(zname, [x, y, z + offset], scene, [0, -pi2, 0], options))

def radius_scale(radius, min_point, max_point, epsilon=0.001):
    """
    Scale x,y,z so points fit into box centered at origin with radius.
    """
    diff = np.abs(max_point - min_point)
    scale = radius * 1.0/(diff + epsilon)
    offset = min_point + 0.5 * diff
    def scale_function(point):
        return scale * (point - offset)
    return scale_function


class Series3D(traitlets.HasTraits):

    marker = "star"

    marker_view_size = None

    color = 0xff0000

    max_point = None

    min_point = None

    def __init__(self, *pargs, **kwargs):
        super(Series3D, self).__init__(*pargs, **kwargs)
        self.points = []

    def add_points(self, points):
        for p in points:
            p = np.array(p)
            if self.max_point is None:
                self.max_point = self.min_point = p
            else:
                self.max_point = np.maximum(self.max_point, p)
                self.min_point = np.minimum(self.min_point, p)
            self.points.append(p)

    def plot_points(self, view_scale_function, widget, scene, marker_size=None):
        marker_size1 = self.marker_view_size
        if marker_size1 is None:
            marker_size1 = marker_size
        if marker_size1 is None:
            marker_size1 = 1
        scaled_points = [view_scale_function(p).tolist() for p in self.points]
        three = widget.window().THREE
        #print "marker size", marker_size1
        widget(three.scatter(scene, self.marker, scaled_points, marker_size1, self.color))

def xyz_dict(x, y, z):
    return {"x": x, "y": y, "z": z}

def test_plot(with_box=False, with_rotator=True):
    from IPython import display
    import math
    sp = ScatterPlot3D()
    points1 = [(400+math.sin(i*2), math.cos(i*3)*1.5, math.sin(i*0.5)) for i in range(150)]
    sp.add_series("star", 0xff0000, points1)
    points2 = [(401+math.sin(i), math.cos(i*2), math.sin(i*1.5)*1.7) for i in range(150)]
    sp.add_series("openCube", 0xffff00, points2)
    w = js_proxy.ProxyWidget()
    window = w.window()
    element = w.element()
    THREE = window.THREE
    new = w.save_new
    scene = new("scene", THREE.Scene, [])
    camera = new("camera", THREE.PerspectiveCamera, [75, 1.0, 1, 10000])
    w(camera.position._set("z", 500))
    # plot the scatter points
    sp.plot(300, w, scene, 10)
    if with_box:
        geometry = new("geometry", THREE.BoxGeometry, [200, 200, 200])
        #geometry = new("geometry", THREE.TetrahedronGeometry, [])
        material = new("material", THREE.MeshBasicMaterial, [{"color": 0xff00ee, "wireframe": True } ])
        mesh = new("mesh", THREE.Mesh, [geometry, material])
        w(scene.add(mesh))
    renderer = new("renderer", THREE.WebGLRenderer, [])
    w(renderer.setSize(800, 800))
    w(element.append(renderer.domElement))
    do_render = w(renderer.render(scene, camera))
    if with_rotator:
        gamma = xyz_dict(0, 0, 1)
        delta = xyz_dict(1, 0, 0)
        radius = 300
        w(THREE.rotator(gamma, delta, radius, camera, renderer, scene))
    json_sent = w.flush()
    display.display(w)
    return w