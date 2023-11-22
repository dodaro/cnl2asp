from __future__ import annotations

from typing import TYPE_CHECKING

from cnl2asp.ASP_elements.asp_operation import ASPOperation
from cnl2asp.specification.attribute_component import AttributeOrigin
from cnl2asp.utility.utility import Utility

from cnl2asp.ASP_elements.asp_element import ASPElement


class ASPValue(ASPElement, str):
    pass

class RangeASPValue(ASPValue):
    def __new__(cls, content):
        return str.__new__(cls, content.replace(' ', '..'))


class ASPAttribute(ASPElement):
    def __init__(self, name: str, value: ASPElement, origin: AttributeOrigin = None,
                 operations: list[ASPOperation] = None):
        if operations is None:
            operations = []
        self.name = name
        self.value = value
        self.origin = origin
        self.operations = operations

    def is_null(self):
        if self.value == Utility.ASP_NULL_VALUE:
            return True
        return False

    def __str__(self):
        return f'{self.value}'

    def isnull(self):
        return self.value == Utility.ASP_NULL_VALUE

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, ASPAttribute):
            return False
        return self.name == other.name and self.value == other.value

    def __repr__(self):
        str(self)
