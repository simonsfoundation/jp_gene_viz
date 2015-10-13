
require(["widgets/js/widget", "widgets/js/manager", "cytoscape"], function(widget, manager, cytoscape) {
	debugger;

	var CytoScapeView = widget.DOMWidgetView.extend({

		render: function() {
			debugger;
			var that = this;
			var $el = that.$el;
            var target = document.createElement("div");
            target.style.width = "100px";
            target.style.height = "100px";
            var $target = $(target);
            $el.append(target);
            //$el.text("Hello world!");
            //return;
			var cy = $target.cytoscape({
                elements: {
                    nodes:[{ data: { id: "n", label: "cytoscape.js"}} ]
                },
                style: 'node { content: data(label); }',
				ready: function() { 
                    debugger;
                    console.log("cytoscape is ready"); 
                }
			});
		}
	});

	manager.WidgetManager.register_widget_view('CytoScapeView', CytoScapeView);
});
