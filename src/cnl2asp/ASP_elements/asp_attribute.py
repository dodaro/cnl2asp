from __future__ import annotations

from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.proposition.attribute_component import AttributeOrigin
from cnl2asp.utility.utility import Utility


class ASPValue(ASPElement, str):
    def to_string(self):
        return self

    def __repr__(self):
        self.to_string()


class RangeASPValue(ASPValue):
    def __new__(cls, content):
        return str.__new__(cls, content.replace(' ', '..'))



class ASPAttribute(ASPElement):
    def __init__(self, name: str, value: ASPElement, origin: AttributeOrigin = None):
        self.name = name
        self.value = value
        self.origin = origin

    def to_string(self):
        return self.value.to_string()

    def isnull(self):
        return self.value == Utility.ASP_NULL_VALUE

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, ASPAttribute):
            return False
        return self.name == other.name and self.value == other.value

    def __repr__(self):
        self.to_string()
