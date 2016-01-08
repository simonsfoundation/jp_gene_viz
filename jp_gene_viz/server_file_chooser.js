/*
jQuery plugin to provide a simple user interface
to allow users to navigate server-side directories
and upload/download files.
*/

(function ($) {
    $.fn.server_file_chooser = function (top_path, top_listing, 
        select_callback, upload_callback, options) {
        var settings = $.extend({
            "dummy": 123
        }, options);
        var result = $('<div/>');
        var patharea = $('<div/>').html("(path)").appendTo(result);
        var listarea = $('<div/>').html("(listing)").appendTo(result);
        var on_click_maker = function(path, entry) {
            var path_copy = path.slice();
            return function() {
                select_callback(path_copy, entry);
                return false;
            };
        };
        var layout = function (path, listing) {
            debugger;
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
        return result
    };

    $.fn.server_file_chooser.example = function (element) {
        debugger;
        var output_area = $("<pre/>").html("(Output will go here)");
        element.append(output_area);
        var path = ["first", "second"];
        var listing = [
            ["index.html", "file"],
            ["js", "folder"],
            ["README.txt", "file"],
            ["css", "folder"]
        ];
        var select_callback = function (path, entry) {
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
        var chooser = element.server_file_chooser(path, listing, select_callback);
        element.append(chooser);
        return element;
    };
})(jQuery);