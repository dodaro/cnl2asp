import unittest
from unittest.mock import patch

from cnl2asp.utility.utility import Utility
from lark import Lark

from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.parser.parser import CNLTransformer
from cnl2asp.specification.signaturemanager import SignatureManager

cnl_parser = Lark(open("cnl2asp/grammar.lark", "r").read())


class TestInductiveSignatures(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        Utility.DETECTING_SIGNATURES = True
        SignatureManager.signatures = []
        asp_converter: ASPConverter = ASPConverter()
        asp_converter.clear_support_variables()

    def _compute_asp(self, string: str) -> str:
        problem = CNLTransformer().transform(cnl_parser.parse(string))
        asp_converter: ASPConverter = ASPConverter()
        program: ASPProgram = problem.convert(asp_converter)
        return str(program)

    def assert_equal(self, input_string, expected_output):
        SignatureManager.signatures = []
        asp = self._compute_asp(input_string)
        self.assertEqual(asp.strip(), expected_output)

    def test_simple_choice(self):
        self.assert_equal('Whenever there is an entity1 X, then we can have a relation1.',
                          '{relation1(X)} :- entity1(X).')
        self.assert_equal('Whenever there is an entity1 with field1 X, with field2 Y, then we can have a relation1.',
                          '{relation1(X,Y)} :- entity1(X,Y).')
        self.assert_equal('Every entity1 with field1 X can be relation1.',
                          '{relation1(X)} :- entity1(X).')
        self.assert_equal('Whenever there is an entity1 X, whenever there is an entity2 Y, then we can have a relation1.',
                          '{relation1(X,Y)} :- entity1(X), entity2(Y).')
        self.assert_equal('Whenever there is an entity1 with field1 X, with field2 Y, whenever there is an entity2 Z, then we can have a relation1.',
                          '{relation1(X,Y,Z)} :- entity1(X,Y), entity2(Z).')
        self.assert_equal('Whenever there is an entity1 with field1 X, with field2 Y, whenever there is an entity2 Z, then we can have a relation1 with field K.',
                          '{relation1(K,X,Y,Z)} :- entity1(X,Y), entity2(Z).')

    def test_simple_constraints(self):
        self.assert_equal('It is prohibited that there is an entity X.', ':- entity(X).')
        self.assert_equal('It is prohibited that there is an entity X, whenever there is an entity2 Y.', ':- entity(X), entity2(Y).')
        self.assert_equal('It is prohibited that the sum between X, and Y is equal to 3, whenever there is an entity1 X, whenever there is an entity2 Y.',
                          ':- (X + Y) = 3, entity1(X), entity2(Y).')
        self.assert_equal(
            'It is prohibited that the sum between the field X of the entity1 X, and the field Y of the entity2 Y is equal to 3, whenever there is an entity1 X, whenever there is an entity2 Y.',
            ':- (X + Y) = 3, entity1(X), entity2(Y).')
        self.assert_equal(
            'It is prohibited that the number of an entity1 occurrences is equal to 1.',
            ':- #count{entity1(NTTY1_D): entity1(NTTY1_D)} = 1.')
        self.assert_equal(
            'It is prohibited that the number of field of an entity is equal to 1.',
            ':- #count{FLD: entity(FLD)} = 1.')
        self.assert_equal(
            'It is prohibited that the number of field1 that have an entity1 is equal to 1.',
            ':- #count{FLD1: entity1(FLD1)} = 1.')
        self.assert_equal(
            'It is prohibited that the number of field1 where an entity1 X is entity2 is equal to 1.',
            ':- entity1(X), #count{FLD1: entity2(FLD1)} = 1.')  # TODO fix entity1 as attribute of entity2

    def test_combined(self):
        self.assert_equal('Whenever there is an entity1 X, then we can have a relation1.'
                          'It is prohibited that there is an entity1 with field1 X.',
                          '{relation1(X)} :- entity1(X,_).\n:- entity1(_,X).')
