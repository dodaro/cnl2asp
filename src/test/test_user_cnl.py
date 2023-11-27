import unittest

from lark import Lark

from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.specification.problem import Problem
from cnl2asp.specification.signaturemanager import SignatureManager
from user_cnl2asp.user_cnl_builder import TreeInterpreter
from user_cnl2asp.user_cnl_parser import DynamicTransformer

parser = Lark(open('user_cnl2asp/user_cnl_grammar.lark', 'r').read())

class TestCnlPropositions(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        SignatureManager.signatures = []
        DynamicTransformer.problem = Problem()
        asp_converter: ASPConverter = ASPConverter()
        asp_converter.clear_support_variables()

    def assert_equal(self, grammar: str, problem_specification: str, output: str):
        interpreter = TreeInterpreter()
        interpreter.visit(parser.parse(grammar))
        parser_user_grammar = Lark(str(interpreter.grammar), propagate_positions=True)
        transformer = DynamicTransformer(interpreter.grammar.rule_functions)
        transformer.transform(parser_user_grammar.parse(problem_specification))
        asp_converter = ASPConverter()
        encoding = asp_converter.convert_problem(DynamicTransformer.problem)
        self.assertEqual(str(encoding).strip(), output)

    def test_base(self):
        input_string = '''
        [constraint]
        "It is forbidden that a" entity{body} "is" string{body}
        [choice]
        "Whenever there is a" test{body} "then we can have a" ENTITY{head} "for each" ENTITY{condition}
        [preference]
        "It is preferred that a" ENTITY{body} "is" ENTITY{body}
                    '''
        problem_specification = '''
        It is forbidden that a node is blue.
        It is preferred that a node is blue.
        It is preferred that a node is red.
        Whenever there is a nurse then we can have a shift for each day.'''
        output = ':- node(), blue().\n:~ node(), blue(). [1@1]\n:~ node(), red(). [1@1]\n{shift(): day()} :- nurse().'
        self.assert_equal(input_string, problem_specification, output)

    def test_import(self):
        input_string = '''
        import entity
        import explicit_definition_proposition
        [constraint]
        "It is forbidden that a" entity{body} "is" string{body}
        '''
        problem_specification = '''
        A node is identified by an id.
        It is forbidden that a node with id equal to 1 is blue.
        '''
        output = ':- node(1), blue().'
        self.assert_equal(input_string, problem_specification, output)

    def test_aggregate_support_rules(self):
        input_string = '''
        import explicit_definition_proposition
        [aggregate.operator.sum]
        sum: "sum"
        [aggregate]
        aggregate: "the" sum{aggregate.operator} "of" VALUE{aggregate.discriminant} "of" ENTITY{aggregate.body}
        [constraint]
        "It is forbidden that" aggregate{body} "is equal to 1"
        '''
        problem_specification = '''
        A node is identified by an id. 
        It is forbidden that the sum of id of node is equal to 1.'''
        output = ':- #sum{D: node(D)}.'
        self.assert_equal(input_string, problem_specification, output)

    def test_operation_support_rules(self):
        input_string = '''
        import explicit_definition_proposition
        [operation.operator.sum]
        sum: "sum"
        [operation]
        operation: "the" sum{aggregate.operator} "of" VALUE{operation.operand} "and" ENTITY{operation.operand}
        [constraint]
        "It is forbidden that" operation{body} "is equal to 1"
        '''
        problem_specification = '''
        A node is identified by an id. 
        It is forbidden that the sum of x and y is equal to 1.'''
        output = ':- "x" + "y".'
        self.assert_equal(input_string, problem_specification, output)

    def test_telingo_support_rules(self):
        input_string = '''
        import explicit_definition_proposition
        [operation.operator.previous]
        before: "before"
        [operation]
        operation: "the" VALUE{operation.operand} "is" before{operation.operator}
        [constraint]
        "It is forbidden that" operation{body}
        '''
        problem_specification = '''
        A node is identified by an id. 
        It is forbidden that the x is before.'''
        output = ':- &tel {< "x"}.'
        self.assert_equal(input_string, problem_specification, output)

    def test_aggregate_combined_operation_support_rules(self):
        input_string = '''
        import explicit_definition_proposition
        [aggregate.operator.sum]
        sum: "sum"
        [aggregate]
        aggregate: "the" sum{aggregate.operator} "of" VALUE{aggregate.discriminant} "of a" ENTITY{aggregate.body}
        [operation.operator.equality]
        equal: "equal to"
        [operation]
        operation: aggregate{operation.operand} "is" equal{operation.operator} VALUE{operation.operand}
        [constraint]
        "It is forbidden that" operation{body}
        '''
        problem_specification = '''
        A node is identified by an id. 
        It is forbidden that the sum of id of a node is equal to 1.'''
        output = ':- #sum{D: node(D)} = 1.'
        self.assert_equal(input_string, problem_specification, output)

    def test_closure_operators(self):
        input_string = '''
        import explicit_definition_proposition
        [operation.operator.conjunction]
        and: "and"
        [operation]
        operation: entity{operation.operand} (and{operation.operator} entity{operation.operand})+
        [constraint]
        "It is forbidden that there is" operation{body}
        '''
        problem_specification = '''
        It is forbidden that there is sun and rain and snow.'''
        output = ':- &tel {"sun" & "rain" & "snow"}.'
        self.assert_equal(input_string, problem_specification, output)

