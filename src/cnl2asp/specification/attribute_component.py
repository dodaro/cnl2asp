from __future__ import annotations

from typing import Any, TYPE_CHECKING

import inflect

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.specification.component import Component
from cnl2asp.specification.name_component import NameComponent

if TYPE_CHECKING:
    from cnl2asp.specification.operation_component import OperationComponent


class ValueComponent(Component, str):
    def convert(self, converter: Converter):
        return converter.convert_value(self)

    def copy(self) -> Any:
        return ValueComponent(self)

    def is_angle(self) -> bool:
        return False


class AngleValueComponent(ValueComponent):

    def copy(self) -> Any:
        return AngleValueComponent(self)

    def is_angle(self) -> bool:
        return True


class RangeValueComponent(ValueComponent):
    def __new__(cls, *content):
        value = content[0]
        if len(content) > 1:
            value += f' {content[1]}'
        return str.__new__(cls, value)

    def convert(self, converter: Converter):
        return converter.convert_range_value(self)

    def copy(self) -> Any:
        return RangeValueComponent(self)


class AttributeOrigin:
    def __init__(self, name: str, origin: AttributeOrigin = None):
        self.name = NameComponent(str(name))
        self.origin = origin
        if origin and self.name == origin.name:
            # avoid nesting same origin
            self.origin = origin.origin

    def is_angle(self):
        if 'angle' in self.name:
            return True
        if self.origin:
            return self.origin.is_angle()
        return False

    def __str__(self):
        if self.origin:
            return str(self.name) + ' ' + str(self.origin)
        return str(self.name)

    def __eq__(self, other):
        if not isinstance(other, AttributeOrigin):
            return False
        if self.name == other.name:
            if self.origin:
                return self.origin == other.origin
            elif not self.origin and not other.origin:
                return True
        return False


def is_same_origin(origin_1: AttributeOrigin, origin_2: AttributeOrigin) -> bool:
    if origin_1 and not origin_2:
        return False
    if origin_2 and not origin_1:
        return False
    # one can be the subset of the other
    if origin_1 == origin_2:
        return True
    if origin_1.origin == origin_2:
        return True
    if origin_2.origin == origin_1:
        return True
    return False


class AttributeComponent(Component):
    def __init__(self, name: str, value: ValueComponent,
                 attribute_origin: AttributeOrigin = None,
                 operations: list[OperationComponent] = None):
        if operations is None:
            operations = []
        self._name = NameComponent(str(name))
        # origin of the attribute, the entity from which it has been taken
        self.origin = attribute_origin
        self.value = AngleValueComponent(value) if self.is_angle() else value
        self.operations = operations

    def name_match(self, name: str) -> bool:
        if self._name == name:
            return True
        return False

    def set_name(self, name: str):
        self._name = NameComponent(name)

    def get_name(self):
        return str(self._name)

    def removesuffix(self, suffix: str):
        self._name.removesuffix(suffix)

    def convert(self, converter: Converter):
        return converter.convert_attribute(self)

    def add_operation(self, operation: OperationComponent):
        self.operations.append(operation)

    def copy(self) -> Any:
        return AttributeComponent(self.get_name(), self.value.copy(), self.origin)

    def is_angle(self) -> bool:
        return 'angle' in self.get_name() or (self.origin.is_angle() if self.origin else False)

    def __eq__(self, other):
        if not isinstance(other, AttributeComponent):
            return False
        return self._name == other._name and self.value == other.value

    def __str__(self):
        return str(self.origin) + ' ' + self.get_name()
