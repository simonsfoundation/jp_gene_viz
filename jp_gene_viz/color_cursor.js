/*
jQuery plugin for a color arrow cursor over an element.

Based on
http://stackoverflow.com/questions/18779354/assign-color-to-mouse-cursor-using-css
*/

(function ($) {

    $.fn.color_cursor = function(color) {
        var that = this;
        var cvs = document.createElement("canvas");
        cvs.height = 16;
        cvs.width = 16;
        var ctx = cvs.getContext("2d");
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.moveTo(2, 12);
        ctx.lineTo(2, 2);
        ctx.lineTo(12, 2);
        ctx.moveTo(2, 2);
        ctx.lineTo(30, 30)    
        ctx.stroke();
        var url = cvs.toDataURL();
        that.css("cursor", "url(" + url + '), auto');
        return that;
    };

    $.fn.color_cursor_reset = function () {
        this.css("cursor", "");
        return this;
    };

    $.fn.color_cursor.example = function (element) {
        debugger;
        var d = $("<div>Cursor should be red over me. Click to reset.</div>")
            .color_cursor("red");
        var reset = function() {
            d.color_cursor_reset();
            d.html("Now the cursor should be normal");
        }
        d.click(reset);
        element.append(d);
        return element;
    };

})(jQuery)
