
"""
This is an experimental use of HighCharts with js_proxy
to explore file system space usage.
"""

from subprocess import check_output
#from jp_gene_viz import js_proxy
import os

def directory_usage(directory, epsilon=0.02):
    if not os.path.isdir(directory):
        return None
    ls = os.listdir(directory)
    result = {}
    total = 0.0
    for fn in ls:
        path = os.path.join(directory, fn)
        try:
            usage = check_output(["du", "-s", path])
        except Exception:
            pass
        else:
            [snum, sname] = usage.strip().split("\t")
            num = float(snum)
            total += num
            result[fn] = (path, num)
    final = {}
    other = 0
    for fn in result:
        (path, num) = result[fn]
        portion = num/total
        if portion < epsilon:
            other += num
        else:
            final[fn] = {"name": fn, "y": num, "percent": portion*100, "id": path}
    if other>epsilon:
        final["other"] = {"name": "other", "y": other, "percent": other*100/total, "id": None}
    return final

def explore_directory(directory):
    from jp_gene_viz import js_proxy
    from IPython.display import display, HTML
    js_proxy.load_javascript_support()
    load_highcharts = """
    <script src="https://code.highcharts.com/highcharts.js"></script>
    """
    display(HTML(load_highcharts))
    widget = js_proxy.ProxyWidget()
    elt = widget.element()
    # create a chart element look up table
    #widget(elt._set("PieCharts", {}))
    # attach a pie chart for directory
    chart = DirectoryPieChart(directory, widget, elt)
    widget.flush()
    display(widget)
    return widget


class DirectoryPieChart(object):

    def __init__(self, directory, widget, elt):
        du = directory_usage(directory)
        self.widget = widget
        self.elt = elt
        window = widget.window()
        if len(du) < 1:
            widget(elt.html("Directory is empty."))
            return
        jQuery = window.jQuery
        PieCharts = elt.PieCharts
        # XXXX NEED TO FIX THE NAMING FOR MULTIPLE LEVELS
        # append an element for the chart
        widget(elt._set("chartDiv", jQuery("<div>Directory chart</div>").width("100%").height("400px").appendTo(elt)))
        # make a div for a next chart on click
        widget(elt._set("nextDiv", jQuery("<div>Click on a directory to expand</div>").width("100%").appendTo(elt)))
        # add a pie chart to the chartDiv
        chartinfo = {}
        chartinfo["chart"] = {"type": "pie"}
        chartinfo["title"] = {"text": directory}
        data = []
        for fn in du:
            info = du[fn]
            data.append(info)
        chartinfo["series"] = [{
            "name": "files",
            "colorByPoint": True,
            "data": data
        }]
        chartinfo["tooltip"] = {"pointFormat": "{series.name} {point.percent:.1f} % {point.y}"}
        pointsEvents = {"click": self.clickCallback()}
        pointsOptions = {"events": pointsEvents}
        seriesOptions = {"point": pointsOptions}
        plotOptions = {"series": seriesOptions}
        chartinfo["plotOptions"] = plotOptions
        widget(elt.chartDiv.highcharts(chartinfo))
        self.nextChart = None

    def clickCallback(self):
        return self.widget.callback(self.handle_click, data=None, level=3)

    def handle_click(self, ident, args):
        #import pprint
        eventinfo = args["0"]
        #pprint.pprint(eventinfo)
        widget = self.widget
        element = self.elt
        widget(element.nextDiv.empty())
        clickDirectory = eventinfo["point"].get("id")
        if clickDirectory and os.path.isdir(clickDirectory):
            self.nextChart = DirectoryPieChart(clickDirectory, widget, element.nextDiv)
        else:
            widget(element.nextDiv.html(repr(clickDirectory) + " is not a directory."))
        widget.flush()


if __name__=="__main__":
    from pprint import pprint
    pprint(directory_usage("."))
