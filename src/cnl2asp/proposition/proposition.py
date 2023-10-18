from enum import Enum

from cnl2asp.exception.cnl2asp_exceptions import EntityNotFound, AttributeNotFound
from cnl2asp.converter.converter_interface import Converter, NewKnowledgeConverter, ConditionConverter, RequisiteConverter, \
    CardinalityConverter, PropositionConverter
from cnl2asp.utility.utility import Utility
from .attribute_component import AttributeComponent, ValueComponent, AttributeOrigin, is_same_origin
from .component import Component
from .entity_component import EntityComponent
from .relation_component import RelationComponent


class AggregateOfComponents(Component):
    def __init__(self, components: list[Component]):
        self.components = components if components else []

    def add_components(self, components: list[Component]):
        self.components += components

    def convert(self, converter: Converter):
        pass

    def copy(self):
        return [component.copy() for component in self.components]

    def get_entities(self) -> list[EntityComponent]:
        entities = []
        for entity in self.components:
            entities += entity.get_entities()
        return entities


class ConditionComponent(AggregateOfComponents):
    def __init__(self, condition: list[Component] = []):
        super().__init__(condition)

    def convert(self, converter: Converter) -> ConditionConverter:
        return converter.convert_condition(self)

    def copy(self):
        return ConditionComponent(super().copy())


class NewKnowledgeComponent(Component):
    def __init__(self, new_knowledge: EntityComponent, condition: ConditionComponent = None):
        self.new_entity = new_knowledge
        self.condition = condition if condition else ConditionComponent([])

    def convert(self, converter: Converter) -> NewKnowledgeConverter:
        return converter.convert_new_knowledge(self)

    def copy(self):
        return NewKnowledgeComponent(self.new_entity.copy(), self.condition.copy())

    def get_entities(self) -> list[EntityComponent]:
        entities = [self.new_entity]
        for entity in self.condition.get_entities():
            entities.append(entity)
        return entities


class RequisiteComponent(AggregateOfComponents):
    def __init__(self, requisite: list[Component]):
        super().__init__(requisite)

    def convert(self, converter: Converter) -> RequisiteConverter:
        return converter.convert_requisite(self)

    def copy(self):
        return RequisiteComponent(super().copy())


class CardinalityComponent(Component):
    def __init__(self, lower_bound: int | None, upper_bound: int | None):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def convert(self, converter: Converter) -> CardinalityConverter:
        return converter.convert_cardinality(self)

    def copy(self):
        return CardinalityComponent(self.lower_bound, self.upper_bound)


class Proposition(Component):
    # Data structure for representing the sentences
    def __init__(self, new_knowledge: list[NewKnowledgeComponent] = None,
                 cardinality: CardinalityComponent = None, requisite: RequisiteComponent = None,
                 relations: list[RelationComponent] = None):
        self.new_knowledge = new_knowledge if new_knowledge else []
        self.cardinality = cardinality if cardinality else None
        self.requisite = requisite if requisite else RequisiteComponent([])
        self.relations = relations if relations else []

    def is_empty(self) -> bool:
        return len(self.new_knowledge) == 0 and len(self.requisite.components) == 0 and len(self.relations) == 0

    def add_requisite(self, requisite: list[Component]):
        self.requisite.add_components(requisite)

    def create_new_signature(self, new_entity: EntityComponent) -> EntityComponent:
        signature: EntityComponent = new_entity.copy()
        # add all the keys of all the entities related with the new entity
        for relation in self.relations:
            to_be_related_with = None
            if relation.entity_1 == new_entity:
                to_be_related_with = relation.entity_2
            elif relation.entity_2 == new_entity:
                to_be_related_with = relation.entity_1
            if to_be_related_with:
                for key in to_be_related_with.get_keys():
                    try:
                        signature.get_attributes_by_name_and_origin(key.name, key.origin)
                    except AttributeNotFound:
                        try:
                            attribute = signature.get_attributes_by_name(key.name)[0]
                            if attribute.value == key.value and attribute.origin.name == signature.name and not attribute.origin.origin:
                                new_entity.get_attributes_by_name(key.name)[0].origin = key.origin
                                attribute.origin = key.origin
                            else:
                                raise AttributeNotFound('')
                        except AttributeNotFound:
                            signature.attributes.append(AttributeComponent(key.name, ValueComponent(Utility.NULL_VALUE),
                                                                           AttributeOrigin(to_be_related_with.name,
                                                                                           key.origin)))
        signature.attributes.sort(key=lambda x: x.name)
        if not signature.attributes:
            signature.attributes.append(
                AttributeComponent(Utility.DEFAULT_ATTRIBUTE, ValueComponent(Utility.NULL_VALUE),
                                   AttributeOrigin(signature.name)))
        for attribute in signature.get_keys_and_attributes():
            attribute.value = ValueComponent(Utility.NULL_VALUE)
        return signature

    def convert(self, converter: Converter) -> PropositionConverter:
        return converter.convert_proposition(self)

    def get_entity_by_name(self, name: str):
        for entity in self.get_entities():
            if entity.name == name:
                return entity
        raise EntityNotFound(f'Entity {name} not found.')

    def get_entities(self) -> list[EntityComponent]:
        entities: list[EntityComponent] = []
        for component in self.requisite.components:
            entities += component.get_entities()
        for new_knowledge in self.new_knowledge:
            entities += new_knowledge.get_entities()
        for relation in self.relations:
            entities += relation.get_entities()
        return entities

    def copy(self):
        new_knowledge = [new_knowledge.copy() for new_knowledge in self.new_knowledge]
        cardinality = self.cardinality.copy() if self.cardinality else None
        requisite = self.requisite.copy()
        relations = [relation.copy() for relation in self.relations]
        return Proposition(new_knowledge, cardinality, requisite, relations)


class PREFERENCE_PROPOSITION_TYPE(Enum):
    MINIMIZATION = 0
    MAXIMIZATION = 1


class PREFERENCE_PRIORITY_LEVEL(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class PreferenceProposition(Proposition):
    def __init__(self, requisite: RequisiteComponent = None, relations: list[RelationComponent] = None,
                 weight: str = '1', level: PREFERENCE_PRIORITY_LEVEL = PREFERENCE_PRIORITY_LEVEL.LOW,
                 discriminant: list[AttributeComponent] = []):
        super().__init__(None, None, requisite, relations)
        self.weight = weight
        self.level = level
        self.discriminant = discriminant
        self.type = PREFERENCE_PROPOSITION_TYPE.MINIMIZATION

    def convert(self, converter: Converter) -> PropositionConverter:
        return converter.convert_preference_proposition(self)

    def add_discriminant(self, discriminant: AttributeComponent):
        if not discriminant in self.discriminant:
            self.discriminant.append(discriminant)

    def copy(self):
        proposition = super().copy()
        preference_proposition = PreferenceProposition(proposition.requisite, proposition.relations, self.weight,
                                                       self.level,
                                                       [discriminant.copy() for discriminant in self.discriminant])
        return preference_proposition