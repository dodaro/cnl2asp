from __future__ import annotations

from typing import Any, TYPE_CHECKING

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.proposition.component import Component
if TYPE_CHECKING:
    from cnl2asp.proposition.operation_component import OperationComponent


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
        self.name = name
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
            return self.name + ' ' + str(self.origin)
        return self.name

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
        self.name = name
        # origin of the attribute, the entity from which it has been taken
        self.origin = attribute_origin
        self.value = AngleValueComponent(value) if self.is_angle() else value
        self.operations = operations

    def removesuffix(self, suffix: str):
        self.name = self.name.removesuffix(suffix)

    def convert(self, converter: Converter):
        return converter.convert_attribute(self)

    def add_operation(self, operation: OperationComponent):
        self.operations.append(operation)

    def copy(self) -> Any:
        return AttributeComponent(self.name, self.value.copy(), self.origin)

    def is_angle(self) -> bool:
        return 'angle' in self.name or (self.origin.is_angle() if self.origin else False)

    def __eq__(self, other):
        if not isinstance(other, AttributeComponent):
            return False
        return self.name == other.name and self.value == other.value

    def __str__(self):
        return str(self.origin) + ' ' + self.name

