

"""
Nearest neighbors interactive display with 3d presentation.
"""

from sklearn import neighbors, datasets
from jp_gene_viz import js_proxy
from IPython.display import display, HTML
import copy
import numpy as np
import traitlets
import ipywidgets as widgets
from sklearn.cross_validation import train_test_split
from jp_gene_viz import scatter3d
from jp_gene_viz import js_context
import math
import time

load_three = """
<script src="http://cdnjs.cloudflare.com/ajax/libs/three.js/r70/three.min.js">
</script>
"""

load_font = """
<script src="http://threejs.org/examples/fonts/helvetiker_regular.typeface.js">
</script>
"""
#display(HTML(load_three))
from jp_gene_viz import js_context
js_context.load_if_not_loaded(["three.js"])
js_context.load_if_not_loaded(["FontUtils.js"])
#time.sleep(0.1)
#display(HTML(load_font))
js_context.load_if_not_loaded(["helvetiker_regular.typeface.js"])


class Nearest(traitlets.HasTraits):

    test_size = traitlets.Float(0.30)

    n_neighbors = traitlets.Integer(5)

    weights = "uniform"

    show_borders = traitlets.Bool(True)

    show_training = traitlets.Bool(True)

    show_test = traitlets.Bool(True)

    x_name = traitlets.Unicode("")

    y_name = traitlets.Unicode("")

    z_name = traitlets.Unicode("")

    # debugging only
    with_box = False

    rotate = True

    cleanup = False

    show_target_names = True

    def __init__(self, dataset, *args, **kwargs):
        super(Nearest, self).__init__(*args, **kwargs)
        self.dataset = dataset
        feature_names = list(dataset.feature_names)
        self.x_name = feature_names[0]
        self.y_name = feature_names[1]
        self.z_name = feature_names[2]
        sc = self.scatter_plot = js_proxy.ProxyWidget()
        xd = self.x_dropdown = widgets.Dropdown(
            options=list(feature_names), value=self.x_name)
        yd = self.y_dropdown = widgets.Dropdown(
            options=list(feature_names), value=self.y_name)
        zd = self.z_dropdown = widgets.Dropdown(
            options=list(feature_names), value=self.z_name)
        bc = self.border_checkbox = widgets.Checkbox(description="border", value=True)
        tc = self.training_checkbox = widgets.Checkbox(description="training", value=True)
        tstc = self.test_checkbox = widgets.Checkbox(description="test", value=True)
        ns = self.n_slider = widgets.IntSlider(value=self.n_neighbors, min=1, max=20,
            description="neighbors", width="50px")
        ss = self.n_slider = widgets.FloatSlider(value=self.n_neighbors, min=0.2, max=0.5,
            description="test size", width="50px", step=0.1)
        traitlets.directional_link((ss, "value"), (self, "test_size"))
        traitlets.directional_link((xd, "value"), (self, "x_name"))
        traitlets.directional_link((yd, "value"), (self, "y_name"))
        traitlets.directional_link((zd, "value"), (self, "z_name"))
        traitlets.directional_link((bc, "value"), (self, "show_borders"))
        traitlets.directional_link((ns, "value"), (self, "n_neighbors"))
        traitlets.directional_link((tc, "value"), (self, "show_training"))
        traitlets.directional_link((tstc, "value"), (self, "show_test"))
        xd.on_trait_change(self.redraw, "value")
        ss.on_trait_change(self.redraw, "value")
        yd.on_trait_change(self.redraw, "value")
        zd.on_trait_change(self.redraw, "value")
        bc.on_trait_change(self.redraw, "value")
        tc.on_trait_change(self.redraw, "value")
        tstc.on_trait_change(self.redraw, "value")
        ns.on_trait_change(self.redraw, "value")
        controls = widgets.VBox(children=[xd, yd, zd, bc, tc, tstc, ns, ss])
        self.assembly = widgets.HBox(children=[controls, sc])

    def redraw(self, *args):
        self.draw_plot()

    def draw_plot(self, width="700px", height="700px", do_flush=False):
        # clean up first.
        if self.cleanup:
            self.cleanup()
        dataset = self.dataset
        feature_names = list(dataset.feature_names)
        data0 = dataset.data
        target0 = dataset.target
        target_names = dataset.target_names
        # Do train test split eventually
        (data, datat, target, targett) = train_test_split(data0, target0,
            test_size=self.test_size, random_state=42)
        x_name = self.x_name
        y_name = self.y_name
        z_name = self.z_name
        print "showing", x_name, y_name, z_name
        x_index = feature_names.index(x_name)
        y_index = feature_names.index(y_name)
        z_index = feature_names.index(z_name)
        X = np.hstack([data[:, x_index:x_index+1], data[:, y_index:y_index+1], data[:, z_index:z_index+1]])
        # train the model
        clf = neighbors.KNeighborsClassifier(self.n_neighbors, weights=self.weights)
        clf.fit(X, target)
        # get a mesh of 
        x_min, x_max = X[:, 0].min(), X[:, 0].max()
        y_min, y_max = X[:, 1].min(), X[:, 1].max()
        z_min, z_max = X[:, 2].min(), X[:, 2].max()
        dx = (x_max - x_min)
        dy = (y_max - y_min)
        dz = (z_max - z_min)
        x_min1, x_max1 = x_min - dx*0.1, x_max + dx*0.1
        y_min1, y_max1 = y_min - dy*0.1, y_max + dy*0.1
        z_min1, z_max1 = z_min - dz*0.1, z_max + dz*0.1
        pixel_side = 30.0
        hx = (dx)/pixel_side
        hy = (dy)/pixel_side
        hz = (dz)/pixel_side
        xx, yy, zz = np.meshgrid(
            np.arange(x_min1, x_max1, hx),
            np.arange(y_min1, y_max1, hy),
            np.arange(z_min1, z_max1, hz))
        Z = clf.predict(np.c_[xx.ravel(), yy.ravel(), zz.ravel()])
        Z = Z.reshape(xx.shape)
        # find the borders
        Z1 = Z + 1
        DD = np.zeros(Z1.shape)
        DD[1:] += np.abs(Z1[1:] - Z1[:-1])
        DD[:,1:] += np.abs(Z1[:,1:] - Z1[:,:-1])
        DD[:,:,1:] += np.abs(Z1[:,:,1:] - Z1[:,:,:-1])
        DD[:-1] += np.abs(Z1[:-1] - Z1[1:])
        DD[:, :-1] += np.abs(Z1[:, :-1] - Z1[:, 1:])
        DD[:, :,:-1] += np.abs(Z1[:,:, :-1] - Z1[:,:, 1:])
        # XXXX add 3rd dimension border...
        (xnz, ynz, znz) = np.where(DD)
        # construct the data and prediction series
        data_series = []
        test_series = []
        error_series = []
        border_series = []
        colors = []
        for (tindex, target_name) in enumerate(target_names):
            color = get_color(tindex)
            colors.append(color)
            s = self.make_series_dict(target_name, color)
            error_series.append(s)
            if self.show_training:
                s = self.make_series_dict(target_name, color)
                data_series.append(s)
            if self.show_test:
                s = self.make_series_dict(target_name+"?", color, 2, "cube")
                test_series.append(s)
            if self.show_borders:
                bcolor = get_color(tindex, opacity="0.3")
                bs = self.make_series_dict("[%s]"%(target_name,), bcolor, 1, "star",
                    fillColor="white")
                border_series.append(bs)
        if self.show_training:
            for (dindex, tindex) in enumerate(target):
                x = data[dindex, x_index]
                y = data[dindex, y_index]
                z = data[dindex, z_index]
                s = data_series[tindex]
                predicted = clf.predict([[x,y,z]])
                if predicted == tindex:
                    datum = [x,y,z]
                else:
                    datum = [x,y,z]
                s["data"].append(datum)
        if self.show_test:
            for (dindex, tindex) in enumerate(targett):
                x = datat[dindex, x_index]
                y = datat[dindex, y_index]
                z = datat[dindex, z_index]
                s = test_series[tindex]
                #s["data"].append([x,y])
                predicted = clf.predict([[x,y,z]])
                if predicted == tindex:
                    datum = [x,y,z]
                else:
                    datum = [x,y,z]
                s["data"].append(datum)
        if self.show_borders:
            for (nzindex, i) in enumerate(xnz):
                j = ynz[nzindex]
                k = znz[nzindex]
                xijk = xx[i,j,k]
                yijk = yy[i,j,k]
                zijk = zz[i,j,k]
                Zijk = Z[i,j,k]
                bs = border_series[Zijk]
                bs["data"].append([xijk,yijk,zijk])
        sp = scatter3d.ScatterPlot3D()
        for s in border_series + data_series + test_series + error_series:
            marker = s["symbol"]
            color = s["color"]
            points = s["data"]
            radius =  s["radius"]
            #print "series", (marker, hex(color), len(points))
            if points:
                sp.add_series(marker, color, points, radius)
        sc = self.scatter_plot
        element = sc.element()
        sc(element.empty())
        window = sc.window()
        if self.show_target_names:
            for (tindex, target_name) in enumerate(target_names):
                hcolor = html_color(get_color(tindex))
                sc(element.append('<div style="background-color: %s; color: white;">%s</div>'
                    % (hcolor, target_name)))
        THREE = window.THREE
        new = sc.save_new
        scene = new("scene", THREE.Scene, [])
        camera = new("camera", THREE.PerspectiveCamera, [75, 1.0, 1, 100000])
        #sc(camera.lookAt(scene.position))
        if self.with_box:
            geometry = new("geometry", THREE.BoxGeometry, [200, 200, 200])
            #geometry = new("geometry", THREE.TetrahedronGeometry, [])
            material = new("material", THREE.MeshBasicMaterial, [{"color": 0xff00ee, "wireframe": True } ])
            mesh = new("mesh", THREE.Mesh, [geometry, material])
            sc(scene.add(mesh))
        for (position, color) in [
            ((1000, 1000, 1000), 0xFF00FF),
            ((-1000, -1000, 1000), 0x9999FF),
            ((1000, -1000, -1000), 0xaa00FF),
            ((-1000, 1000, -1000), 0xFF4444),
            ]:
            light = new("light", THREE.DirectionalLight, [color])
            sc(light.position.set(*position))
            sc(scene.add(light))
        sc(camera.position._set("z", 500))
        renderer = new("renderer", THREE.WebGLRenderer, [])
        sc(renderer.setSize(800, 800))
        sc(element.append(renderer.domElement))
        # draw the scatter plot
        sp.plot(300, sc, scene, 10, [x_name, y_name, z_name])
        sc(renderer.render(scene, camera))
        if self.rotate:
            s2 = math.sqrt(2)*0.5
            s3 = math.sqrt(1/3.0)
            gamma = scatter3d.xyz_dict(s3, s3, s3)
            delta = scatter3d.xyz_dict(s2, s2, 0)
            radius = 400
            options = {"dtheta": 0.003}
            sc.save("rotator", THREE.rotator(gamma, delta, radius, camera, renderer, scene, options))
        if do_flush:
            sc.flush()
        # define a clean up action
        def cleanup():
            if self.rotate:
                sc(element.rotator.destroy())
            sc.flush()
        self.cleanup = cleanup

    def make_series_dict(self, name, color, radius=5, symbol="wireBox", 
        fillColor=None, data=()):
        return {
            "name": name,
            "color": color,
            "radius": radius,
            "symbol": symbol,
            "fillcolor": fillColor,
            "data": list(data)
        }

    def show(self):
        self.draw_plot()
        display(self.assembly)

def get_color(i, opacity="0.5"):
    [r,g,b] = std_colors[i]
    return r * 0x10000 + g * 0x100 + b

def html_color(color):
    return "#" + ("%06x" % color)

std_colors = [
    [255, 0, 0],
    [55, 255, 55],
    [100, 100, 255],
    [200, 200, 0],
    [0, 200, 200],
    [200, 0, 200],
    [155, 155, 155],
    [230, 155, 90],
    [230, 90, 155],
    [155, 230, 90],
    [155, 90, 230],
    [90, 155, 230],
    [90, 230, 155]
]

def show_iris():
    iris = datasets.load_iris()
    result = Nearest(iris)
    result.show()
    return result

def static_iris():
    iris = datasets.load_iris()
    result = Nearest(iris)
    result.draw_plot(do_flush=False)
    result.scatter_plot.embed(True, await=["THREE", "_typeface_js.faces['helvetiker']"])
    return result

def show_bc():
    bc = datasets.load_breast_cancer()
    result = Nearest(bc)
    result.show()
    return result
