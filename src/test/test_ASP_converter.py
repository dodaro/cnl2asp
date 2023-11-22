import unittest

from cnl2asp.ASP_elements.asp_aggregate import ASPAggregate
from cnl2asp.ASP_elements.asp_atom import ASPAtom
from cnl2asp.ASP_elements.asp_attribute import ASPAttribute
from cnl2asp.ASP_elements.asp_conjunction import ASPConjunction
from cnl2asp.proposition.aggregate_component import AggregateComponent, AggregateOperation
from cnl2asp.proposition.signaturemanager import SignatureManager
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.proposition.attribute_component import AttributeComponent, AttributeOrigin
from cnl2asp.proposition.entity_component import EntityComponent
from cnl2asp.proposition.relation_component import RelationComponent

from cnl2asp.ASP_elements.asp_attribute import ASPValue
from cnl2asp.proposition.attribute_component import ValueComponent
from cnl2asp.utility.utility import Utility

asp_converter = ASPConverter()
test_signature_manager = SignatureManager().add_signature(EntityComponent('test', '',
                                                                          [AttributeComponent('key',
                                                                                              ValueComponent('_'))],
                                                                          [AttributeComponent('field',
                                                                                              ValueComponent('_')),
                                                                           AttributeComponent('field2',
                                                                                              ValueComponent('_'))]))


class TestASPConverter(unittest.TestCase):

    def test_convert_entity(self):
        entity_component = EntityComponent('test', '', [AttributeComponent('key', ValueComponent('KEY'))],
                                           [AttributeComponent('field', ValueComponent('FIELD')),
                                            AttributeComponent('field2', ValueComponent('_'))])
        asp_atom = ASPAtom('test', [ASPAttribute('key', ASPValue('KEY')),
                                    ASPAttribute('field', ASPValue('FIELD')), ASPAttribute('field2', ASPValue('_'))])
        asp_converter = ASPConverter()
        atom = asp_converter.convert_entity(entity_component)
        self.assertEqual(atom, asp_atom)

    def test_convert_aggregate(self):
        operation = AggregateOperation.COUNT
        discriminant = [AttributeComponent('TEST_DISCR', ValueComponent('TST_DSCR'))]
        entity_component = EntityComponent('test', '', [AttributeComponent('key', ValueComponent('KEY'))],
                                           [AttributeComponent('field', ValueComponent('FIELD')),
                                            AttributeComponent('TEST_DISCR', ValueComponent('_'))])
        aggregate = AggregateComponent(operation, discriminant, [entity_component])
        asp_converter = ASPConverter()
        asp_atom = ASPAtom('test', [ASPAttribute('key', ASPValue('KEY')),
                                    ASPAttribute('field', ASPValue('FIELD')), ASPAttribute('TEST_DISCR', ASPValue('TST_DSCR'))])
        asp_aggregate = ASPAggregate(AggregateOperation.COUNT, [ASPAttribute('TEST_DISCR', ASPValue('TST_DSCR'))],
                                     ASPConjunction([asp_atom]))
        self.assertEqual(str(aggregate.convert(asp_converter)),
                         asp_aggregate.__str__())

    def test_link_two_atoms(self):
        entity_1 = EntityComponent('entity_1', '', [], [AttributeComponent('field1', ValueComponent(Utility.ASP_NULL_VALUE), AttributeOrigin('entity_1'))])
        entity_2 = EntityComponent('entity_2', '', [], [AttributeComponent('field1', ValueComponent(Utility.ASP_NULL_VALUE), AttributeOrigin('entity_1')),
                                                        AttributeComponent('field2', ValueComponent(Utility.ASP_NULL_VALUE), AttributeOrigin('entity_1'))])
        relation = RelationComponent(entity_1, entity_2)
        asp_converter = ASPConverter()
        atom_1 = entity_1.convert(asp_converter)
        self.assertEqual(str(atom_1), 'entity_1(_)')
        atom_2 = entity_2.convert(asp_converter)
        self.assertEqual(str(atom_2), 'entity_2(_,_)')
        asp_converter._link_two_atoms(relation, atom_1, atom_2)
        self.assertEqual(str(atom_1), 'entity_1(NTTY_2_FLD1)')
        self.assertEqual(str(atom_2), 'entity_2(NTTY_2_FLD1,_)')


if __name__ == '__main__':
    unittest.main()
