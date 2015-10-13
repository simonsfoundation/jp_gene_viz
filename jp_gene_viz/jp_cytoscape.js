
require(["widgets/js/widget", "widgets/js/manager", "cytoscape", "underscore", "jquery"
], function(widget, manager, cytoscape, _, $) {
	debugger;

	var CytoScapeView = widget.DOMWidgetView.extend({

		render: function() {
			//debugger;
			var that = this;
			var $el = that.$el;
            var target = document.createElement("div");
            target.style.width = "100px";
            target.style.height = "100px";
            var $target = $(target);
            $el.append(target);
            that.$target = $target;
            //$el.text("Hello world!");
            //return;
            var style = {
                "color": "red",
                "background-color": "blue"
            }
			var cy = cytoscape({
                container: target,
                elements: {
                    nodes:[{ data: { id: "n", label: "cytoscape.js", style: style}} ]
                },
                style: 'node { content: data(label); }',
				ready: function() { 
                    //debugger;
                    console.log("cytoscape is ready"); 
                }
			});
            that.cy = cy;
            that.update();
            // for debugging only
            window.cy = cy;
		},

        update: function(options) {
            var that = this;
            var commands = this.model.get("commands");
            var width = this.model.get("width");
            var height = this.model.get("height");
            var $target = that.$target;
            var target = $target[0];
            var cy = that.cy;
            // set width and height of container
            $target.width(width);
            $target.height(height);
            // execute any commands, in batch mode.
            if (commands.length == 2) {
                var command_counter = commands[0];
                var command_list = commands[1];
                var some_command = false;
                var results = [];
                cy.batch(function() {
                    _.each(command_list, function(command, i) {
                        some_command = true;
                        var result = that.execute_command(command);
                        results[i] = that.json_safe(result, 1);
                    });
                });
            }
            // reset the commands list, if appropriate.
            if (some_command) {
                that.model.set("commands", []);
                that.model.set("results", [command_counter, results])
                that.touch();
            }
        },

        execute_command: function(command) {
            // see jp_cytoscope.py send_commands docstring for explanation.
            var that = this;
            var result = command;   // default
            if ($.isArray(command)) {
                var cy = that.cy;
                var indicator = command[0];
                var remainder = command.slice();
                remainder.shift();
                if (indicator == "fun") {
                    var name = remainder.shift();
                    var args = remainder.map(that.execute_command);
                    var fn = cy[name];
                    result = fn.apply(cy, args);
                } else if (indicator == "method") {
                    var target_desc = remainder.shift();
                    var target = that.execute_command(target_desc);
                    var name = remainder.shift();
                    var args = remainder.map(that.execute_command);
                    var method = target[name];
                    result = method.apply(target, args);
                } else if (indicator == "list") {
                    result = remainder.map(that.execute_command);
                } else if (indicator == "dict") {
                    result = {};
                    var desc = remainder[0];
                    for (var key in desc) {
                        var key_desc = desc[key];
                        var val = that.execute_command(key_desc);
                        result[key] = val;
                    }
                } else if (indicator == "id") {
                    // untranslated object
                    return remainder[0]
                }
            }
            return result;
        },

        json_safe: function(val, depth) {
            // maybe expand later as need arises
            var that = this;
            var ty = (typeof val);
            if ((ty == "number") || (ty == "string") || (ty == "boolean")) {
                return val;
            }
            if (depth) {
                if ($.isArray(val)) {
                    var result = [];
                    _.each(val, function(elt, i) {
                        var r = that.json_safe(elt, depth-1);
                        if (r != null) {
                            result[i] = r;
                        }
                    });
                    return result;
                } else {
                    var result = {};
                    for (var key in val) {
                        var jv = that.json_safe(val[key], depth-1);
                        if (jv != null) {
                            result[key] = jv;
                        }
                    }
                    return result;
                }
            }
            return null;
        }

	});

	manager.WidgetManager.register_widget_view('CytoScapeView', CytoScapeView);
});
