from __future__ import annotations

from typing import TYPE_CHECKING

from cnl2asp.ASP_elements.asp_operation import ASPOperation
from cnl2asp.specification.attribute_component import AttributeOrigin
from cnl2asp.utility.utility import Utility

from cnl2asp.ASP_elements.asp_element import ASPElement


class ASPValue(ASPElement, str):
    def is_null(self):
        return self == Utility.ASP_NULL_VALUE

    def set_value(self, value: ASPValue):
        return ASPValue(value)


class RangeASPValue(ASPValue):
    def __new__(cls, content):
        return str.__new__(cls, content.replace(' ', '..'))

    def is_null(self):
        if self[0] == Utility.ASP_NULL_VALUE:
            return True
        return False

    def set_value(self, value: ASPValue):
        if Utility.ASP_NULL_VALUE not in self:
            return value
        value = self.replace(Utility.ASP_NULL_VALUE, value).replace('..', ' ')
        return RangeASPValue(value)


class ASPAttribute(ASPElement):
    def __init__(self, name: str, value: ASPValue, origin: AttributeOrigin = None,
                 operations: list[ASPOperation] = None):
        if operations is None:
            operations = []
        self.name = name
        self._value = value
        self.origin = origin
        self.operations = operations

    def is_null(self):
        return self._value.is_null()

    def set_value(self, value: ASPValue):
        self._value = self._value.set_value(value)

    def get_value(self):
        return self._value

    def __str__(self):
        return f'{self._value}'

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, ASPAttribute):
            return False
        return self.name == other.name and self._value == other._value

    def __repr__(self):
        str(self)
