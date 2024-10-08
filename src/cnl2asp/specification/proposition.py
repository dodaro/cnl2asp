from enum import Enum

from cnl2asp.exception.cnl2asp_exceptions import EntityNotFound, AttributeNotFound
from cnl2asp.converter.converter_interface import Converter, NewKnowledgeConverter, ConditionConverter, \
    RequisiteConverter, \
    CardinalityConverter, PropositionConverter
from cnl2asp.utility.utility import Utility
from .attribute_component import AttributeComponent, ValueComponent, AttributeOrigin
from .component import Component
from .entity_component import EntityComponent
from .relation_component import RelationComponent


class PROPOSITION_TYPE(Enum):
    CONSTRAINT = 0
    REQUIREMENT = 1
    PREFERENCE = 2


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

    def get_entities_to_link_with_new_knowledge(self) -> list[EntityComponent]:
        entities = []
        for entity in self.components:
            entities += entity.get_entities_to_link_with_new_knowledge()
        return entities


class ConditionComponent(AggregateOfComponents):
    def __init__(self, condition: list[Component] = []):
        super().__init__(condition)

    def convert(self, converter: Converter) -> ConditionConverter:
        return converter.convert_condition(self)

    def copy(self):
        return ConditionComponent(super().copy())


class NewKnowledgeComponent(Component):
    def __init__(self, new_knowledge: EntityComponent, condition: ConditionComponent = None,
                 subject=None, auxiliary_verb=None, objects=None):
        self.new_entity = new_knowledge
        self.condition = condition if condition else ConditionComponent([])
        self.subject = subject
        self.auxiliary_verb = auxiliary_verb
        self.objects = [x.copy() for x in objects] if objects else None

    def convert(self, converter: Converter) -> NewKnowledgeConverter:
        return converter.convert_new_knowledge(self)

    def copy(self):
        return NewKnowledgeComponent(self.new_entity.copy(), self.condition.copy(), self.subject, self.auxiliary_verb, self.objects)

    def get_entities(self) -> list[EntityComponent]:
        entities = self.new_entity.get_entities()
        for entity in self.condition.get_entities():
            entities.append(entity)
        return entities

    def get_entities_to_link_with_new_knowledge(self) -> list[EntityComponent]:
        entities = [self.new_entity]
        for entity in self.condition.get_entities_to_link_with_new_knowledge():
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
                 relations: list[RelationComponent] = None, defined_attributes: list[AttributeComponent] = None):
        if defined_attributes is None:
            defined_attributes = []
        self.new_knowledge = new_knowledge if new_knowledge else []
        self.cardinality = cardinality if cardinality else None
        self.requisite = requisite if requisite else RequisiteComponent([])
        self.relations = relations if relations else []
        self.defined_attributes = defined_attributes

    def is_empty(self) -> bool:
        return len(self.new_knowledge) == 0 and len(self.requisite.components) == 0 and len(self.relations) == 0

    def add_requisite(self, requisite: list[Component]):
        self.requisite.add_components(requisite)

    def create_new_signature(self, new_entity: EntityComponent) -> EntityComponent:
        signature: EntityComponent = new_entity.copy()
        linked_entities: list[str] = []  # list of labels already linked
        # add all the keys of all the entities related with the new entity
        for relation in self.relations:
            to_be_related_with = None
            if relation.relation_component_1 == new_entity:
                to_be_related_with = relation.relation_component_2
            elif relation.relation_component_2 == new_entity:
                to_be_related_with = relation.relation_component_1
            if to_be_related_with:

                if len(to_be_related_with.get_keys_and_attributes()) == 1 and \
                        to_be_related_with.label not in linked_entities:
                    for key in to_be_related_with.get_keys():
                        if not new_entity.has_attribute_value(key.value):
                            signature.attributes.append(AttributeComponent(key.get_name(), ValueComponent(Utility.NULL_VALUE),
                                                                           AttributeOrigin(to_be_related_with.get_name(),
                                                                                           key.origin)))
                if to_be_related_with.label not in linked_entities:
                    linked_entities.append(to_be_related_with.label)
                for key in to_be_related_with.get_keys():
                    if key.value != Utility.NULL_VALUE and signature.has_attribute_value(key.value):
                        try:
                            new_entity.get_attributes_by_name_and_origin(key.get_name(), AttributeOrigin(signature.get_name()))[
                                0].origin = key.origin
                            signature.get_attributes_by_name_and_origin(key.get_name(), AttributeOrigin(signature.get_name()))[
                                0].origin = key.origin
                        except:
                            pass
                    try:
                        signature.get_attributes_by_name_and_origin(key.get_name(), key.origin)
                    except AttributeNotFound:
                        try:
                            attribute = signature.get_attributes_by_name(key.get_name())[0]
                            if attribute.value == key.value and attribute.origin.name == signature.get_name() \
                                    and not attribute.origin.origin:
                                new_entity.get_attributes_by_name(key.get_name())[0].origin = key.origin
                                attribute.origin = key.origin
                            else:
                                raise AttributeNotFound('')
                        except AttributeNotFound:
                            signature.attributes.append(AttributeComponent(key.get_name(), ValueComponent(Utility.NULL_VALUE),
                                                                           AttributeOrigin(to_be_related_with.get_name(),
                                                                                           key.origin)))
        if not signature.attributes:
            signature.attributes.append(
                AttributeComponent(Utility.DEFAULT_ATTRIBUTE, ValueComponent(Utility.NULL_VALUE),
                                   AttributeOrigin(signature.get_name())))
        for attribute in signature.get_keys_and_attributes():
            attribute.value = ValueComponent(Utility.NULL_VALUE)
        return signature

    def convert(self, converter: Converter) -> PropositionConverter:
        return converter.convert_proposition(self)

    def get_entity_by_name(self, name: str):
        for entity in self.get_entities():
            if entity.get_name() == name:
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

    def get_entities_to_link_with_new_knowledge(self) -> list[EntityComponent]:
        entities: list[EntityComponent] = []
        for component in self.requisite.components:
            entities += component.get_entities_to_link_with_new_knowledge()
        for new_knowledge in self.new_knowledge:
            entities += new_knowledge.get_entities_to_link_with_new_knowledge()
        for relation in self.relations:
            entities += relation.get_entities_to_link_with_new_knowledge()
        return entities

    def copy(self):
            new_knowledge = [new_knowledge.copy() for new_knowledge in self.new_knowledge]
            cardinality = self.cardinality.copy() if self.cardinality else None
            requisite = self.requisite.copy()
            relations = [relation.copy() for relation in self.relations]
            defined_attributes = [attribute.copy() for attribute in self.defined_attributes]
            return Proposition(new_knowledge, cardinality, requisite, relations, defined_attributes)


class PREFERENCE_PROPOSITION_TYPE(Enum):
    MINIMIZATION = 0
    MAXIMIZATION = 1


class PreferenceProposition(Proposition):
    def __init__(self, requisite: RequisiteComponent = None, relations: list[RelationComponent] = None,
                 weight: str = '1', level: int = 1,
                 discriminant: list[AttributeComponent] = None):
        super().__init__(None, None, requisite, relations)
        if discriminant is None:
            discriminant = []
        self.weight = weight
        self.level = level
        self.discriminant = discriminant
        self.type = PREFERENCE_PROPOSITION_TYPE.MINIMIZATION

    def convert(self, converter: Converter) -> PropositionConverter:
        return converter.convert_preference_proposition(self)

    def add_discriminant(self, discriminant: AttributeComponent):
        if discriminant not in self.discriminant:
            self.discriminant.append(discriminant)

    def copy(self):
        proposition = super().copy()
        preference_proposition = PreferenceProposition(proposition.requisite, proposition.relations, self.weight,
                                                       self.level,
                                                       [discriminant.copy() for discriminant in self.discriminant])
        return preference_proposition
