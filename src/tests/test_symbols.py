import unittest

from cnl2asp.cnl2asp import Cnl2asp, Symbol, SymbolType


class TestCnlPropositions(unittest.TestCase):

    def setUp(self):
        pass

    def get_symbols(self, input_text):
        return Cnl2asp(input_text).get_symbols()

    def test_get_symbol(self):
        text = 'A node is identified by an id.'
        self.assertIn(Symbol('node', ['id'], ['id'], SymbolType.DEFAULT), self.get_symbols(text))
        self.assertNotIn(Symbol('Node', ['id'], ['id'], SymbolType.DEFAULT), self.get_symbols(text))
        self.assertNotIn(Symbol('node', [], ['id'], SymbolType.DEFAULT), self.get_symbols(text))

        text = 'A parent is identified by an id.' \
               'A child is identified by a parent, and by an id.'
        parent_symbol = Symbol('parent', ['id'], ['id'], SymbolType.DEFAULT)
        self.assertIn(Symbol('child', [parent_symbol, 'id'], [parent_symbol, 'id'],
                             SymbolType.DEFAULT), self.get_symbols(text))

    def test_symbols_arity(self):
        text = 'A test is identified by an id.'
        self.assertEqual(self.get_symbols(text)[0].get_arity(), 1)
        text = 'A test is identified by an first, and has a second.'
        self.assertEqual(self.get_symbols(text)[0].get_arity(), 2)
        text = 'A test is identified by an first, and by a second.'
        self.assertEqual(self.get_symbols(text)[0].get_arity(), 2)
        text = 'A parent is identified by an first, and by a second.' \
               'A child is identified by a parent.'
        self.assertEqual(self.get_symbols(text)[1].get_arity(), 2)
        self.assertEqual(self.get_symbols(text)[1].get_arity(True), 1)