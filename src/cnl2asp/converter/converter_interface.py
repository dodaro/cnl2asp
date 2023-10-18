from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, TYPE_CHECKING


if TYPE_CHECKING:
    from proposition.attribute_component import ValueComponent, RangeValueComponent
    from proposition.constant_component import ConstantComponent
    from proposition.problem import Problem
    from proposition.proposition import Proposition, PreferenceProposition, CardinalityComponent
    from proposition.aggregate_component import AggregateComponent
    from proposition.entity_component import EntityComponent
    from proposition.operation_component import OperationComponent
    from proposition.relation_component import RelationComponent
    from proposition.attribute_component import AttributeComponent

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

    def convert_value(self, value: ValueComponent) -> ValueConverter:
        """Convert value"""

    def convert_range_value(self, value: RangeValueComponent) -> ValueConverter:
        """Convert range value"""

    @abstractmethod
    def convert_relation(self, relation: RelationComponent) -> RelationConverter:
        """Convert relation"""
