from __future__ import annotations

import collections

from cnl2asp.converter.converter_interface import Converter, ProblemConverter
from cnl2asp.specification.constant_component import ConstantComponent
from cnl2asp.specification.entity_component import EntityComponent, TemporalEntityComponent
from cnl2asp.specification.attribute_component import AttributeComponent, RangeValueComponent, is_same_origin
from cnl2asp.specification.problem import Problem
from cnl2asp.specification.proposition import Proposition, NewKnowledgeComponent, ConditionComponent, RequisiteComponent, \
    PreferenceProposition, CardinalityComponent, PREFERENCE_PROPOSITION_TYPE
from cnl2asp.specification.aggregate_component import AggregateComponent
from cnl2asp.specification.operation_component import OperationComponent, Operators
from cnl2asp.specification.relation_component import RelationComponent
from cnl2asp.specification.attribute_component import ValueComponent
from cnl2asp.specification.signaturemanager import SignatureManager
from cnl2asp.specification.specification import SpecificationComponent
from cnl2asp.utility.utility import Utility


class Cnl2jsonConverter(Converter):


    def __init__(self):
        self._json = dict()
        self._json_assignment = collections.defaultdict(set)
        self._json_constant = collections.defaultdict(set)
        self._delayed_operations = []
        self._problem_constants = []

    def convert_specification(self, specification: SpecificationComponent):
        self._json["assignments"] = []
        self._json["constants"] = []
        for constant in specification.get_constants():
            constant.convert(self)
        for problem in specification.get_problems():
            self.convert_problem(problem)
        return self._json

    def convert_problem(self, problem: Problem) -> ProblemConverter:
        for proposition in problem.get_propositions():
            proposition.convert(self)
            self._clear_support_variables()

    def _clear_support_variables(self):
        self._json_assignment = collections.defaultdict(set)
        self._json_constant = collections.defaultdict(set)
        self._delayed_operations = []

    def convert_proposition(self, proposition: Proposition):
        for component in proposition.new_knowledge:
            component.convert(self)
        for component in proposition.requisite.components:
            component.convert(self)
        for delayed_operation in self._delayed_operations:
            self._convert_delayed_operation(delayed_operation)
        for key, value in self._json_assignment.items():
            self._json_assignment.update({key: list(value)})
        for key, value in self._json_constant.items():
            self._json_constant.update({key: list(value)})
        self._json["assignments"].append(dict(self._json_assignment))
        self._json["constants"].append(dict(self._json_constant))

    def __find_attribute(self, attribute_value: ValueComponent):
        for assignment_key, assignment_values in self._json_assignment.items():
            for assignment_value in assignment_values:
                if assignment_value == attribute_value:
                    return assignment_key

    def __is_constant(self, value: ValueComponent):
        for constant in self._problem_constants:
            if constant.name == value:
                return True
        return False

    def _convert_delayed_operation(self, delayed_operation: list[ValueComponent]):
        constants = []
        attributes = []
        for attribute in delayed_operation:
            if self.__is_constant(attribute):
                constants.append(attribute)
            else:
                attributes.append(attribute)
        for attribute in attributes:
            entity = self.__find_attribute(attribute)
            for constant in constants:
                self._json_constant[entity].add(constant)

    def convert_preference_proposition(self, preference: PreferenceProposition):
        self.convert_proposition(preference)

    def convert_new_knowledge(self, head: NewKnowledgeComponent):
        head.new_entity.convert(self)
        for component in head.condition.components:
            component.convert(self)

    def convert_cardinality(self, cardinality: CardinalityComponent) -> (int, int):
        pass

    def convert_condition(self, condition: ConditionComponent):
        for component in condition.components:
            component.convert(self)

    def convert_requisite(self, requisite: RequisiteComponent):
        for component in requisite.components:
            component.convert(self)

    def _is_predicate(self, name: str):
        try:
            SignatureManager.clone_signature(name)
            return True
        except:
            return False


    def _get_predicate(self, entity_name: str, attribute: AttributeComponent):
        split_name = attribute.get_name().split('_')
        if len(split_name) > 1:
            for name in split_name:
                if self._is_predicate(name):
                    return SignatureManager.clone_signature(name)
        signature_name = attribute.get_name()
        if attribute.origin != entity_name:
            signature_name = attribute.origin.name
        if self._is_predicate(signature_name):
            return SignatureManager.clone_signature(signature_name)
        return None

    def convert_entity(self, entity: EntityComponent):
        self._json_assignment[entity.get_name()] = set()
        for attribute in entity.get_keys_and_attributes():
            if attribute.value != Utility.NULL_VALUE:
                predicate = self._get_predicate(entity.get_name(), attribute)
                if predicate:
                    self._json_assignment[predicate.get_name()].add(attribute.value)
                else:
                    self._json_assignment[entity.get_name()].add(attribute.value)

    def convert_temporal_entity(self, temporal_entity: TemporalEntityComponent):
        self.convert_entity(temporal_entity)

    def convert_aggregate(self, aggregate: AggregateComponent):
        for discriminant in aggregate.discriminant:
            discriminant.convert(self)
        for entity in aggregate.body:
            entity.convert(self)

    def _convert_between_operation_without_aggregate(self, operation, operands):
        for operand in operands:
            operand.convert(self)

    def convert_operation(self, operation: OperationComponent):
        delayed_operation = list()
        for operand in operation.operands:
            res = operand.convert(self)
            if res:
                delayed_operation.append(res)
        self._delayed_operations.append(delayed_operation)

    def convert_attribute(self, attribute: AttributeComponent):
        for operation in attribute.operations:
            self.convert_operation(operation)
        return attribute

    def convert_constant(self, constant: ConstantComponent):
        self._problem_constants.append(constant)
        return constant

    def convert_value(self, value: ValueComponent):
        return value

    def convert_range_value(self, value: RangeValueComponent):
        pass

    def convert_relation(self, relation: RelationComponent, new_knowledge: NewKnowledgeComponent = None) -> None:
        pass
