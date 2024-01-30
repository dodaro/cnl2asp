import unittest

from cnl2asp.cnl2asp import Cnl2asp
from cnl2asp.ASP_elements.solver.clingo import Clingo
from cnl2asp.ASP_elements.solver.clingo_result_parser import ClingoResultParser
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.proposition.signaturemanager import SignatureManager

class TestClingoResultParser(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        SignatureManager.signatures = []
        asp_converter: ASPConverter = ASPConverter()
        asp_converter.clear_support_variables()

    def compute_model(self, string: str) -> str:
        cnl2asp = Cnl2asp(string)
        asp_encoding = cnl2asp.compile()
        clingo = Clingo()
        clingo.load(str(asp_encoding))
        res = clingo.solve()
        clingo_res = ClingoResultParser(cnl2asp.parse_input(), res)
        return clingo_res.parse_model()

    def test_graph_coloring(self):
        model = self.compute_model('''A node goes from 1 to 3.
A color is one of red, green, blue.

Node 1 is connected to node X, where X is one of 2, 3.
Node 2 is connected to node X, where X is one of 1, 3.
Node 3 is connected to node X, where X is one of 1, 2.

Every node can be assigned to exactly 1 color.

It is required that when node X is connected to node Y then node X is not assigned to color C and also node Y is not assigned to color C.''')
        self.assertEqual(model, '''There is node 1.
There is node 2.
There is node 3.
Node 2 is connected to node 1.
Node 3 is connected to node 1.
Node 1 is connected to node 2.
Node 3 is connected to node 2.
Node 1 is connected to node 3.
Node 2 is connected to node 3.
There is color "red".
There is color "green".
There is color "blue".
Node 3 is assigned to color "red".
Node 2 is assigned to color "green".
Node 1 is assigned to color "blue".
''')