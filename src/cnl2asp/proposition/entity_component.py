from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TYPE_CHECKING

from cnl2asp.exception.cnl2asp_exceptions import EntityNotDefined, AttributeNotFound
from cnl2asp.converter.converter_interface import Converter, EntityConverter
from cnl2asp.proposition.attribute_component import AttributeComponent, ValueComponent, AttributeOrigin, is_same_origin
from cnl2asp.proposition.component import Component
from cnl2asp.utility.utility import Utility
from cnl2asp.proposition.relation_component import RelationComponent

if TYPE_CHECKING:
    from parser.proposition_builder import PropositionBuilder


class EntityType(Enum):
    GENERIC = 0
    TIME = 1
    DATE = 2
    STEP = 3
    ANGLE = 4


class EntityComponent(Component):
    def __init__(self, name: str, label: str, keys: list[AttributeComponent], attributes: list[AttributeComponent],
                 negated: bool = False, entity_type: EntityType = EntityType.GENERIC):
        self.name = name
        self.label = label
        self.keys = keys if keys else []
        self.attributes = attributes if attributes else []
        for attribute in self.attributes:
            if attribute.origin is None:
                attribute.origin = AttributeOrigin(self.name)
        self.negated = negated
        self.entity_type = entity_type

    def label_is_key_value(self):
        if self.label and len(self.get_keys()) == 1 and self.get_keys()[0].value == Utility.NULL_VALUE:
            return True
        return False

    def set_label_as_key_value(self):
        # we consider the label value as the value of the key in case the entity has only one key and
        # has no values
        self.set_attributes_value(
            [AttributeComponent(self.get_keys()[0].name,
                                ValueComponent(self.label), self.get_keys()[0].origin)])

    def set_name(self, name: str):
        self.name = name

    def convert(self, converter: Converter) -> EntityConverter:
        return converter.convert_entity(self)

    def negate(self):
        self.negated = not self.negated

    def get_keys(self) -> list[AttributeComponent]:
        return self.keys if self.keys else self.attributes

    def get_attributes(self) -> list[AttributeComponent]:
        return self.attributes

    def get_keys_and_attributes(self) -> list[AttributeComponent]:
        return self.keys + self.attributes

    def set_attributes_value(self, attributes: list[AttributeComponent], proposition: PropositionBuilder = None):
        for attribute in attributes:
            if isinstance(attribute, EntityComponent):
                if not proposition:
                    raise RuntimeError('Error in compilation phase.')
                proposition.add_relations([RelationComponent(self, attribute)])
            else:
                if attribute.origin:
                    entity_attributes = self.get_attributes_by_name_and_origin(attribute.name, attribute.origin)
                else:
                    entity_attributes = self.get_attributes_by_name(attribute.name)
                for entity_attribute in entity_attributes:
                    entity_attribute.value = attribute.value

    def set_attribute_value(self, attribute_name: str, value: ValueComponent, origin: AttributeOrigin = None):
        if not origin:
            origin = self.get_attributes_by_name(attribute_name)[0].origin
        self.set_attributes_value([AttributeComponent(attribute_name, value, origin)])

    def get_attributes_by_name_and_origin(self, name: str, origin: AttributeOrigin = None) -> list[AttributeComponent]:
        attributes = []
        origin = AttributeOrigin(self.name) if not origin else origin
        for attribute in self.get_keys_and_attributes():
            if attribute.name == name and is_same_origin(attribute.origin, origin):
                attributes.append(attribute)
        if attributes:
            return attributes
        raise AttributeNotFound(f'Entity \"{self.name}\" do not contain attribute \"{name}\".')

    def get_attributes_by_name(self, name: str) -> list[AttributeComponent]:
        attributes = []
        for attribute in self.get_keys_and_attributes():
            if attribute.name == name:
                attributes.append(attribute)
        if attributes:
            return attributes
        raise AttributeNotFound(f'Entity \"{self.name}\" do not contain attribute \"{name}\".')

    def copy(self) -> Any:
        keys = [key.copy() for key in self.keys]
        attributes = [attribute.copy() for attribute in self.attributes]
        return EntityComponent(self.name, self.label, keys,
                               attributes, self.negated, self.entity_type)

    def get_entities(self) -> list[EntityComponent]:
        return [self]

    def is_temporal_entity(self) -> bool:
        return False

    def __eq__(self, other):
        if not isinstance(other, EntityComponent):
            return False
        return self.name == other.name \
               and self.label == other.label \
               and self.keys == other.keys \
               and self.attributes == other.attributes \
               and self.negated == other.negated \
               and self.entity_type == other.entity_type


class SetOfTypedEntities:
    _TypedEntities = []

    def __init__(self):
        pass

    @staticmethod
    def add_entity(entity: EntityComponent):
        SetOfTypedEntities._TypedEntities.append(entity)

    def is_temporal_entity(name: str) -> bool:
        try:
            SetOfTypedEntities.get_entity(name)
            return True
        except:
            return False

    @staticmethod
    def get_entity(name: str) -> EntityComponent:
        for entity in SetOfTypedEntities._TypedEntities:
            if entity.name == name:
                return entity.copy()
        raise EntityNotDefined(f"Typed entity {name} not defined.")

    @staticmethod
    def get_entity_from_type(entity_type: str) -> EntityComponent:
        for entity in SetOfTypedEntities._TypedEntities:
            if entity.entity_type == entity_type:
                return entity.copy()
        raise EntityNotDefined(f"Typed entity with type {entity_type} not defined.")

    @staticmethod
    def get_entity_from_value(value: ValueComponent):
        """
        Parse the value and return the first entity that match the same type
        :param value: a date, time or number
        :return: the entity that match the type
        """
        entity_type = EntityType.STEP
        try:
            datetime.strptime(str(value), '%I:%M %p')
            entity_type = EntityType.TIME
        except:
            pass
        try:
            datetime.strptime(str(value), '%d/%m/%Y')
            entity_type = EntityType.DATE
        except:
            pass
        for entity in SetOfTypedEntities._TypedEntities:
            if entity.entity_type == entity_type:
                return entity
        raise Exception(f"No entity found with same type of {value}")


class TemporalEntityComponent(EntityComponent):
    def __init__(self, name: str, label: str,
                 lhs_range_value: ValueComponent,
                 rhs_range_value: ValueComponent, step: ValueComponent,
                 entity_type: EntityType, values: dict = None):
        super().__init__(name, label, [],
                         [AttributeComponent(name, ValueComponent('_'), AttributeOrigin(name))],
                         entity_type=entity_type)
        step = 1 if not step else step
        self.values: dict = self._compute_values(lhs_range_value, rhs_range_value, step) if not values else values

    def get_value(self, value: ValueComponent):
        try:
            in_time = datetime.strptime(str(value), "%I:%M %p")
            value = datetime.strftime(in_time, "%H:%M")
        except:
            pass
        return self.values[value]

    def _compute_values(self, lhs_value: ValueComponent, rhs_value: ValueComponent,
                        step: ValueComponent) -> dict:
        """
        Compute all the values in the range and assign a label starting from 0.
        :param lhs_value: left hand side value of the range
        :param rhs_value: right hand side value of the range
        :param step: step of increment from lhs to rhs
        :return: a dict with each value associated to a number
        """
        elements = dict()
        counter = 1
        try:
            if self.entity_type == EntityType.TIME:
                start = datetime.strptime(lhs_value, '%I:%M %p')
                end = datetime.strptime(rhs_value, '%I:%M %p')
                elements[start.strftime('%H:%M')] = 0
                start = start + timedelta(minutes=int(step))
                while start <= end:
                    if start > end:
                        start = end
                    elements[start.strftime('%H:%M')] = counter
                    counter += 1
                    start = start + timedelta(minutes=int(step))
            elif self.entity_type == EntityType.DATE:
                start = datetime.strptime(lhs_value, '%d/%m/%Y')
                end = datetime.strptime(rhs_value, '%d/%m/%Y')
                elements[start.strftime('%d/%m/%Y')] = 0
                start = start + timedelta(minutes=int(step))
                while start <= end:
                    if start > end:
                        start = end
                    elements[start.strftime('%d/%m/%Y')] = counter
                    counter += 1
                    start = start + timedelta(minutes=int(step))
            elif self.entity_type == EntityType.STEP:
                start = lhs_value
                end = rhs_value
                elements[0] = start
                for i in range(int(start) + 1, int(end) + 1):
                    elements[i] = counter
                    counter += 1
        except:
            raise Exception(f"Entity {self.name}, entity type do not match {lhs_value} and {rhs_value}")
        return elements

    def is_temporal_entity(self) -> bool:
        return True

    def get_temporal_key(self) -> AttributeComponent:
        return self.attributes[0]

    def copy(self) -> Any:
        copy = TemporalEntityComponent(self.name, self.label, None,
                                       None, None, self.entity_type, self.values)
        copy.set_attributes_value(super(TemporalEntityComponent, self).copy().attributes)
        copy.set_attributes_value(super(TemporalEntityComponent, self).copy().keys)
        return copy
