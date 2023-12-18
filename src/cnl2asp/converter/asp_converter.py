from __future__ import annotations

import random
import re

from cnl2asp.parser.parser import CNLTransformer
from multipledispatch import dispatch

from cnl2asp.ASP_elements.asp_aggregate import ASPAggregate
from cnl2asp.ASP_elements.asp_atom import ASPAtom
from cnl2asp.ASP_elements.asp_attribute import ASPAttribute, RangeASPValue
from cnl2asp.ASP_elements.asp_conjunction import ASPConjunction
from cnl2asp.ASP_elements.asp_operation import ASPOperation, ASPAngleOperation
from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.ASP_elements.asp_rule import ASPRule, ASPRuleHead, ASPWeakConstraint
from cnl2asp.ASP_elements.asp_attribute import ASPValue

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.exception.cnl2asp_exceptions import AttributeNotFound, EntityNotFound, CompilationError

from cnl2asp.proposition.constant_component import ConstantComponent
from cnl2asp.proposition.entity_component import EntityComponent, TemporalEntityComponent
from cnl2asp.proposition.attribute_component import AttributeComponent, RangeValueComponent, is_same_origin
from cnl2asp.proposition.component import Component
from cnl2asp.proposition.problem import Problem
from cnl2asp.proposition.proposition import Proposition, NewKnowledgeComponent, ConditionComponent, RequisiteComponent, \
    PreferenceProposition, CardinalityComponent, PREFERENCE_PROPOSITION_TYPE
from cnl2asp.proposition.aggregate_component import AggregateComponent
from cnl2asp.proposition.operation_component import OperationComponent, Operators, is_arithmetic_operator
from cnl2asp.proposition.relation_component import RelationComponent
from cnl2asp.proposition.attribute_component import ValueComponent
from cnl2asp.proposition.signaturemanager import SignatureManager
from cnl2asp.utility.utility import Utility


class EntityToAtom:
    def __init__(self, entity: EntityComponent, atom: ASPAtom):
        self.entity = entity
        self.atom = atom


class ForbiddenLink:
    def __init__(self, entity_1: EntityComponent, entity_2: EntityComponent, attribute_1: AttributeComponent,
                 attribute_2: AttributeComponent):
        self.entity_1 = entity_1
        self.entity_2 = entity_2
        self.attribute_1 = attribute_1
        self.attribute_2 = attribute_2

    def contains(self, atom_1, atom_2, attribute):
        if atom_1 == self.atom_1 or atom_1 == self.atom_2:
            if atom_2 == self.atom_1 or atom_2 == self.atom_2:
                if attribute == self.attribute_1 or self.attribute_2:
                    return True
        return False


class ASPConverter(Converter[ASPProgram,
                             ASPRule, ASPWeakConstraint,
                             ASPRuleHead, (int, int),
                             ASPConjunction, ASPConjunction,
                             ASPAtom, ASPAggregate,
                             ASPOperation, ASPAttribute,
                             None, ASPValue, None]):
    def __init__(self):
        self._program: ASPProgram = ASPProgram()
        self._atoms_in_current_rule: list[EntityToAtom] = []  # variable used to track the conversion entity -> atom
        self._created_fields: list[str] = []
        self._aggregates: list[ASPAggregate] = []
        self._operations: list[ASPOperation] = []
        self._forbidden_links: list[ForbiddenLink] = []
        self._converted_complex_entities: list[str] = [] # name of complex entities already converted, used to track if their values have been already converted.

    def get_trailing_number(self, s: str):
        m = re.search(r'\d+$', s)
        return int(m.group()) if m else None

    def _get_initialized_attributes(self, proposition: Proposition):
        for entity in proposition.get_entities():
            for attribute in entity.get_keys_and_attributes():
                if attribute.value != Utility.NULL_VALUE:
                    self._created_fields.append(attribute.value)

    def create_new_field_value(self, name: str) -> ASPValue:
        result = re.sub(r'[AEIOU]', '', name, flags=re.IGNORECASE).upper()
        if result in self._created_fields:
            trailing_number = self.get_trailing_number(result)
            if trailing_number:
                new_value = int(trailing_number) + 1
                result = result.replace(str(trailing_number), str(new_value))
            else:
                result += '1'
            result = self.create_new_field_value(result)
        self._created_fields.append(result)
        return result

    def convert_problem(self, problem: Problem) -> ASPProgram:
        for constant in problem.get_constants():
            constant.convert(self)
        for proposition in problem.get_propositions():
            self._program.add_rule(proposition.convert(self))
            self.clear_support_variables()
        return self._program

    def clear_support_variables(self):
        self._atoms_in_current_rule = []
        self._created_fields = []
        self._forbidden_links = []
        self._aggregates = []
        self._operations = []

    def convert_proposition(self, proposition: Proposition) -> ASPRule:
        # Create a new signature for each new entity
        self._get_initialized_attributes(proposition)
        head = []
        cardinality = None
        body = None
        if proposition.new_knowledge:
            for new_knowledge in proposition.new_knowledge:
                head.append(new_knowledge.convert(self))
                self._forbidden_links += self.forbidden_links(new_knowledge, proposition.requisite)
        if proposition.cardinality:
            cardinality = proposition.cardinality.convert(self)
        if proposition.requisite:
            body: ASPConjunction = proposition.requisite.convert(self)
        if proposition.relations:
            for relation in proposition.relations:
                relation.convert(self)
        self.__move_operations(body)
        return ASPRule(body, head, cardinality)

    def __move_operations(self, body):
        for operation in self._operations:
            for operand in operation.operands:
                for aggregate in self._aggregates:
                    if operand in aggregate.get_discriminant_attributes_value():
                        aggregate.body.add_element(operation)
                        body.remove_element(operation)

    def convert_preference_proposition(self, preference: PreferenceProposition) -> ASPWeakConstraint:
        rule = self.convert_proposition(preference)
        discriminant = [attribute.convert(self) for attribute in preference.discriminant if
                        CNLTransformer.is_variable(attribute.value)]
        weight = preference.weight
        if preference.type == PREFERENCE_PROPOSITION_TYPE.MAXIMIZATION:
            weight = '-' + preference.weight.upper()
        weak_constraint = ASPWeakConstraint(rule.body, weight,
                                            preference.level.value, discriminant)
        return weak_constraint

    def convert_new_knowledge(self, head: NewKnowledgeComponent) -> ASPRuleHead:
        new_knowledge = head.new_entity.convert(self)
        condition = head.condition.convert(self) if head.condition.components else None
        return ASPRuleHead(new_knowledge, condition)

    def convert_cardinality(self, cardinality: CardinalityComponent) -> (int, int):
        return cardinality.lower_bound, cardinality.upper_bound

    def convert_condition(self, condition: ConditionComponent) -> ASPConjunction:
        return self.__create_conjunction(condition.components)

    def convert_requisite(self, requisite: RequisiteComponent) -> ASPConjunction:
        return self.__create_conjunction(requisite.components)

    def __create_conjunction(self, components: list[Component]) -> ASPConjunction:
        asp_conjunction = ASPConjunction([])
        for component in components:
            asp_conjunction.add_element(component.convert(self))
        return asp_conjunction

    def convert_entity(self, entity: EntityComponent) -> ASPAtom:
        atom = ASPAtom(entity.name, [attribute.convert(self) for attribute in entity.keys + entity.attributes],
                       entity.negated)
        self._atoms_in_current_rule.append(EntityToAtom(entity, atom))
        return atom

    def convert_temporal_entity(self, temporal_entity: TemporalEntityComponent):
        if temporal_entity.name not in self._converted_complex_entities:
            for value, idx in temporal_entity.values.items():
                self._program.add_rule(ASPRule(head=[ASPRuleHead(ASPAtom(temporal_entity.name,
                                                                       [ASPAttribute(temporal_entity.name, ASPValue(idx)),
                                                                        ASPAttribute('value', ASPValue(f'\"{value}\"'))]))]))
            self._converted_complex_entities.append(temporal_entity.name)
        return self.convert_entity(temporal_entity)

    def __has_single_key(self, entity: EntityComponent) -> bool:
        entity_keys = entity.get_keys()
        return len(entity_keys) == 1 and \
               entity.get_attributes_by_name_and_origin(entity_keys[0].name, entity_keys[0].origin)[0].value == Utility.ASP_NULL_VALUE

    def _match_discriminant_attributes_with_body(self, discriminant: list, body: ASPConjunction):
        unmatched_discriminant_attributes = []
        # create a variable to match discriminant attribute with the atoms attributes with the same name
        for attribute in discriminant:
            discriminant_value = attribute.value
            attributes_to_be_equal_discriminant_value = [attribute]
            attribute_matched = False
            for atom in body.get_atom_list():
                atom_matched_attributes = atom.get_attributes_list(attribute.name, attribute.origin)
                if len(atom_matched_attributes) > 1:
                    # TODO give the aggregate in the warning
                    print(f"Warning: multiple attribute with same name for atom {atom}, "
                          f"the first has been taken for aggregate.")
                if atom_matched_attributes:
                    attribute_matched = True
                    atom_matched_attribute = atom_matched_attributes[0]
                    if atom_matched_attribute.value != Utility.ASP_NULL_VALUE:
                        if discriminant_value != Utility.ASP_NULL_VALUE and discriminant_value != atom_matched_attribute.value:
                            continue
                        discriminant_value = atom_matched_attribute.value
                    attributes_to_be_equal_discriminant_value.append(atom_matched_attribute)
            if not attribute_matched:
                unmatched_discriminant_attributes.append(attribute)
                try:
                    discriminant += [attribute.convert(self) for attribute in
                                     SignatureManager.get_signature(attribute.name).get_keys()]
                except EntityNotFound:
                    raise Exception(f"Impossible to use attribute \"{attribute.origin} {attribute.name}\" in aggregate.")
            discriminant = [attribute for attribute in discriminant if
                            attribute not in unmatched_discriminant_attributes]
            if discriminant_value == Utility.ASP_NULL_VALUE:
                discriminant_value = ASPValue(self.create_new_field_value(attribute.name))
            for attribute_to_set in attributes_to_be_equal_discriminant_value:
                attribute_to_set.value = discriminant_value
        return discriminant

    def _match_discriminant_atom_with_body(self, discriminant: list[ASPAtom], body: ASPConjunction):
        for discriminant_elem in discriminant:
            for body_elem in body.get_atom_list():
                if discriminant_elem == body_elem:
                    for attribute in discriminant_elem.attributes:
                        self._link_atom_to_attribute(body_elem, attribute, discriminant_elem, [])

    def convert_aggregate(self, aggregate: AggregateComponent) -> ASPAggregate:
        # discriminant can be an atom or an attribute
        discriminant = [discr.convert(self) for discr in aggregate.discriminant]
        body = ASPConjunction([component.convert(self) for component in aggregate.body])
        if [x for x in discriminant if isinstance(x, ASPAttribute)]:
            discriminant = self._match_discriminant_attributes_with_body(discriminant, body)
        else:
            self._match_discriminant_atom_with_body(discriminant, body)
        aggregate = ASPAggregate(aggregate.operation, discriminant, body)
        self._aggregates.append(aggregate)
        return aggregate

    def _is_list_of_aggregates(self, operands) -> bool:
        for operand in operands:
            if not isinstance(operand, ASPAggregate):
                return False
        return True

    def _convert_operation_of_list_of_aggregate(self, operation, operands):
        operations: list[ASPOperation] = []
        fields: list[ASPValue] = []
        for operand in operands:
            new_field = ASPValue(Utility.create_unique_identifier().upper())
            operations.append(ASPOperation(Operators.EQUALITY, operand, new_field))
            fields.append(new_field)
        for i, field_1 in enumerate(fields):
            for j, field_2 in enumerate(fields[i + 1:]):
                operations.append(ASPOperation(operation.operator, field_1, field_2))
        for operation in operations:
            self._operations.append(operation)
        return operations

    def _convert_between_operation_without_aggregate(self, operation, operands):
        operation1 = ASPOperation(operation.operator, operands[0], operands[1])
        operation2 = ASPOperation(operation.operator, operands[1], operands[2])
        self._operations.append(operation1)
        self._operations.append(operation2)
        return ASPConjunction([operation1, operation2])

    def convert_operation(self, operation: OperationComponent) -> ASPOperation | [ASPOperation]:
        operands = []
        is_operation_on_angle = False
        for operand in operation.operands:
            if operand.is_angle():
                is_operation_on_angle = True
            operands.append(operand.convert(self))
        if is_operation_on_angle:
            return ASPAngleOperation(operation.operator, *operands)
        if self._is_list_of_aggregates(operands):
            return self._convert_operation_of_list_of_aggregate(operation, operands)
        if not is_arithmetic_operator(operation.operator) and len(operands) == 3 \
                and not isinstance(operands[1], ASPAggregate):
            return self._convert_between_operation_without_aggregate(operation, operands)
        operation = ASPOperation(operation.operator, *operands)
        self._operations.append(operation)
        return operation

    def convert_attribute(self, attribute: AttributeComponent) -> ASPAttribute:
        return ASPAttribute(attribute.name, attribute.value.convert(self), attribute.origin,
                            [operation.convert(self) for operation in attribute.operations])

    def convert_constant(self, constant: ConstantComponent) -> None:
        if constant.value and constant.value.isalpha():
            value = f'"{constant.value}"'
        else:
            value = constant.value.convert(self)
        self._program.add_constant((constant.name, value))

    def convert_value(self, value: ValueComponent) -> ASPValue:
        if not value:
            return ASPValue(value)
        if not self._program.is_constant(value) and not value == Utility.NULL_VALUE and not value.isnumeric() and not value.isupper():
            return ASPValue(f'"{value}"')
        return ASPValue(value)

    def convert_range_value(self, value: RangeValueComponent) -> ASPValue:
        return RangeASPValue(value)

    def forbidden_links(self, new_knowledge: NewKnowledgeComponent, requisite: RequisiteComponent) -> list[
        ForbiddenLink]:
        new_knowledge_links: list[AttributeComponent] = []
        for new_entity in new_knowledge.new_entity.get_entities():
            for condition in new_knowledge.condition.get_entities():
                for condition_key in condition.get_keys():
                    try:
                        attributes = new_entity.get_attributes_by_name(condition_key.name)
                        for attribute in attributes:
                            if is_same_origin(attribute.origin, condition_key.origin):
                                new_knowledge_links.append(attribute)
                    except AttributeNotFound:
                        pass
        forbidden_links: list[ForbiddenLink] = []
        for attribute in new_knowledge_links:
            for requisite_entity in requisite.get_entities():
                try:
                    requisite_entity_attributes = requisite_entity.get_attributes_by_name(attribute.name)
                    for requisite_entity_attribute in requisite_entity_attributes:
                        if is_same_origin(attribute.origin, requisite_entity_attribute.origin):
                            forbidden_links.append(
                                ForbiddenLink(new_knowledge.new_entity, requisite_entity,
                                              attribute.convert(self), requisite_entity_attribute.convert(self)))
                except AttributeNotFound:
                    pass
        return forbidden_links

    def convert_relation(self, relation: RelationComponent, new_knowledge: NewKnowledgeComponent = None) -> None:
        atom_1 = None
        atom_2 = None
        for pair in self._atoms_in_current_rule:
            # look for the exactly same entity
            if pair.entity is relation.entity_1:
                atom_1 = pair.atom
            if pair.entity is relation.entity_2:
                atom_2 = pair.atom
        # if entity not found, search for a copy
        if not atom_1:
            for pair in self._atoms_in_current_rule:
                if pair.entity == relation.entity_1:
                    atom_1 = pair.atom
        if not atom_2:
            for pair in self._atoms_in_current_rule:
                if pair.entity == relation.entity_2:
                    atom_2 = pair.atom
        if not atom_1 or not atom_2:
            raise Exception(f'Relation between {relation.entity_1.name} and {relation.entity_2.name} not found.')
        forbidden_links = self.get_forbidden_link(relation.entity_1, relation.entity_2)
        self._link_two_atoms(relation, atom_1, atom_2, forbidden_links)

    def get_forbidden_link(self, entity_1, entity_2) -> list[ASPAttribute]:
        forbidden_attributes = []
        for forbidden_link in self._forbidden_links:
            if (entity_1 == forbidden_link.entity_1 or entity_1 == forbidden_link.entity_2) and \
                    (entity_2 == forbidden_link.entity_1 or entity_2 == forbidden_link.entity_2):
                forbidden_attributes += [forbidden_link.attribute_1, forbidden_link.attribute_2]
        return forbidden_attributes

    def _link_two_atoms(self, relation: RelationComponent, atom_1: ASPAtom, atom_2: ASPAtom,
                        forbidden_links: list[ASPAttribute] = None):
        if forbidden_links is None:
            forbidden_links = []
        linked_attributes: list[ASPAttribute] = forbidden_links  # list of already linked attributes
        for key in relation.entity_1.get_keys():
            atom_1_keys = atom_1.get_attributes_list_by_name_and_origin(key.name, key.origin)
            for atom_1_key in atom_1_keys:
                self._link_atom_to_attribute(atom_2, atom_1_key, atom_1, linked_attributes)

        for key in relation.entity_2.get_keys():
            atom_2_keys = atom_2.get_attributes_list_by_name_and_origin(key.name, key.origin)
            for atom_2_key in atom_2_keys:
                if atom_2_key in linked_attributes:
                    continue
                self._link_atom_to_attribute(atom_1, atom_2_key, atom_2, linked_attributes)

    def _link_atom_to_attribute(self, atom_1: ASPAtom,
                                attribute: ASPAttribute, atom_2: ASPAtom, linked_attributes: list[ASPAttribute]):
        atom_1_attributes = atom_1.get_attributes_list(attribute.name)
        for atom_1_attribute in atom_1_attributes:
            if (atom_1_attribute.value != '_' and atom_2.has_attribute(atom_1_attribute)) or (attribute.value != '_' and atom_1.has_attribute(attribute)):
                continue
            if atom_1_attribute in linked_attributes:
                continue
            if is_same_origin(atom_1_attribute.origin, attribute.origin):
                # if both attributes have a value, skip it. The next attribute should be the correct one
                new_var = ASPValue(self.create_new_field_value('_'.join([atom_1.name, attribute.name])))
                if attribute.value != Utility.ASP_NULL_VALUE and atom_1_attribute.value != Utility.ASP_NULL_VALUE:
                    continue
                if attribute.value != Utility.ASP_NULL_VALUE:
                    new_var = attribute.value
                if atom_1_attribute.value != Utility.ASP_NULL_VALUE:
                    new_var = atom_1_attribute.value
                atom_1.set_attributes_value([ASPAttribute(attribute.name, new_var, attribute.origin)])
                attribute.value = new_var
                # add the two linked attribute keys to the already linked attributes list
                linked_attributes.append(attribute)
                linked_attributes.append(atom_1_attribute)
                # we found a match we can skip. We do not want to link also the next value, this is
                # the case in which the entity has more attributes matching
                break
