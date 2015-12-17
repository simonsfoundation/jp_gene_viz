"""
Functionality to manipulate sequence motif data from MEME
file formats (for example mm9_em.meme for mouse genome motifs).
"""

import numpy as np
import re


class MotifCollection(object):

    """
    A collection of named motifs on a common alphabet.
    """

    def __init__(self):
        self.letter_order = None
        self.name_to_motif = {}

    def set_order(self, letters):
        #assert self.letter_order is None or self.letter_order==letters, "cannot reset letter order."
        self.letter_order = letters

    def __setitem__(self, name, motif):
        "self[motif_name] = motif_object operation"
        self.name_to_motif[name] = motif

    def __getitem__(self, name):
        "self[motif_name]: retrieve a motif"
        return self.name_to_motif[name]

    def get(self, name, default=None):
        return self.name_to_motif.get(name, default)

    def read_meme_file(self, file):
        """
        Read a MEME format file
        as described in http://meme-suite.org/doc/meme-format.html
        """
        # look for header (don't check the version)
        line = file.readline()
        while line and not line.startswith("MEME"):
            line = line.strip()
            if line:
                raise ValueError("Bad file header: " + repr(line))
            line = file.readline()
        # parse expected sections of file
        line = file.readline()
        while line:
            sline = line.strip()
            if sline == "":
                # skip white lines between sections.
                pass
            elif sline.startswith("ALPHABET="):
                [_, letters] = sline.split("=")
                self.set_order(letters.strip())
            elif sline.startswith("strands"):
                pass  # Ignore the strands line? XXXXX
            elif sline.startswith("Background"):
                # read and ignore the background line for now XXXXX
                ignored = file.readline()
            elif sline.startswith("MOTIF"):
                assert self.letter_order is not None, (
                    "Cannot parse MOTIF before alphabet: " + repr(sline))
                motifsplit = sline.split()
                assert motifsplit[0] == "MOTIF"
                motif_names = motifsplit[1:]
                assert len(motif_names) > 0
                # look for motif components
                line = file.readline()
                frequencies_found = False
                # look for "letter-probability" line
                while line and not line.startswith("letter-probability"):
                    if line.strip():
                        raise ValueError("expected letter-probability " +
                            repr(line))
                    line = file.readline()
                # parse line like 
                # "letter-probability matrix: alength= 4 w= 18 nsites= 425 E= 2.6e-297"
                regex = (
                    "letter-probability" +
                    "\s+" + "matrix:" +
                    "\s+" + "alength=" + "\s*" + "(\d+)" +
                    "\s+" + "w=" + "\s*" + "(\d+)"
                    )  # ignore the rest of the line for now.
                p = re.compile(regex)
                m = p.match(line)
                ncolumns = int(m.group(1).strip())
                nrows = int(m.group(2).strip())
                frequencies = np.zeros((nrows, ncolumns))
                if m is None:
                    raise ValueError("failed to match probability line: "
                        + repr(line))
                for nrow in range(nrows):
                    rowstring = file.readline()
                    row = np.fromstring(rowstring, sep=" ")
                    row = row / np.sum(row)
                    frequencies[nrow] = row
                    frequencies_found = True
                if not frequencies_found:
                    raise ValueError("No motif frequencies found for "
                        + repr(motif_names))
                motif = Motif(self.letter_order, frequencies)
                motif.names = motif_names
                for name in motif_names:
                    self[name] = motif
            else:
                raise ValueError("Unexpected line format " +
                    repr(sline)) 
                # get the next line
            line = file.readline()
        return self


class Motif(object):

    """Motif object encapsulations."""

    def __init__(self, letters, frequency_sequence):
        """
        Create a motif encapulation from a letter sequence
        and a 2d array of frequencies for letter positions.
        """
        frequency_sequence = np.array(frequency_sequence, np.float)
        (nrows, ncols) = frequency_sequence.shape
        assert len(letters) == ncols, "array and letters don't match " + repr((
            letters, ncols))
        self.letters = letters
        self.frequency_sequence = frequency_sequence
        self.names = None   # name set externally

    def frequency_entropy(self, epsilon=0.001):
        """
        Return frequencies weighted by entropy:
        http://www.nature.com/nbt/journal/v24/n4/full/nbt0406-423.html.
        """
        f = self.frequency_sequence
        near_zero = (np.abs(f) < epsilon)
        with np.errstate(all="ignore"):
            plogp = f * np.log2(f)
        entropy = np.where(near_zero, 0, plogp)
        total = entropy.sum(1)
        rescale = np.log2(len(self.letters)) + total
        result = f * rescale.reshape(len(f), 1)
        return result

    def json_columns(self, entropy=True, epsilon=0.05):
        """
        Create a JSON array as expected by the sequence_motif jQuery plugin.
        """
        letters = self.letters
        data = self.frequency_sequence
        if entropy:
            data = self.frequency_entropy()
        result = []
        for d in data:
            column = []
            lf = sorted(zip(d, letters))
            for (frequency, letter) in lf:
                if frequency > epsilon:
                    column.append([letter, frequency])
            result.append(column)
        return result

    def canvas(self, width=None, height=None, entropy=True):
        """
        Make a jsproxy canvas widget which draws the motif using sequence_motif.js.
        """
        from jp_gene_viz import js_proxy
        js_proxy.load_javascript_support()
        w = js_proxy.ProxyWidget()
        elt = w.element()
        return self.add_canvas(w, elt,
            width=width, height=height, entropy=entropy,
            x=5, y=5)

    def add_canvas(self, proxy_widget, dom_element_ref, 
            width=None, height=None, x=0, y=0, entropy=True, 
            dwidth=30, dheight=40, ylabel=None):
        from jp_gene_viz import js_context
        js_context.load_if_not_loaded(["sequence_motifs.js"])
        columns = self.json_columns(entropy=entropy)
        (ncolumns, nrows) = self.frequency_sequence.shape
        if width is None:
            width = ncolumns * dwidth
        if height is None:
            height = nrows * dheight
        w = proxy_widget
        elt = dom_element_ref
        canvas_tag = '<canvas width="%s" height="%s"/>' % (
            int(width + x * 2), int(height + y * 2))
        options = {
            "x": x,
            "y": y,
        }
        if ylabel is not None:
            options["ylabel"] = ylabel
        else:
            if not entropy:
                options["ylabel"] = "probability"
            else:
                options["ylabel"] = "bits"
                options["yMaximumDefault"] = 2.0
        jQuery = w.window().jQuery
        new_canvas = jQuery(canvas_tag)
        w(elt.append(new_canvas.sequence_motif(width, height, columns, options)))
        w.flush()
        return w
