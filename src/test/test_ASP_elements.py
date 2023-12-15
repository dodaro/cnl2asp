import unittest

from cnl2asp.ASP_elements.asp_aggregate import ASPAggregate
from cnl2asp.ASP_elements.asp_atom import ASPAtom
from cnl2asp.ASP_elements.asp_attribute import ASPAttribute
from cnl2asp.ASP_elements.asp_conjunction import ASPConjunction
from cnl2asp.ASP_elements.asp_encoding import ASPEncoding
from cnl2asp.ASP_elements.asp_operation import ASPOperation, ASPTemporalOperation
from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.ASP_elements.asp_rule import ASPRule, ASPRuleHead, ASPWeakConstraint
from cnl2asp.ASP_elements.asp_temporal_formula import ASPTemporalFormula
from cnl2asp.specification.aggregate_component import AggregateOperation
from cnl2asp.specification.attribute_component import AttributeOrigin
from cnl2asp.specification.operation_component import Operators

from cnl2asp.ASP_elements.asp_attribute import ASPValue
from cnl2asp.utility.utility import Utility


class TestASPElements(unittest.TestCase):

    def setUp(self) -> None:
        Utility.PRINT_WITH_FUNCTIONS = False

    def test_atom_to_string(self):
        atom = ASPAtom('test', [ASPAttribute('field', ASPValue('FIELD'))])
        self.assertEqual(str(atom), 'test(FIELD)', 'Incorrect atom print.')

    def test_conjunction_to_string(self):
        conjunction = ASPConjunction([ASPAtom('test', [ASPAttribute('field', ASPValue('FIELD'))]),
                                      ASPAtom('test2', [ASPAttribute('field', ASPValue('FIELD'))])])
        self.assertEqual(str(conjunction), 'test(FIELD), test2(FIELD)', 'Incorrect conjunction print.')

    def test_aggregate_to_string(self):
        conjunction = ASPConjunction([ASPAtom('test', [ASPAttribute('field', ASPValue('FIELD'))]),
                                      ASPAtom('test2', [ASPAttribute('field', ASPValue('FIELD'))])])
        aggregate = ASPAggregate(AggregateOperation.SUM, [ASPAttribute('discriminant', ASPValue('DISCRIMINANT'))],
                                 conjunction)
        self.assertEqual(str(aggregate),
                         '#sum{DISCRIMINANT: test(FIELD), test2(FIELD)}',
                         'Incorrect aggregate print.')

    def test_choice_to_string(self):
        condition = ASPConjunction([ASPAtom('condition', [ASPAttribute('field', ASPValue('FIELD'))]),
                                    ASPAtom('condition2', [ASPAttribute('field', ASPValue('FIELD'))])])
        new_knowledge = ASPAtom('head', [ASPAttribute('field', ASPValue('FIELD'))])
        head = ASPRuleHead(new_knowledge, condition)
        body = ASPConjunction([ASPAtom('body', [ASPAttribute('field', ASPValue('FIELD'))]),
                               ASPAtom('body2', [ASPAttribute('field', ASPValue('FIELD'))])])
        rule = ASPRule(body, [head])
        # choice without cardinality
        self.assertEqual(str(rule),
                         '{head(FIELD): condition(FIELD), condition2(FIELD)} :- body(FIELD), body2(FIELD).\n',
                         'Incorrect choice without cardinality print.')

    def test_choice_with_cardinality_to_string(self):
        condition = ASPConjunction([ASPAtom('condition', [ASPAttribute('field', ASPValue('FIELD'))]),
                                    ASPAtom('condition2', [ASPAttribute('field', ASPValue('FIELD'))])])
        new_knowledge = ASPAtom('head', [ASPAttribute('field', ASPValue('FIELD'))])
        head = ASPRuleHead(new_knowledge, condition)
        body = ASPConjunction([ASPAtom('body', [ASPAttribute('field', ASPValue('FIELD'))]),
                               ASPAtom('body2', [ASPAttribute('field', ASPValue('FIELD'))])])
        # choice with cardinality
        rule = ASPRule(body, [head], (1, 1))
        self.assertEqual(str(rule),
                         '1 <= {head(FIELD): condition(FIELD), condition2(FIELD)} <= 1 :- body(FIELD), body2(FIELD).\n',
                         'Incorrect choice with cardinality print.')

    def test_assignment_to_string(self):
        body = ASPConjunction([ASPAtom('body', [ASPAttribute('field', ASPValue('FIELD'))]),
                               ASPAtom('body2', [ASPAttribute('field', ASPValue('FIELD'))])])
        # assignment
        rule = ASPRule(body, [ASPRuleHead(ASPAtom('head', [ASPAttribute('field', ASPValue('FIELD'))]))])
        self.assertEqual(str(rule),
                         'head(FIELD) :- body(FIELD), body2(FIELD).\n',
                         'Incorrect assignment print.')

    def test_constraint_to_string(self):
        body = ASPConjunction([ASPAtom('body', [ASPAttribute('field', ASPValue('FIELD'))]),
                               ASPAtom('body2', [ASPAttribute('field', ASPValue('FIELD'))])])
        # constraint
        rule = ASPRule(body)
        self.assertEqual(str(rule),
                         ':- body(FIELD), body2(FIELD).\n',
                         'Incorrect constraint print.')

    def test_program_to_string(self):
        condition = ASPConjunction([ASPAtom('condition', [ASPAttribute('field', ASPValue('FIELD'))]),
                                    ASPAtom('condition2', [ASPAttribute('field', ASPValue('FIELD'))])])
        new_knowledge = ASPAtom('head', [ASPAttribute('field', ASPValue('FIELD'))])
        head = ASPRuleHead(new_knowledge, condition)
        body = ASPConjunction([ASPAtom('body', [ASPAttribute('field', ASPValue('FIELD'))]),
                               ASPAtom('body2', [ASPAttribute('field', ASPValue('FIELD'))])])
        rule = ASPRule(body, [head])
        program = ASPProgram()
        program.add_rule(rule)

        encoding = ASPEncoding()
        encoding.add_program(program)
        encoding.add_constant(('time', '10'))
        self.assertEqual(str(encoding).strip(),
                         '#const time = 10.\n'
                         '{head(FIELD): condition(FIELD), condition2(FIELD)} :- body(FIELD), body2(FIELD).',
                         'Incorrect choice without cardinality print.')

    def test_weak_constraint(self):
        weak_constraint = ASPWeakConstraint(
            ASPConjunction([ASPAtom('test', [ASPAttribute('field', ASPValue('FIELD'))])]),
            1, 1, [ASPAttribute('key', ASPValue('KEY'))])
        self.assertEqual(str(weak_constraint),
                         ':~ test(FIELD). [1@1,KEY]\n')

    def test_asp_operation(self):
        operation = ASPOperation(Operators.SUM, ASPValue('1'), ASPValue('2'), ASPValue('3'))
        self.assertEqual(str(operation), '1 + 2 + 3')

    def test_print_with_functions(self):
        Utility.PRINT_WITH_FUNCTIONS = True
        atom = ASPAtom('atom1', [ASPAttribute('field1', ASPValue('FIELD'), AttributeOrigin('atom2')),
                                 ASPAttribute('field2', ASPValue('FIELD'),
                                              AttributeOrigin('atom2', AttributeOrigin('atom3'))),
                                 ASPAttribute('field3', ASPValue('FIELD'), AttributeOrigin('atom2',
                                                                                           AttributeOrigin('atom3',
                                                                                                           AttributeOrigin(
                                                                                                               'atom4')))),
                                 ASPAttribute('field4', ASPValue('FIELD'), AttributeOrigin('atom1'))])
        self.assertEqual(str(atom), 'atom1(atom2(FIELD,atom3(FIELD,atom4(FIELD))),FIELD)')

    def test_temporal_on_single_atom(self):
        atom_before = ASPAtom('atom_before', [ASPAttribute('field', ASPValue('FIELD'), AttributeOrigin('atom_before'))],
                              is_before=True)
        atom_after = ASPAtom('atom_after', [ASPAttribute('field', ASPValue('FIELD'), AttributeOrigin('atom_after'))],
                             is_after=True)
        atom_initial = ASPAtom('atom_initial',
                               [ASPAttribute('field', ASPValue('FIELD'), AttributeOrigin('atom_after'))],
                               is_initial=True)
        self.assertEqual(str(atom_before), '\'atom_before(FIELD)')
        self.assertEqual(str(atom_after), 'atom_after\'(FIELD)')
        self.assertEqual(str(atom_initial), '_atom_initial(FIELD)')

    def test_temporal_operations(self):
        operation1 = ASPTemporalOperation(Operators.CONJUNCTION, 'a', 'b')
        operation2 = ASPTemporalOperation(Operators.EQUIVALENCE, 'a', operation1)
        operation3 = ASPTemporalOperation(Operators.NEGATION, 'a')
        self.assertEqual(str(operation1), 'a & b')
        self.assertEqual(str(operation2), 'a <> (a & b)')
        self.assertEqual(str(operation3), '~ a')

    def test_temporal_formulas(self):
        atom = ASPAtom('atom', [ASPAttribute('field', ASPValue('FIELD'), AttributeOrigin('atom'))])
        atom2 = ASPAtom('atom2', [ASPAttribute('field', ASPValue('FIELD'), AttributeOrigin('atom2'))])
        temporal_formula1 = ASPTemporalFormula([ASPTemporalOperation(Operators.CONJUNCTION, 'a', 'b')])
        self.assertEqual(str(temporal_formula1), '&tel {a & b}')

        temporal_formula2 = ASPTemporalFormula([ASPTemporalOperation(Operators.CONJUNCTION, atom, 'b')])
        self.assertEqual(str(temporal_formula2), '&tel {atom(FIELD) & b}')

        atom.is_after = True
        temporal_formula3 = ASPTemporalFormula([ASPTemporalOperation(Operators.DISJUNCTION, atom, atom2)])
        self.assertEqual(str(temporal_formula3), '&tel {atom\'(FIELD) | atom2(FIELD)}')

        temporal_formula4 = ASPTemporalFormula([ASPTemporalOperation(Operators.PREVIOUS,
                                                                     ASPTemporalOperation(Operators.CONJUNCTION, 'a', 'b'))])
        self.assertEqual(str(temporal_formula4), '&tel {< (a & b)}')

        atom.is_after = False
        temporal_formula5 = ASPTemporalFormula([ASPTemporalOperation(Operators.PREVIOUS,
                                                                     ASPTemporalOperation(Operators.EQUIVALENCE, atom,
                                                                                          ASPTemporalOperation(Operators.DISJUNCTION, 'a', 'b')))])
        self.assertEqual(str(temporal_formula5), '&tel {< (atom(FIELD) <> (a | b))}')

    def test_multiple_programs(self):
        atom = ASPAtom('atom', [ASPAttribute('field', ASPValue('FIELD'), AttributeOrigin('atom'))])
        encoding = ASPEncoding()
        program_base = ASPProgram('base')
        program_base.add_rule(ASPRule(ASPConjunction([atom])))
        program_dynamic = ASPProgram('dynamic')
        program_dynamic.add_rule(ASPRule(ASPConjunction([atom])))

        encoding.add_program(program_base)
        encoding.add_program(program_dynamic)
        self.assertEqual(str(encoding).strip(), '''#program base.\n:- atom(FIELD).\n\n#program dynamic.\n:- atom(FIELD).''')

if __name__ == '__main__':
    unittest.main()
