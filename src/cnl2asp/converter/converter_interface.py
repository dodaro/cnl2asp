from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, TYPE_CHECKING

from cnl2asp.specification.component import Component

if TYPE_CHECKING:
    from cnl2asp.specification.entity_component import TemporalEntityComponent
    from cnl2asp.specification.specification import SpecificationComponent
    from cnl2asp.specification.attribute_component import ValueComponent, RangeValueComponent
    from cnl2asp.specification.constant_component import ConstantComponent
    from cnl2asp.specification.problem import Problem
    from cnl2asp.specification.proposition import Proposition, PreferenceProposition, CardinalityComponent
    from cnl2asp.specification.aggregate_component import AggregateComponent
    from cnl2asp.specification.entity_component import EntityComponent
    from cnl2asp.specification.operation_component import OperationComponent
    from cnl2asp.specification.relation_component import RelationComponent
    from cnl2asp.specification.attribute_component import AttributeComponent

ProblemConverter = TypeVar('ProblemConverter')
DomainDefinitionConverter = TypeVar('DomainDefinitionConverter')
PropositionConverter = TypeVar('PropositionConverter')
PreferencePropositionConverter = TypeVar('PreferencePropositionConverter')
NewKnowledgeConverter = TypeVar('NewKnowledgeConverter')
CardinalityConverter = TypeVar('CardinalityConverter')
ConditionConverter = TypeVar('ConditionConverter')
RequisiteConverter = TypeVar('RequisiteConverter')
EntityConverter = TypeVar('EntityConverter')
AggregateConverter = TypeVar('AggregateConverter')
OperationConverter = TypeVar('OperationConverter')
AttributeConverter = TypeVar('AttributeConverter')
ConstantConverter = TypeVar('ConstantConverter')
ValueConverter = TypeVar('ValueConverter')
RelationConverter = TypeVar('RelationConverter')


class Converter(ABC, Generic[ProblemConverter,
                             PropositionConverter, PreferencePropositionConverter,
                             NewKnowledgeConverter, CardinalityConverter,
                             ConditionConverter, RequisiteConverter,
                             EntityConverter, AggregateConverter,
                             OperationConverter, AttributeConverter,
                             ConstantConverter, ValueConverter,
                             RelationConverter]):
    @abstractmethod
    def convert_problem(self, problem: Problem) -> ProblemConverter:
        """Convert problem"""

    @abstractmethod
    def convert_proposition(self, proposition: Proposition) -> PropositionConverter:
        """Convert proposition"""

    @abstractmethod
    def convert_preference_proposition(self, preference: PreferenceProposition) -> PreferencePropositionConverter:
        """Converter preference proposition"""

    @abstractmethod
    def convert_new_knowledge(self, new_knowledge: NewKnowledgeConverter) -> NewKnowledgeConverter:
        """Convert new knowledge"""

    @abstractmethod
    def convert_cardinality(self, cardinality: CardinalityComponent) -> CardinalityConverter:
        """Convert cardinality"""

    @abstractmethod
    def convert_condition(self, condition: ConditionConverter) -> ConditionConverter:
        """Convert condition"""

    @abstractmethod
    def convert_requisite(self, requisite: RequisiteConverter) -> RequisiteConverter:
        """Convert requisite"""

    @abstractmethod
    def convert_entity(self, entity: EntityComponent) -> EntityConverter:
        """Convert entity"""

    @abstractmethod
    def convert_temporal_entity(self, temporal_entity: TemporalEntityComponent):
        "Convert temporal entity"


    @abstractmethod
    def convert_aggregate(self, aggregate: AggregateComponent) -> AggregateConverter:
        """Convert aggregate"""

    @abstractmethod
    def convert_operation(self, operation: OperationComponent) -> OperationConverter:
        """Convert operation"""

    @abstractmethod
    def convert_attribute(self, attribute: AttributeComponent) -> AttributeConverter:
        """Convert attribute"""

    @abstractmethod
    def convert_constant(self, constant: ConstantComponent) -> ConstantConverter:
        """Convert constant"""

    @abstractmethod
    def convert_value(self, value: ValueComponent) -> ValueConverter:
        """Convert value"""

    @abstractmethod
    def convert_range_value(self, value: RangeValueComponent) -> ValueConverter:
        """Convert range value"""

    @abstractmethod
    def convert_relation(self, relation_component_1: Component, relation_component_2: Component) -> RelationConverter:
        """Convert relation"""

    @abstractmethod
    def convert_specification(self, specification: SpecificationComponent):
        """Convert specification"""

    @abstractmethod
    def convert_temporal_entity(self, temporal_entity: TemporalEntityComponent):
        """Convert temporal entity"""

