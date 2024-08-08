from __future__ import annotations

import abc
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TYPE_CHECKING

from cnl2asp.exception.cnl2asp_exceptions import AttributeNotFound
from cnl2asp.converter.converter_interface import Converter, EntityConverter
from cnl2asp.specification.attribute_component import AttributeComponent, ValueComponent, \
    AttributeOrigin, is_same_origin
from cnl2asp.specification.component import Component
from cnl2asp.specification.name_component import NameComponent
from cnl2asp.specification.relation_component import RelationComponent
from cnl2asp.utility.utility import Utility

if TYPE_CHECKING:
    from cnl2asp.parser.proposition_builder import PropositionBuilder


class EntityType(Enum):
    GENERIC = 0
    TIME = 1
    DATE = 2
    STEP = 3
    ANGLE = 4
    SET = 5
    LIST = 6


class EntityComponent(Component):
    def __init__(self, name: str, label: str, keys: list[AttributeComponent], attributes: list[AttributeComponent],
                 negated: bool = False, entity_type: EntityType = EntityType.GENERIC,
                 is_before: bool = False, is_after: bool = False, is_initial: bool = False,
                 is_final: bool = False, auxiliary_verb: str = ""):
        self._name = NameComponent(name)
        self.label = label
        self.keys = keys if keys else []
        self.attributes = attributes if attributes else []
        for attribute in self.attributes:
            if attribute.origin is None:
                attribute.origin = AttributeOrigin(self.get_name())
        self.negated = negated
        self.entity_type = entity_type
        self.auxiliary_verb = auxiliary_verb
        self.is_before = is_before
        self.is_after = is_after
        self.is_initial = is_initial
        self.is_final = is_final

    def label_is_key_value(self):
        if self.label and len(self.get_keys()) == 1 and self.get_keys()[0].value == Utility.NULL_VALUE:
            return True
        return False

    def set_label_as_key_value(self):
        self.set_attributes_value([AttributeComponent(self.get_keys()[0].get_name(),
                                   ValueComponent(self.label), self.get_keys()[0].origin)])

    def set_name(self, name: str):
        self._name = NameComponent(name)

    def get_name(self):
        return str(self._name)

    def is_initialized(self) -> bool:
        if self.get_keys_and_attributes():
            return True
        return False

    def get_initialized_attributes(self) -> list[AttributeComponent]:
        res = []
        for attribute in self.get_attributes():
            if attribute.value != Utility.NULL_VALUE:
                res.append(attribute)
        return res

    def has_attribute_value(self, value: ValueComponent) -> bool:
        for attribute in self.attributes:
            if attribute.value == value:
                return True
        return False

    def convert(self, converter: Converter) -> EntityConverter:
        return converter.convert_entity(self)

    def negate(self):
        self.negated = not self.negated

    def get_entity_identifier(self):
        return self._name

    def get_keys(self) -> list[AttributeComponent]:
        return self.keys if self.keys else self.attributes

    def get_attributes(self) -> list[AttributeComponent]:
        if self.keys:
            return self.attributes
        return []

    def get_keys_and_attributes(self) -> list[AttributeComponent]:
        return self.keys + self.attributes

    def set_attributes_value(self, attributes: list[AttributeComponent], proposition: PropositionBuilder = None):
        def update_attribute(attribute, value, operations):
            attribute.value = value
            attribute.operations = operations

        def get_first_null_attribute(attributes):
            for attribute in attributes:
                if attribute.value == Utility.NULL_VALUE:
                    return attribute
            return None

        for attribute in attributes:
            if isinstance(attribute, EntityComponent):
                if not proposition:
                    raise RuntimeError('Error in compilation phase.')
                proposition.add_relations([RelationComponent(self, attribute)])
            else:
                origin = attribute.origin
                if not origin:
                    origin = AttributeOrigin(str(self.get_name()))
                matching_attributes = self.get_attributes_by_name_and_origin(attribute.get_name(), origin)
                if get_first_null_attribute(matching_attributes):
                    update_attribute(get_first_null_attribute(matching_attributes), attribute.value,
                                     attribute.operations)
                else:
                    for matching_attribute in matching_attributes:
                        update_attribute(matching_attribute, attribute.value, attribute.operations)

    def set_attribute_value(self, attribute_name: str, value: ValueComponent, origin: AttributeOrigin = None):
        if not origin:
            origin = self.get_attributes_by_name(attribute_name)[0].origin
        self.set_attributes_value([AttributeComponent(attribute_name, value, origin)])

    def get_attributes_by_name_and_origin(self, name: str, origin: AttributeOrigin = None) -> list[AttributeComponent]:
        attributes = []
        origin = AttributeOrigin(self.get_name()) if not origin else origin
        for attribute in self.get_keys_and_attributes():
            if attribute.name_match(name) and is_same_origin(attribute.origin, origin):
                attributes.append(attribute)
        if attributes:
            return attributes
        else:
            error_msg = f'Entity \"{self.get_name()}\" do not contain attribute \"{origin} {name}\".'
            try:
                hint = self.get_attributes_by_name(name)
                error_msg += f'\nDid you mean \"{hint[0]}\"?'
            except AttributeNotFound:
                pass
            raise AttributeNotFound(error_msg)

    def get_attributes_by_name(self, name: str) -> list[AttributeComponent]:
        attributes = []
        for attribute in self.get_keys_and_attributes():
            if attribute.name_match(name):
                attributes.append(attribute)
        if attributes:
            return attributes
        raise AttributeNotFound(f'Entity \"{self.get_name()}\" do not contain attribute \"{name}\".')

    def copy(self) -> EntityComponent:
        keys = [key.copy() for key in self.keys]
        attributes = [attribute.copy() for attribute in self.attributes]
        return EntityComponent(self.get_name(), self.label, keys,
                               attributes, self.negated, self.entity_type,
                               self.is_before, self.is_after, self.is_initial, self.is_final,
                               self.auxiliary_verb)

    def get_entities(self) -> list[EntityComponent]:
        return [self]

    def get_entities_to_link_with_new_knowledge(self) -> list[EntityComponent]:
        return [self]

    def is_temporal_entity(self) -> bool:
        return False

    def __eq__(self, other):
        if not isinstance(other, EntityComponent):
            return False
        return self._name == other._name \
               and self.label == other.label \
               and self.keys == other.keys \
               and self.attributes == other.attributes \
               and self.negated == other.negated \
               and self.entity_type == other.entity_type


class TemporalEntityComponent(EntityComponent):
    def __init__(self, name: str, label: str,
                 lhs_range_value: ValueComponent,
                 rhs_range_value: ValueComponent, step: ValueComponent,
                 entity_type: EntityType, values: dict = None):
        super().__init__(name, label,
                         [AttributeComponent(name, ValueComponent('_'), AttributeOrigin(name))],
                         [AttributeComponent('value', ValueComponent('_'), AttributeOrigin(name))],
                         entity_type=entity_type)
        step = 1 if not step else step
        self.values: dict = self._compute_values(lhs_range_value, rhs_range_value, step) if not values else values

    def get_temporal_value_id(self, value: ValueComponent):
        temporal_value_id = self.values.get(value)
        if temporal_value_id is not None:
            return temporal_value_id
        raise KeyError(f'Value "{value}" out of "{self.get_name()}" range')

    def _compute_values(self, lhs_value: ValueComponent, rhs_value: ValueComponent,
                        step: ValueComponent) -> dict:
        """
        Compute all the values in the range and assign a label starting from 0
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
                elements[start.strftime('%I:%M %p')] = 0
                start = start + timedelta(minutes=int(step))
                while start <= end:
                    if start > end:
                        start = end
                    elements[start.strftime('%I:%M %p')] = counter
                    counter += 1
                    start = start + timedelta(minutes=int(step))
            elif self.entity_type == EntityType.DATE:
                start = datetime.strptime(lhs_value, '%d/%m/%Y')
                end = datetime.strptime(rhs_value, '%d/%m/%Y')
                elements[start.strftime('%d/%m/%Y')] = 0
                start = start + timedelta(days=int(step))
                while start <= end:
                    if start > end:
                        start = end
                    elements[start.strftime('%d/%m/%Y')] = counter
                    counter += 1
                    start = start + timedelta(days=int(step))
            elif self.entity_type == EntityType.STEP:
                start = lhs_value
                end = rhs_value
                elements[int(start)] = 0
                for i in range(int(start) + 1, int(end) + 1):
                    elements[i] = counter
                    counter += 1
        except:
            raise Exception(f"Entity {self.get_name()}, entity type do not match {lhs_value} and {rhs_value}")
        return elements

    def is_temporal_entity(self) -> bool:
        return True

    def get_temporal_key(self) -> AttributeComponent:
        return self.keys[0]

    def copy(self) -> Any:
        copy = TemporalEntityComponent(self.get_name(), self.label, None,
                                       None, None, self.entity_type, self.values)
        copy.set_attributes_value(super(TemporalEntityComponent, self).copy().attributes)
        copy.set_attributes_value(super(TemporalEntityComponent, self).copy().keys)
        return copy

    def convert(self, converter: Converter):
        return converter.convert_temporal_entity(self)


class ComplexEntityComponent(EntityComponent):
    def __init__(self, name: str, complex_entity_id: ValueComponent, keys: list[AttributeComponent],
                 attributes: list[AttributeComponent], entity_type: EntityType, values: list[ValueComponent] = None):
        if values is None:
            self.values = []
        else:
            self.values = values
        self.entity_identifier = complex_entity_id
        super().__init__(name, '', keys, attributes, False, entity_type)

    def get_entity_identifier(self):
        return self.entity_identifier

    def set_values(self, values):
        self.values = values


class SetEntityComponent(ComplexEntityComponent):
    def __init__(self, set_id: ValueComponent = None, values: list[ValueComponent] = None):
        super().__init__('set', set_id, [AttributeComponent('set_id', set_id, AttributeOrigin('set')),
                                         AttributeComponent('element', ValueComponent(Utility.NULL_VALUE),
                                                            AttributeOrigin('set'))],

                         [], EntityType.SET, values)

    def is_value_in_set(self, value: ValueComponent) -> bool:
        for set_value in self.values:
            if value == set_value:
                return True
        return False

    def set_label_as_key_value(self):
        if self.label in self.values:
            self.set_attribute_value('element', ValueComponent(self.label))

    def copy(self) -> SetEntityComponent:
        return SetEntityComponent(self.entity_identifier, self.values)


class ListEntityComponent(ComplexEntityComponent):
    def __init__(self, list_id: ValueComponent = None, values: list[ValueComponent] = None):
        super().__init__('list', list_id, [AttributeComponent('list_id', list_id, AttributeOrigin('list')),
                                           AttributeComponent('index', ValueComponent(Utility.NULL_VALUE),
                                                              AttributeOrigin('list'))],
                         [AttributeComponent('element', ValueComponent(Utility.NULL_VALUE), AttributeOrigin('list'))],
                         EntityType.LIST, values)

    def set_label_as_key_value(self):
        if self.label in self.values:
            self.set_attribute_value('element', ValueComponent(self.label))
            self.set_attribute_value('index', ValueComponent(self.values.index(ValueComponent(self.label))))

    def copy(self) -> ListEntityComponent:
        return ListEntityComponent(self.entity_identifier, self.values)

    def set_shifted_value(self, shift_value: int, starting_value: str, element_variable: ValueComponent):
        element_index = (self.values.index(ValueComponent(starting_value)) + shift_value) % len(self.values)
        element = self.values[element_index]
        if element_variable:
            element_index = element_variable
        self.set_attribute_value('index', ValueComponent(element_index))
        self.set_attribute_value('element', ValueComponent(element))

    def set_index_value(self, index: int, element_variable: ValueComponent):
        element = self.values[index]
        if element_variable:
            index = element_variable
        self.set_attribute_value('index', ValueComponent(index))
        self.set_attribute_value('element', ValueComponent(element))
