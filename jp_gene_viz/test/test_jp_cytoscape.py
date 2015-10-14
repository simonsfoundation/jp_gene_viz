import unittest
from jp_gene_viz import jp_cytoscape

def validate(f):
    return jp_cytoscape.validate_command(f)

class TestBasic(unittest.TestCase):

    def test_fn_call(self):
        c = jp_cytoscape.CommandMaker()
        f = c.fn()
        cmd = validate(f)
        self.assertEqual(["fun", "fn"], cmd)

    def test_fn_arg(self):
        c = jp_cytoscape.CommandMaker()
        f = c.remove("node")
        cmd = validate(f)
        self.assertEqual(["fun", "remove", "node"], cmd)

    def test_fn_dict(self):
        c = jp_cytoscape.CommandMaker()
        f = c.add("node", {"group": "nodes"})
        cmd = validate(f)
        self.assertEqual(["fun", "add", "node", {"group": "nodes"}], cmd)

    def test_fn_list(self):
        c = jp_cytoscape.CommandMaker()
        f = c.add("node", [{"group": "nodes"}])
        cmd = validate(f)
        self.assertEqual(["fun", "add", "node", ["list", {"group": "nodes"}]], cmd)

    def test_method(self):
        c = jp_cytoscape.CommandMaker()
        f = c.dd("#j").addClass("funny")
        cmd = validate(f)
        self.assertEqual(["method", ["fun", "dd", "#j"], "addClass", "funny"], cmd)

    def test_dollar(self):
        c = jp_cytoscape.CommandMaker()
        f = c.DOLLAR("#j").addClass("funny")
        cmd = validate(f)
        self.assertEqual(["method", ["fun", "$", "#j"], "addClass", "funny"], cmd)
