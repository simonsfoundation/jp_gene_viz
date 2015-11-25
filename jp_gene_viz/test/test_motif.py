
import unittest
import StringIO
import numpy as np

from .. import motif_data

EXAMPLE_FILE = """
MEME version 4.4

ALPHABET= ACGT

strands: + -

Background letter frequencies (from uniform background):
A 0.25000 C 0.25000 G 0.25000 T 0.25000 

MOTIF BatfIrf4Th17f_1 Batf::Irf4

letter-probability matrix: alength= 4 w= 18 nsites= 425 E= 2.6e-297
0.176471 0.115294 0.080000 0.628235 
0.054118 0.181176 0.529412 0.235294 
0.903529 0.000000 0.007059 0.089412 
0.032941 0.355294 0.496471 0.115294 
0.004706 0.000000 0.016471 0.978824 
0.087059 0.877647 0.028235 0.007059 
1.000000 0.000000 0.000000 0.000000 
0.249412 0.051765 0.152941 0.545882 
0.550588 0.080000 0.000000 0.369412 
0.270588 0.211765 0.131765 0.385882 
0.202353 0.402353 0.117647 0.277647 
0.242353 0.075294 0.470588 0.211765 
0.520000 0.089412 0.287059 0.103529 
0.411765 0.115294 0.364706 0.108235 
0.851765 0.089412 0.030588 0.028235 
0.265882 0.247059 0.378824 0.108235 
0.235294 0.268235 0.124706 0.371765 
0.301176 0.171765 0.301176 0.225882 

MOTIF M0107_1.01 Arid5b

letter-probability matrix: alength= 4 w= 8 nsites= 20 E= 0
  0.215558    0.305892    0.198985    0.279564  
  0.497422    0.067995    0.230313    0.204269  
  0.835696    0.067240    0.001646    0.095418  
  0.059111    0.062142    0.016600    0.862147  
  0.541039    0.077749    0.128187    0.253025  
  0.188467    0.310730    0.085535    0.415268  
  0.205969    0.319810    0.246590    0.227631  
  0.296771    0.189230    0.302766    0.211233  

"""

class TestMotif(unittest.TestCase):

    def test_collection(self):
        f = StringIO.StringIO(EXAMPLE_FILE)
        md = motif_data.MotifCollection()
        md.read_meme_file(f)
        motif = md["BatfIrf4Th17f_1"]
        self.assertEqual(motif.frequency_sequence[6, 2], 0.0)
        self.assertEqual(list(md.letter_order), list("ACGT"))

    def test_Motif(self):
        letters = "abcd"
        frequencies = [[1,0,0,0], [0.25,0.25,0.25,0.25]]
        m = motif_data.Motif(letters, frequencies)
        entropy = m.frequency_entropy()
        self.assertEqual(entropy[0].tolist(), [2,0,0,0])
        self.assertEqual(entropy[1].tolist(), [0] * 4)

    def test_columns(self):
        a = [[1, 2, 3, 4], [4, 2, 3, 1]]
        m = motif_data.Motif("ABCD", a)
        c = m.json_columns(entropy=False)
        expected = [
            [('A', 1), ('B', 2), ('C', 3), ('D', 4)], 
            [('D', 1), ('B', 2), ('C', 3), ('A', 4)]]
        self.assertEqual(c, expected)
