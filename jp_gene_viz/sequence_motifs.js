
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
            "letters": {"A": "green", "C": "blue", "T": "red", "G": "orange"},
            "ylabel": "bits",
            "leftlabel": "5'",
            "rightlabel": "3'",
            "x": 0,
            "y": 0,
            "bgcolor": "white",
            "boundary": "cornsilk",
            "border": 8,
            "labelfont": "10px Arial",
            "letterfont": "30px Arial",
            "fontpixelheight": 24,
            "yMaximumDefault": 0,
        }, options);
        // collect stats on columns
        var maxOffset = settings.yMaximumDefault;
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
        ctx.strokeStyle = settings.boundary;
        ctx.fillRect(0, 0, width, height);
        ctx.strokeRect(0, 0, width, height);
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
            ctx.save();
            ctx.fillStyle = "black";
            ctx.textAlign = "center";
            ctx.font = settings.labelfont;
            ctx.fillText("" + (ncolumn + 1), columnx + columndelta/2, height);
            ctx.restore();
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
        return that;
    };

    // example usage and test case: jQuery.fn.sequence_motif.example($("#canvas"))
    $.fn.sequence_motif.example = function (element) {
        debugger;
        var newcanvas = $('<canvas width="300" height="300"/>'); //.width("110px").height("110px");
        var options = {
            "ylabel": "count",
            "x": 10,
            "y": 10
        };
        // light grey fill for reference
        var ctx = newcanvas[0].getContext("2d");
        ctx.fillStyle = "#dddddd";
        ctx.fillRect(0, 0, 300, 300);
        var columns = [
        [["A", 2], ["C", 3], ["T", 5]],
        [["A", 3], ["C", 7]],
        [["T", 10]],
        [["A", 3], ["G", 3], ["T", 4]],
        [["A", 1], ["C", 2], ["G", 7]],
        ];
        newcanvas.sequence_motif(190, 111, columns, options);
        element.append(newcanvas);
    };
})(jQuery);
