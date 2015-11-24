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
        assert self.letter_order is None, "cannot reset letter order."
        self.letter_order = letters

    def __setitem__(self, name, motif):
        "self[motif_name] = motif_object operation"
        self.name_to_motif[name] = motif

    def __getitem__(self, name):
        "self[motif_name]: retrieve a motif"
        return self.name_to_motif[name]

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
                for nrow in xrange(nrows):
                    rowstring = file.readline()
                    row = np.fromstring(rowstring, sep=" ")
                    row = row / np.sum(row)
                    frequencies[nrow] = row
                    frequencies_found = True
                if not frequencies_found:
                    raise ValueError("No motif frequencies found for "
                        + repr(motif_names))
                motif = Motif(self.letter_order, frequencies)
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
        (nrows, ncols) = frequency_sequence.shape
        assert len(letters) == ncols, "array and letters don't match " + repr((
            letters, ncols))
        self.letters = letters
        self.frequency_sequence = frequency_sequence
