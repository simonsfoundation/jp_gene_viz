
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
            // cytoscape doesn't initialize properly with no elements?
			var cy = cytoscape({
                container: target,
                elements: {
                    nodes:[{ data: { id: "n", label: "cytoscape.js" }} ]
                },
                style: 'node { content: data(label); }',
				ready: function() { 
                    //debugger;
                    console.log("cytoscape is ready"); 
                }
			});
            that.cy = cy;
            // Special function to fix scrolling issue (hack)
            // This function must be called once after the network is visible
            // to make mouse events respond correctly after notebook scroll.
            // In the notebook: cy.send(jp.fix())
            that.fix = function (keep_elements) {
                var renderer = cy.renderer();
                var invalidate = function (e) {
                    renderer.invalidateContainerClientCoordsCache();
                };
                var node = $el[0];
                while (node) {
                    renderer.registerBinding(node, "scroll", invalidate);
                    node = node.parentNode;
                }
                // also get rid of the test element(s)
                if (!keep_elements) {
                    cy.remove("node");
                    cy.remove("edge");
                }
            };
            that.update();
            // fix the scrolling when the widget is displayed.
            that.on("displayed", function() { that.fix(true); });
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
                    var args = remainder.map(that.execute_command, that);
                    // look for the function in the visualization instance.
                    var fn = cy[name];
                    var fnthis = cy;
                    if (!fn) {
                        // look in the cytoscape namespace if not found.
                        fn = cytoscape[name];
                        fnthis = cytoscape;
                    }
                    if (name == "fix") {
                        // special function: fix scrolling issues
                        fn = that.fix;
                    }
                    if (name == "callback") {
                        // event callback function factory
                        fn = that.event_callback_factory;
                        fnthis = that;
                    }
                    if (fn) {
                        result = fn.apply(fnthis, args);
                    } else {
                        result = "No such function found " + name;  // ???
                    }
                } else if (indicator == "method") {
                    var target_desc = remainder.shift();
                    var target = that.execute_command(target_desc);
                    var name = remainder.shift();
                    var args = remainder.map(that.execute_command, that);
                    var method = target[name];
                    if (method) {
                        result = method.apply(target, args);
                    } else {
                        result = "In " + target + " no such method " + name;
                    }
                } else if (indicator == "list") {
                    result = remainder.map(that.execute_command, that);
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

        event_callback_factory: function(data) {
            var that = this;
            var handler = function(e) {
                // XXXX this may be sending too much?  too little?
                //var info = that.json_safe(e, 2);   // 2 levels?
                var info = {};
                var send_attrs = ["cyPosition", "cyRenderedPosition", "timeStamp", "type"];
                _.each(send_attrs, function(attr, i){
                    info[attr] = that.json_safe(e[attr], 3);
                });
                info.target_id = null;
                if ((e.cyTarget && e.cyTarget.id)) {
                    info.target_id = e.cyTarget.id();
                };
                var payload = [data, info];
                that.model.set("event_data", payload);
                that.touch();
            };
            return handler;
        },

        json_safe: function(val, depth) {
            // maybe expand later as need arises
            var that = this;
            var ty = (typeof val);
            if ((ty == "number") || (ty == "string") || (ty == "boolean")) {
                return val;
            }
            if (!val) {
                // translate all other falsies to None
                return null;
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
