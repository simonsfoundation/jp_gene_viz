
/*
jQuery plugin for sequence motifs.

$(canvas).sequence_motif(width, height, columns, options)

Columns represent stacks of letters with from bottom to top.

Structure follows: https://learn.jquery.com/plugins/basic-plugin-creation/
*/

(function ($) {
    $.fn.sequence_motif = function (width, height, columns, options) {
        debugger;
        var that = this;
        // Get setttings from options or default values.
        var settings = $.extend({
            "letters": {"A": "green", "C": "blue", "T": "red", "G": "darkkhaki"},
            "ylabel": "bits",
            "leftlabel": "5'",
            "rightlabel": "3'",
            "x": 0,
            "y": 0,
            "bgcolor": "white",
            "border": 8,
            "labelfont": "10px Arial",
            "letterfont": "30px Courier",
            "fontpixelheight": 18,
        }, options);
        // collect stats on columns
        var maxOffset = 0.0;
        var ncolumns = columns.length;
        for (var ncolumn = 0; ncolumn < ncolumns; ncolumn++) {
            var totalweight = 0.0;
            var column = columns[ncolumn];
            for (var nletter = 0; nletter < column.length; nletter++ ) {
                var info = column[nletter];
                var letter = info[0];
                var weight = info[1];
                totalweight += weight;
            }
            if (totalweight > maxOffset) {
                maxOffset = totalweight;
            }
        }
        var ctx = that[0].getContext("2d");
        ctx.save();
        // draw the background
        ctx.translate(settings.x, settings.y);
        ctx.fillStyle = settings.bgcolor;
        ctx.fillRect(0, 0, width, height);
        // draw the letters
        var columnx = settings.border;
        var columndelta = (width - settings.border)/ncolumns;
        var yheight = height - settings.border;
        ctx.font = settings.letterfont;
        for (var ncolumn = 0; ncolumn < ncolumns; ncolumn++) {
            var totalweight = 0.0;
            var column = columns[ncolumn];
            var lettery = yheight;
            var nletters = column.length;
            for (var nletter = 0; nletter < nletters; nletter++ ) {
                var info = column[nletter];
                var letter = info[0];
                var weight = info[1];
                totalweight += weight;
                ctx.save()
                ctx.fillStyle = settings.letters[letter];
                ctx.translate(columnx, lettery);
                var mt = ctx.measureText(letter);
                var scaley = (yheight * weight) / (settings.fontpixelheight * maxOffset);
                var letterwidth = mt.width;
                var scalex = columndelta / letterwidth;
                ctx.scale(scalex, scaley);
                ctx.fillText(letter, 0, 0)
                ctx.restore()
                lettery -= (weight * yheight) / maxOffset;
            }
            columnx += columndelta;
        }
        // deaw the labels
        ctx.save()
        ctx.fillStyle = "black";
        ctx.font = settings.labelfont;
        ctx.textAlign = "start";
        ctx.fillText(settings.leftlabel, 0, height);
        var ymark = (""+maxOffset).substring(0, 3);  // xxxx not quite right.
        ctx.fillText(ymark, 0, settings.border);
        ctx.textAlign = "end";
        ctx.fillText(settings.rightlabel, width, height);
        ctx.textAlign="center";
        ctx.translate(settings.border*0.7, height/2);
        ctx.rotate(-Math.PI/2);
        ctx.fillText(settings.ylabel, 0, 0);
        ctx.restore()     
        ctx.restore();
    };
    $.fn.sequence_motif.example = function (element) {
        debugger;
        var newcanvas = $('<canvas width="300", height="300"/>'); //.width("110px").height("110px");
        var options = {
            "ylabel": "count",
            "x": 10,
            "y": 10
        };
        // red fill for reference
        var ctx = newcanvas[0].getContext("2d");
        ctx.fillStyle = "#FF0000";
        ctx.fillRect(0, 0, 110, 110);
        var columns = [
        [["A", 0.2], ["C", 0.3], ["T", 0.5]],
        [["A", 0.3], ["C", 0.7]],
        [["T", 1.0]],
        [["A", 0.3], ["G", 0.3], ["T", 0.4]],
        [["A", 0.1], ["C", 0.2], ["G", 0.7]],
        ];
        newcanvas.sequence_motif(90, 50, columns, options);
        element.append(newcanvas);
    };
})(jQuery);