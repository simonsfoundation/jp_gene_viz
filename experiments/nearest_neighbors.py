

"""
Next: border are not working!!!
"""

from sklearn import neighbors, datasets
from jp_gene_viz import js_proxy
from IPython.display import display, HTML
import copy
import numpy as np
import traitlets
import ipywidgets as widgets
from sklearn.cross_validation import train_test_split


def load_javascript_support():
    js_proxy.load_javascript_support()
    load_highcharts = """
    <script src="http://code.highcharts.com/highcharts.js"></script>
    """
    display(HTML(load_highcharts))
    load_modules = """
    <script src="https://code.highcharts.com/modules/drilldown.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    """
    display(HTML(load_modules))


scatter_chart_template = {
        "chart": {
            "type": 'scatter',
            "zoomType": 'xy'
        },
        "exporting": {"enabled": False},
        'title': {
            "text": "nearest neighbor classification"
        },
        "plotOptions": {
            "scatter": {
                "marker": {
                    "radius": 2,
                    "states": {
                        "hover": {
                            "enabled": True,
                            "lineColor": 'rgb(100,100,100)'
                        }
                    }
                },
                "states": {
                    "hover": {
                        "marker": {
                            "enabled": False
                        }
                    }
                },
                "tooltip": {
                    "headerFormat": '<b>{series.name}</b><br>',
                    "pointFormat": '{point.x}, {point.y}'
                }
            }
        }
    }

class Nearest(traitlets.HasTraits):

    test_size = traitlets.Float(0.30)

    n_neighbors = traitlets.Integer(5)

    weights = "uniform"

    prediction_grid = traitlets.Bool(True)

    show_borders = traitlets.Bool(True)

    show_training = traitlets.Bool(True)

    show_test = traitlets.Bool(True)

    x_name = traitlets.Unicode("")

    y_name = traitlets.Unicode("")

    def __init__(self, dataset, *args, **kwargs):
        super(Nearest, self).__init__(*args, **kwargs)
        self.dataset = dataset
        feature_names = list(dataset.feature_names)
        self.x_name = feature_names[0]
        self.y_name = feature_names[1]
        sc = self.scatter_plot = js_proxy.ProxyWidget()
        xd = self.x_dropdown = widgets.Dropdown(
            options=list(feature_names), value=self.x_name)
        yd = self.y_dropdown = widgets.Dropdown(
            options=list(feature_names), value=self.y_name)
        bc = self.border_checkbox = widgets.Checkbox(description="border", value=True)
        ic = self.interior_checkbox = widgets.Checkbox(description="interior", value=True)
        tc = self.training_checkbox = widgets.Checkbox(description="training", value=True)
        tstc = self.test_checkbox = widgets.Checkbox(description="test", value=True)
        ns = self.n_slider = widgets.IntSlider(value=self.n_neighbors, min=1, max=20,
            description="neighbors", width="50px")
        ss = self.n_slider = widgets.FloatSlider(value=self.n_neighbors, min=0.2, max=0.5,
            description="test size", width="50px", step=0.1)
        traitlets.directional_link((ss, "value"), (self, "test_size"))
        traitlets.directional_link((xd, "value"), (self, "x_name"))
        traitlets.directional_link((yd, "value"), (self, "y_name"))
        traitlets.directional_link((bc, "value"), (self, "show_borders"))
        traitlets.directional_link((ic, "value"), (self, "prediction_grid"))
        traitlets.directional_link((ns, "value"), (self, "n_neighbors"))
        traitlets.directional_link((tc, "value"), (self, "show_training"))
        traitlets.directional_link((tstc, "value"), (self, "show_test"))
        xd.on_trait_change(self.redraw, "value")
        ss.on_trait_change(self.redraw, "value")
        yd.on_trait_change(self.redraw, "value")
        bc.on_trait_change(self.redraw, "value")
        tc.on_trait_change(self.redraw, "value")
        ic.on_trait_change(self.redraw, "value")
        tstc.on_trait_change(self.redraw, "value")
        ns.on_trait_change(self.redraw, "value")
        controls = widgets.VBox(children=[xd, yd, bc, ic, tc, tstc, ns, ss])
        self.assembly = widgets.HBox(children=[controls, sc])

    def redraw(self, *args):
        self.draw_plot()

    def draw_plot(self, width="700px", height="600px"):
        sc = self.scatter_plot
        elt = sc.element()
        sc(elt.empty())
        #sc(elt.html("plot here!"))
        sc(elt.width(width).height(height))
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
        x_index = feature_names.index(x_name)
        y_index = feature_names.index(y_name)
        X = np.hstack([data[:, x_index:x_index+1], data[:, y_index:y_index+1]])
        # train the model
        clf = neighbors.KNeighborsClassifier(self.n_neighbors, weights=self.weights)
        clf.fit(X, target)
        # get a mesh of 
        x_min, x_max = X[:, 0].min(), X[:, 0].max()
        y_min, y_max = X[:, 1].min(), X[:, 1].max()
        dx = (x_max - x_min)
        dy = (y_max - y_min)
        x_min1, x_max1 = x_min - dx*0.1, x_max + dx*0.1
        y_min1, y_max1 = y_min - dy*0.1, y_max + dy*0.1
        hx = (dx)/100.0
        hy = (dy)/100.0
        xx, yy = np.meshgrid(np.arange(x_min1, x_max1, hx),
                     np.arange(y_min1, y_max1, hy))
        Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        # find the borders
        Z1 = Z + 1
        DD = np.zeros(Z1.shape)
        DD[1:] += np.abs(Z1[1:] - Z1[:-1])
        DD[:,1:] += np.abs(Z1[:,1:] - Z1[:,:-1])
        DD[:-1] += np.abs(Z1[:-1] - Z1[1:])
        DD[:, :-1] += np.abs(Z1[:, :-1] - Z1[:, 1:])
        (xnz, ynz) = np.where(DD)
        # construct the data and prediction series
        data_series = []
        test_series = []
        prediction_series = []
        border_series = []
        colors = []
        for (tindex, target_name) in enumerate(target_names):
            color = get_color(tindex)
            colors.append(color)
            if self.show_training:
                s = self.make_series_dict(target_name, color)
                data_series.append(s)
            if self.show_test:
                s = self.make_series_dict(target_name+"?", color, 8, "triangle")
                test_series.append(s)
            if self.prediction_grid:
                pcolor = get_color(tindex, opacity="0.1")
                ps = self.make_series_dict("(%s)" % (target_name,), color, 1)
                prediction_series.append(ps)
            if self.show_borders:
                bcolor = get_color(tindex, opacity="0.3")
                bs = self.make_series_dict("[%s]"%(target_name,), bcolor, 4, "square",
                    fillColor="white")
                border_series.append(bs)
        if self.show_training:
            for (dindex, tindex) in enumerate(target):
                x = data[dindex, x_index]
                y = data[dindex, y_index]
                s = data_series[tindex]
                predicted = clf.predict([[x,y]])
                if predicted == tindex:
                    datum = [x,y]
                else:
                    pcolor = colors[predicted]
                    dcolor = colors[tindex]
                    datum = {}
                    datum["x"] = x
                    datum["y"] = y
                    datum["marker"] = {
                        "symbol": "triangle-down",
                        "radius": 9,
                        "lineWidth": 4,
                        "lineColor": pcolor,
                        "fillColor": dcolor
                    }
                s["data"].append(datum)
        if self.show_test:
            for (dindex, tindex) in enumerate(targett):
                x = datat[dindex, x_index]
                y = datat[dindex, y_index]
                s = test_series[tindex]
                #s["data"].append([x,y])
                predicted = clf.predict([[x,y]])
                if predicted == tindex:
                    datum = [x,y]
                else:
                    pcolor = colors[predicted]
                    dcolor = colors[tindex]
                    datum = {}
                    datum["x"] = x
                    datum["y"] = y
                    datum["marker"] = {
                        "symbol": "diamond",
                        "radius": 9,
                        "lineWidth": 4,
                        "lineColor": pcolor,
                        "fillColor": dcolor
                    }
                s["data"].append(datum)
        if self.show_borders:
            for (nzindex, i) in enumerate(xnz):
                j = ynz[nzindex]
                xij = xx[i,j]
                yij = yy[i,j]
                Zij = Z[i,j]
                bs = border_series[Zij]
                bs["data"].append([xij,yij])
        if self.prediction_grid:
            for (i, xr) in enumerate(xx):
                yr = yy[i]
                Zr = Z[i]
                for (j, xij) in enumerate(xr):
                    yij = yr[j]
                    Zij = Zr[j]
                    ps = prediction_series[Zij]
                    ps["data"].append([xij, yij])
        chart_dict = copy.deepcopy(scatter_chart_template)
        chart_dict["xAxis"] = {"title": {"text": self.x_name}}
        chart_dict["yAxis"] = {"title": {"text": self.y_name}}
        chart_dict["series"] = border_series + prediction_series + data_series + test_series
        #import pprint
        #pprint.pprint(chart_dict)
        sc(elt.highcharts(chart_dict))
        sc.flush()

    def make_series_dict(self, name, color, radius=5, symbol="circle", 
        fillColor=None, data=()):
        result = {}
        result["name"] = name
        marker_options = {"radius": radius, "symbol": symbol}
        if fillColor:
            marker_options["fillColor"] = fillColor
            marker_options["lineColor"] = color
            marker_options["lineWidth"] = 1
        result["marker"] = marker_options
        result["color"] = color
        result["data"] = list(data)
        return result

    def show(self):
        self.draw_plot()
        display(self.assembly)

class SVGScatterer:

    side = 50

    spacing = 10

    border_color = "black"

    epsilon = 0.00001

    def __init__(self, dataset):
        self.dataset = dataset

    def plot_pair(self, svg_canvas, x_feature_index, y_feature_index, x0, y0):
        dataset = self.dataset
        data = dataset.data
        target = dataset.target
        datax = data[:, x_feature_index]
        datay = data[:, y_feature_index]
        x_min = datax.min()
        x_max = datax.max()
        y_min = datay.min()
        y_max = datay.max()
        epsilon = self.epsilon
        side = self.side
        x_adjusted = (datax - x_min) * side / (x_max - x_min + epsilon) + x0
        y_adjusted = (datay - y_min) * side / (y_max - y_min + epsilon) + y0
        svg_canvas.rect(None, x0, y0, side, side, "white", stroke=self.border_color)
        for (i, x) in enumerate(x_adjusted):
            y = y_adjusted[i]
            t = target[i]
            color = get_color(t, 0.2)
            svg_canvas.circle(None, x, y, 2, color)

    def plot_all(self, svg_canvas):
        dataset = self.dataset
        feature_names = list(dataset.feature_names)
        nfeatures = len(feature_names)
        rfeatures = range(nfeatures)
        side = self.side
        spacing = self.spacing
        for x_feature_index in rfeatures:
            x0 = x_feature_index * side
            xfeature = feature_names[x_feature_index]
            xt = x0 + side/2.0
            yt = nfeatures * side + spacing
            style = {"transform": "rotate(90, %s, %s)" % (xt, yt)}
            if x_feature_index < nfeatures - 1:
                svg_canvas.text(None, xt, yt, xfeature, **style)
            if x_feature_index:
                svg_canvas.text(None, x0 + side*0.5, xt, xfeature)
            for y_feature_index in reversed(rfeatures):
                if y_feature_index > x_feature_index:
                    y0 = y_feature_index * side
                    self.plot_pair(svg_canvas, x_feature_index, y_feature_index, x0, y0)

    def widget(self):
        from jp_svg_canvas import canvas
        canvas.load_javascript_support(True)
        svg_canvas = canvas.SVGCanvasWidget()
        self.plot_all(svg_canvas)
        svg_canvas.send_commands()
        display(svg_canvas)
        # fit must happen after display.
        svg_canvas.fit()
        svg_canvas.send_commands()
        canvas_side = len(self.dataset.feature_names) * self.side
        canvas_side = max(canvas_side, 500)
        svg_canvas.width = canvas_side
        svg_canvas.height = canvas_side
        return svg_canvas

def get_color(i, opacity="0.5"):
    [r,g,b] = std_colors[i]
    return "rgba(%s,%s,%s,%s)" % (r, g, b, opacity)

std_colors = [
    [255, 0, 0],
    [0, 255, 0],
    [0, 0, 255],
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

def show_bc():
    bc = datasets.load_breast_cancer()
    result = Nearest(bc)
    result.show()
    return result

