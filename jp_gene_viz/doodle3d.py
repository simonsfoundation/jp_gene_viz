"""
Quick helper for creating 3d diagrams with orbit controls in Jupyter
"""

from jp_gene_viz import js_context
from jp_gene_viz import js_proxy

def init():
    js_context.load_if_not_loaded(["three.js"])
    js_context.load_if_not_loaded(["FontUtils.js"])
    js_context.load_if_not_loaded(["helvetiker_regular.typeface.js"])
    js_context.load_if_not_loaded(["three_scatter.js"])
    js_context.load_if_not_loaded(["three_rotator.js"])
    js_context.load_if_not_loaded(["three_orbit.js"])
    js_context.load_if_not_loaded(["three_curve.js"])
    js_context.load_if_not_loaded(["three_triangles.js"])
    js_context.load_if_not_loaded(["TextGeometry.js"])
    js_context.load_if_not_loaded(["three_simple_text.js"])
    js_context.load_if_not_loaded(["OrbitControls.js"])
    js_proxy.load_javascript_support()

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

    def light(self, color, x, y, z):
        w = self.w
        THREE = self.THREE  
        new_light = w.save_new("light", THREE.DirectionalLight, [color])
        w(new_light.position.set(x, y, z))
        w(self.scene.add(new_light))

    def text(self, text, position, rotation):
        w = self.w
        THREE = self.THREE
        w(THREE.simple_text(text, location, self.scene, location))

    def curve(self, color, points):
        points = list(map(list, points))
        w = self.w
        THREE = self.THREE
        w(THREE.simple_curve(self.scene, points, color))

    def triangle_surface(self, points, indices, color, kind="solid", opacity=None):
        assert kind in ["wire", "solid"]
        points = list(map(list, points))
        indices = list(map(list, indices))
        w = self.w
        THREE = self.THREE
        w(THREE.triangle_surface(self.scene, points, indices, color, kind, opacity))

    shapenames = ["star", "wireBox", "openTetrahedron", "wireSphere", "openCube", "cube", "axes"]

    def scatter(self, points, color=0x000000, scale=1.0, shapename="star"):
        assert shapename in self.shapenames, "shapenames are " + repr(shapenames)
        points = list(map(list, points))
        w = self.w
        THREE = self.THREE
        w(THREE.scatter(self.scene, shapename, points, scale, color))

    def ambient_light(self, color):
        w = self.w
        new_light = w.save_new("light", self.THREE.AmbientLight, [color])
        w(self.scene.add(new_light))

    camera_arguments = [75, 1.0, 0.0001, 100000]

    def show(self):
        renderer = self.renderer
        scene = self.scene
        THREE = self.THREE
        w = self.w
        camera = self.camera = w.save_new("camera", THREE.PerspectiveCamera, list(self.camera_arguments))
        w(camera.position._set("z", self.offset))
        w(renderer.setClearColor( 0xffffff, 1))
        #do_render = w(renderer.render(scene, camera))
        options = {"autoRotate": self.autoRotate, "center": list(self.center)}
        w(THREE.orbiter(camera, renderer, scene, options))
        w.flush()
        return w