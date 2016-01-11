/*
jQuery plugin to provide a simple user interface
to allow users to navigate server-side directories
and upload/download files.

The upload feature requires the simple_file_chooser plugin.

See example below for usage.
*/

(function ($) {
    $.fn.server_file_chooser = function (top_path, top_listing, 
        select_callback, upload_callback, options) {
        var settings = $.extend({
            "pathstyle": {"border-style": "solid", "padding-left": "10px"},
            "liststyle": {"padding-left": "20px"}
        }, options);
        var result = $('<div/>');
        var patharea = $('<div/>').html("(path)").appendTo(result);
        if (settings.pathstyle) {
            patharea.css(settings.pathstyle);
        }
        var listarea = $('<div/>').html("(listing)").appendTo(result);
        if (settings.liststyle) {
            listarea.css(settings.liststyle)
        }
        var on_click_maker = function(path, entry) {
            var path_copy = path.slice();
            return function() {
                select_callback(path_copy, entry);
                return false;
            };
        };
        var on_upload_maker = function(path) {
            var upload_path = path.slice();
            return function(data) {
                return upload_callback(upload_path, data);
            };
        };
        var layout = function (path, listing) {
            patharea.empty();
            listarea.empty();
            patharea.append("\u21DB &nbsp;")
            var ancestors = [];
            for (var i=0; i<path.length; i++) {
                var name = path[i];
                var onclick = on_click_maker(ancestors, [name, "folder"]);
                $('<a href="#"/>').
                html(path[i]).
                click(onclick).
                appendTo(patharea);
                $('<b> / </b>').appendTo(patharea);
                ancestors.push(name);
            }
            // ad upload option, if appropriate
            if (upload_callback) {
                var on_upload = on_upload_maker(path);
                var on_upload_button = patharea.simple_upload_button(on_upload);
                patharea.append($("<div>upload </div>").append(on_upload_button));
            }
            for (var i=0; i<listing.length; i++) {
                var item = listing[i];
                var name = item[0];
                var kind = item[1];
                var itemdiv = $("<div/>");
                var onclick = on_click_maker(path, item);
                $('<a href="#"/>').
                html(name).
                click(onclick).
                appendTo(itemdiv);
                if (kind == "folder") {
                    $("<b>&nbsp; \u21DA </b>").appendTo(itemdiv);
                }
                itemdiv.appendTo(listarea);
            }
        };
        layout(top_path, top_listing);
        result.layout = layout;
        return result;
    };

    $.fn.server_file_chooser.example = function (element) {
        var output_area = $("<pre/>").html("(Output will go here)");
        var path = ["first", "second"];
        var listing = [
            ["index.html", "file"],
            ["js", "folder"],
            ["README.txt", "file"],
            ["css", "folder"]
        ];
        var select_callback = function (path, entry) {
            output_area.empty();
            var message = "INVALID MESSAGE";
            var name = entry[0];
            var kind = entry[1];
            if (kind == "file") {
                message = "File chosen.";
            } else if (kind == "folder") {
                message = "Folder expanded";
                var newpath = path.slice();
                newpath.push(name);
                chooser.layout(newpath, listing);
            } else {
                message = 'UNKNOWN KIND ' + kind;
            }
            output_area.html(
                [path.join("/"),
                entry.join(" : "),
                message].join("\n")
                );
        };
        var upload_callback = function(path, data) {
            output_area.empty();
            output_area.append("<b>Output to " + path.join("/") + "</b>");
            output_area.append([
                "/ " + data.name,
                "type " + data.type,
                "size " + data.size,
                "===",
                "" + data.content
                ].join("\n"));
        };
        var chooser = element.server_file_chooser(
            path, listing, select_callback, upload_callback);
        element.append(chooser);
        element.append(output_area);
        return element;
    };
})(jQuery);