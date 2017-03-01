"""
Quick helper for creating 3d diagrams with orbit controls in Jupyter
"""

from jp_gene_viz import js_context
from jp_gene_viz import js_proxy
import numpy as np
from numpy.linalg import norm
from ipywidgets import widgets
import traitlets
from IPython.display import display


def parameterized_points_1d(f, min_t, max_t, npoints):
    t_values = np.linspace(min_t, max_t, npoints)
    return np.array([f(t) for t in t_values], dtype=np.float)

def parameterized_points_2d(f, mins, maxes, counts):
    "generate 2d array of triples using f(u,v) --> (x, y, z)"
    (umin, vmin) = mins
    (umax, vmax) = maxes
    (ucount, vcount) = counts
    u_values = np.linspace(umin, umax, ucount)
    v_values = np.linspace(vmin, vmax, vcount)
    ur = range(ucount)
    vr = range(vcount)
    result = np.zeros((ucount, vcount, 3))
    for i in ur:
        u = u_values[i]
        for j in vr:
            v = v_values[j]
            result[i, j] = f(u, v)
    return result

def parameterized_points_3d(f, mins, maxes, counts):
    "generate 2d array of triples using f(u,v) --> (x, y, z)"
    (umin, vmin, wmin) = mins
    (umax, vmax, wmax) = maxes
    (ucount, vcount, wcount) = counts
    u_values = np.linspace(umin, umax, ucount)
    v_values = np.linspace(vmin, vmax, vcount)
    w_values = np.linspace(wmin, wmax, wcount)
    ur = list(range(ucount))
    vr = list(range(vcount))
    wr = list(range(wcount))
    result = np.zeros((ucount, vcount, wcount, 4))
    for i in ur:
        u = u_values[i]
        for j in vr:
            v = v_values[j]
            for k in wr:
                w = w_values[k]
                result[i, j, k] = f(u, v, w)
    return result

def triangulate_2d_points(array):
    "generate list of points and triangulations from array of triples."
    (u_count, v_count, dimension) = array.shape
    assert dimension == 3
    npoints = u_count * v_count
    points = [None] * npoints
    def point_ravel(i, j):
        return i + (u_count * j)
    for i in range(u_count):
        for j in range(v_count):
            ij = point_ravel(i, j)
            assert points[ij] is None
            points[ij] = array[i,j]
    # assert None not in points
    ntriangles = 2 * (u_count - 1) * (v_count - 1)
    triangles = set()
    for i in range(u_count - 1):
        for j in range(v_count - 1):
            a = point_ravel(i, j)
            b = point_ravel(i, j+1)
            c = point_ravel(i+1, j+1)
            d = point_ravel(i+1, j)
            assert max(a, b, c, d) < npoints
            triangles.add((a, b, d))
            triangles.add((d, b, c))
    assert len(triangles) == ntriangles
    return (points, list(triangles))

def triangulate_3d_points(array):
    "generate list of points and triangulations from array of triples."
    (u_count, v_count, w_count, dimension) = array.shape
    assert dimension == 4
    npoints = u_count * v_count * w_count
    points = [None] * npoints
    def point_ravel(i, j, k):
        return i + (u_count * (j + (v_count * k)))
    for i in range(u_count):
        for j in range(v_count):
            for k in range(w_count):
                ijk = point_ravel(i, j, k)
                assert points[ijk] is None
                points[ijk] = array[i,j,k]
    #assert None not in points
    ntriangles = 2 * (u_count - 1) * (v_count - 1) * (w_count - 1)
    #segments = [(point_ravel(i,j,k), point_ravel(i,j,k+1))
    #    for i in range(u_count)
    #    for j in range(v_count)
    #    for k in range(w_count - 1)]
    segments = [None] * (u_count * v_count * (w_count - 1))
    for i in range(u_count):
        for j in range(v_count):
            for k in range(w_count - 1):
                ijk = point_ravel(i, j, k)
                assert segments[ijk] is None
                segments[ijk] = (ijk, point_ravel(i,j,k+1))
    assert None not in segments
    triangles = set()
    for i in range(u_count - 1):
        for j in range(v_count - 1):
            for k in range(w_count - 1):
                a = point_ravel(i, j, k)
                b = point_ravel(i, j+1, k)
                c = point_ravel(i+1, j+1, k)
                d = point_ravel(i+1, j, k)
                assert max(a, b, c, d) < npoints
                triangles.add((a, b, d))
                triangles.add((d, b, c))
    assert len(triangles) == ntriangles
    return (points, segments, list(triangles))

JS_LIBRARIES = [
    ("three.js", "THREE"),
    ("FontUtils.js", "THREE.FontUtils"),
    ("helvetiker_regular.typeface.js", "_typeface_js.faces['helvetiker']"),
    ("three_scatter.js", "THREE.scatter"),
    ("three_rotator.js", "THREE.rotator"),
    ("three_orbit.js", "THREE.orbiter"),
    ("three_curve.js", "THREE.simple_curve"),
    ("three_triangles.js", "THREE.triangle_surface"),
    ("morph_triangles.js", "THREE.morph_triangles"),
    ("TextGeometry.js", "THREE.TextGeometry"),
    ("three_simple_text.js", "THREE.simple_text"),
    ("three_sprite_text.js", "THREE.sprite_text"),
    ("OrbitControls.js", "THREE.OrbitControls"),
]

def init():
    for (library, dependency) in JS_LIBRARIES:
        js_context.load_if_not_loaded([library], local=False)
    js_proxy.load_javascript_support()

RAWGIT = "https://rawgit.com/simonsfoundation/jp_gene_viz/master/jp_gene_viz/"

def js_includes(baseurl=RAWGIT, libraries=JS_LIBRARIES):
    L = ['<script src="%s"></script>' % (baseurl + library) for (library, dependency) in libraries]
    return "\n".join(L)

class Doodle3D(object):

    def __init__(self, width=500, height=500, autoRotate=False, center=(0,0,0), offset=100):
        init()
        w = self.w = js_proxy.ProxyWidget()
        element = self.element = w.element()
        window = self.window = w.window()
        THREE = self.THREE = window.THREE
        self.center = center
        self.offset = offset
        self.autoRotate = autoRotate
        scene = self.scene = w.save_new("scene", THREE.Scene, [])
        renderer = self.renderer = w.save_new("renderer", THREE.WebGLRenderer, [])
        w(renderer.setSize(width, height))
        w(renderer.setClearColor( 0xffffff, 1))
        w(element.append(renderer.domElement))

    def as_html_page(self, filepath, title='HTML Doodle', div_id="OUTPUT_3D"):
        self.prepare_renderer()
        L = []
        a = L.append
        a("<html>")
        a("<head>")
        a("<title> %s </title>" % title)
        a('<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>')
        a(js_includes())
        a("</head>")
        a("<body>")
        a('<div id="%s"></div>' % div_id)
        a('<script type="text/javascript">')
        a(self.javascript_string(div_id=div_id))
        a('</script>')
        a("</body>")
        a("</html>")
        html = "\n".join(L)
        out = open(filepath, "w")
        out.write(html)

    def javascript_string(self, debugger=False, div_id=None):
        await = [dependency for (library, dependency) in JS_LIBRARIES]
        await += ["jQuery"]
        return self.w.embedded_javascript(debugger, await, div_id=div_id)

    def light(self, color, x, y, z):
        w = self.w
        THREE = self.THREE  
        new_light = w.save_new("light", THREE.DirectionalLight, [color])
        w(new_light.position.set(x, y, z))
        w(self.scene.add(new_light))

    #def text(self, text, position, rotation):
    #    w = self.w
    #    THREE = self.THREE
    #    w(THREE.simple_text(text, location, self.scene, location))

    def curve(self, color, points):
        points = list(map(list, points))
        w = self.w
        THREE = self.THREE
        w(THREE.simple_curve(self.scene, points, color))

    def parameterized_curve(self, color, f, min_t, max_t, npoints):
        points = parameterized_points_1d(f, min_t, max_t, npoints)
        return self.curve(color, points)

    def parameterized_surface(self, f, mins, maxes, counts, color, kind="solid", opacity=None):
        A = parameterized_points_2d(f, mins, maxes, counts)
        (points, indices) = triangulate_2d_points(A)
        return self.triangle_surface(points, indices, color, kind, opacity)

    def parameterized_morph(self, f, mins, maxes, counts, duration, color, opacity=None):
        A = parameterized_points_3d(f, mins, maxes, counts)
        (points, segments, triangles) = triangulate_3d_points(A)
        #print "points", len(points), points
        #print "segments", len(segments), segments
        #print "triangles", len(triangles), triangles
        return self.morph_triangles(points, segments, triangles, mins[-1], maxes[-1], duration, color, opacity=opacity)

    def triangle_surface(self, points, indices, color, kind="solid", opacity=None):
        assert kind in ["wire", "solid"]
        points = list(map(list, points))
        indices = list(map(list, indices))
        w = self.w
        THREE = self.THREE
        w(THREE.triangle_surface(self.scene, points, indices, color, kind, opacity))

    shapenames = ["star", "wireBox", "openTetrahedron", "wireSphere", "openCube", "cube", "axes"]

    def scatter(self, points, color=0x000000, scale=1.0, shapename="star"):
        assert shapename in self.shapenames, "shapenames are " + repr(self.shapenames)
        points = list(map(list, points))
        w = self.w
        THREE = self.THREE
        w(THREE.scatter(self.scene, shapename, points, scale, color))

    def ambient_light(self, color):
        w = self.w
        new_light = w.save_new("light", self.THREE.AmbientLight, [color])
        w(self.scene.add(new_light))

    def pointer(self, from_point, to_point, color, 
            kind="solid", base_ratio=0.1, epsilon=1e-3, strict=True):
        from_point = np.array(from_point)
        to_point = np.array(to_point)
        diff = to_point - from_point
        ndiff = norm(diff)
        if ndiff < epsilon:
            if strict:
                raise ValueError("point difference is too small for pointer")
            else:
                return #  silently ignore
        direction = diff / ndiff
        orthogonal1 = None
        for axis_point in [(1,0,0), (0,1,0), (0,0,1)]:
            orthogonal1 = np.cross(direction, axis_point)
            norm1 = norm(orthogonal1)
            if norm1 > epsilon:
                break
        assert orthogonal1 is not None
        orthogonal1 = orthogonal1 / norm1
        orthogonal2 = np.cross(direction, orthogonal1)
        #print "orthogonals", direction, orthogonal1, orthogonal2
        norm2 = norm(orthogonal2)
        assert norm2 > epsilon
        orthogonal2 = orthogonal2/norm2
        p1 = from_point + (ndiff * base_ratio) * orthogonal1
        p2 = from_point + (ndiff * base_ratio) * orthogonal2
        p3 = from_point - (ndiff * base_ratio * 0.4) * (orthogonal1 + orthogonal2)
        points = [to_point, p1, p2, p3]
        triples = [(1,2,3), (0,3,2), (3,0,1), (1,0,2)]
        self.triangle_surface(points, triples, color, kind)

    def std_lighting(self, offset=1000):
        self.light(0x915f7a, offset, offset, offset)
        self.light(0xa5971f, offset, offset, -offset)
        self.light(0x91a57f, offset, -offset, offset)
        self.light(0xa15f97, offset, -offset, -offset)
        self.light(0x795af1, -offset, offset, offset)
        self.light(0xfa5197, -offset, offset, -offset)
        self.light(0x7fa591, -offset, -offset, offset)
        self.light(0xa59f17, -offset, -offset, -offset)
        self.ambient_light(0x225533)

    def text(self, text, position, size, color=None, rotation=None, height=None, options=None):
        if options is None:
            options = {}
        settings = options.copy()
        if not height:
            height = size/10.0
        settings["size"] = size
        settings["height"] = height
        settings["bevelSize"] = size/20.0
        settings["bevelThickness"] = size/20.0
        if color is not None:
            settings["color"] = color
        position = list(position)
        if rotation:
            rotation = list(rotation)
        w = self.w
        THREE = self.THREE
        w(THREE.simple_text(text, position, self.scene, rotation, settings))

    def morph_triangles(self, points, segments, triangles, min_value, max_value, duration, color, 
            opacity=None, name="morph_triangles", ticking=True):
        self.last_points = points
        self.last_segments = segments
        self.last_triangles = triangles
        w = self.w
        THREE = self.THREE
        element = self.element
        # xxxx don't need to cache material here.
        mesh_options = {"color": color, "morphTargets": True}
        if opacity is not None:
            mesh_options["opacity"] = opacity
        mesh_options["shading"] = THREE.FlatShading
        #klass = THREE.MeshLambertMaterial
        klass = THREE.MeshPhongMaterial
        material = w.save_new("morph_material", klass, [mesh_options])
        data = {}
        data["max_value"] = max_value
        data["min_value"] = min_value
        data["shift"] = [0,0,0,0]
        data["scale"] = [1,1,1,1]
        #data["positions"] = points
        # flatten points, segments, triangles
        positions = []
        for p in points:
            positions.extend(p)
        data["positions"] = positions
        fsegments = []
        for segment in segments:
            fsegments.extend(segment)
        data["segments"] = fsegments
        ftriangles = []
        for triangle in triangles:
            ftriangles.extend(triangle)
        data["triangles"] = ftriangles
        w(material._set("side", THREE.DoubleSide))
        w.save(name, THREE.morph_triangles(data, self.scene, duration, material))
        w(element[name].set_ticking(ticking))

    def animate(self, onoff=True, name="morph_triangles"):
        w = self.w
        info = self.element[name]
        w(info.set_ticking(onoff))
        w.flush()

    def set_time(self, time, name="morph_triangles"):
        w = self.w
        info = self.element[name]
        w(info.set_current_time(time))
        w(info.tick())
        w.flush()

    def morph_stats_async(self, callback, name="morph_triangles"):
        w = self.w
        info = self.element[name]
        return w.send_commands([info.min, info.max, info.get_current_time()], callback)

    def sprite_text(self, text, positions, size, color, canvasWidth, options=None):
        positions = map(list, positions)
        if options is None:
            options = {}
        settings = options.copy()
        # canvasWidth should be power of 2
        canvasWidth2 = 1
        while canvasWidth > canvasWidth2:
            canvasWidth2 += canvasWidth2
        w = self.w
        THREE = self.THREE
        w(THREE.sprite_text(self.scene, text, positions, size, color, canvasWidth2, options))

    camera_arguments = [75, 1.0, 0.0001, 100000]

    prepared = False

    def prepare_renderer(self):
        if self.prepared:
            return
        renderer = self.renderer
        scene = self.scene
        THREE = self.THREE
        w = self.w
        camera = self.camera = w.save_new("camera", THREE.PerspectiveCamera, list(self.camera_arguments))
        try:
            (x, y, z) = self.offset
        except TypeError:
            w(camera.position._set("z", self.offset))
        else:
            w(camera.position._set("x", x))
            w(camera.position._set("y", y))
            w(camera.position._set("z", z))
        w(renderer.setClearColor( 0xffffff, 1))
        #do_render = w(renderer.render(scene, camera))
        options = {"autoRotate": self.autoRotate, "center": list(self.center)}
        w(THREE.orbiter(camera, renderer, scene, options))
        self.prepared = True

    def show(self, embed=False):
        self.prepare_renderer()
        w = self.w
        if embed:
            # html = w.embedded_html(True, await=["THREE", "_typeface_js.faces['helvetiker']"])
            # open("/tmp/embedded_html.txt", "w").write(html)
            w.embed(True, await=["THREE", "_typeface_js.faces['helvetiker']"])
        else:
            w.flush()
            return w

class AnimationControl(object):

    def __init__(self, doodle, min_t, max_t, animation_name="morph_triangles"):
        self.doodle = doodle
        self.name = animation_name
        self.min_t = min_t
        self.max_t = max_t
        slider = self.slider = widgets.FloatSlider(min=min_t, max=max_t)
        slider.on_trait_change(self.change_time, "value")
        checkbox = self.checkbox = widgets.Checkbox(description="animate", value=True)
        checkbox.on_trait_change(self.change_animation, "value")
        self.assembly = widgets.VBox(children=[checkbox, doodle.w, slider])

    def change_time(self, *args):
        new_time = self.slider.value
        self.doodle.set_time(new_time, name=self.name)

    def change_animation(self, *args):
        self.doodle.animate(self.checkbox.value, self.name)

    def stats_callback(self, *args):
        (self.mins, self.maxes, self.current_time) = args[0][0]
        self.slider.min = self.mins[-1]
        self.slider.max = self.maxes[-1]

    def show(self):
        display(self.assembly)
        self.doodle.show()
        # xxxx some sync issue with the following:
        #self.doodle.morph_stats_async(self.stats_callback, self.name)
