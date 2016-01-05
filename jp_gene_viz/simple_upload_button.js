
/*
jQuery plugin for a simple upload button that
sends file information and contents to a callback.

Structure follows: https://learn.jquery.com/plugins/basic-plugin-creation/
Logic from http://www.html5rocks.com/en/tutorials/file/dndfiles/
*/

(function($) {
    $.fn.simple_upload_button = function (callback, options) {
        var settings = $.extend({
            "size_limit": 10000000
        })
        var result = $('<input type="file"/>');
        result.on("change", function(event) {
            debugger;
            var file = this.files[0];
            if (file) {
                var data = {
                    "name": file.name,
                    "type": file.type,
                    "content": null,
                    "size": file.size
                };
                if (settings.size_limit && (settings.size_limit > data.size)) {
                    var reader = new FileReader();
                    reader.onload = function (event) {
                        debugger;
                        data["content"] = event.target.result;
                        // callback with content (not too big)
                        callback(data);
                    };
                    reader.readAsText(file);
                } else {
                    // invoke callback with no content (too big).
                    callback(data);
                }
            }
        });
        return result;
    }

    $.fn.simple_upload_button.example = function(element) {
        var output_area = $("<pre/>");
        element.append(output_area);
        var callback_function = function(data) {
            output_area.html([
                "name " + data.name,
                "type " + data.type,
                "size " + data.size,
                "===",
                "" + data.content
                ].join("\n"));
        };
        var upload_button = element.simple_upload_button(callback_function);
        element.append(upload_button);
        return element;
    }
})(jQuery)
