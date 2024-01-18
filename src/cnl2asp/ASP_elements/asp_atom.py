from __future__ import annotations


from cnl2asp.proposition.attribute_component import AttributeOrigin, is_same_origin
from cnl2asp.utility.utility import Utility
from .asp_attribute import ASPAttribute
from .asp_element import ASPElement


class ASPAtom(ASPElement):
    def __init__(self, name: str, attributes: list[ASPAttribute], negated: bool = False):
        self.name = name
        self.attributes = attributes
        self.negated = negated

    def set_attributes_value(self, attributes: list[ASPAttribute]):
        for attribute in attributes:
            # get the list of matching attributes
            atom_attributes = self.get_attributes_list(attribute.name, attribute.origin)
            for atom_attribute in atom_attributes:
                # update only the first occurrence
                if atom_attribute.is_null():
                    atom_attribute.set_value(attribute.get_value())
                    break

    def get_atom_list(self) -> list[ASPAtom]:
        return [self]

    def is_null(self):
        for attribute in self.attributes:
            if not attribute.is_null():
                return False
        return True

    def has_attribute(self, attribute: ASPAttribute):
        if attribute in self.attributes:
            return True
        return False

    def get_attributes_list(self, name: str, origin: AttributeOrigin = None) -> list[ASPAttribute]:
        if origin:
            return self.get_attributes_list_by_name_and_origin(name, origin)
        else:
            return self.get_attributes_list_by_name(name)

    def get_attributes_list_by_name(self, name: str) -> list[ASPAttribute]:
        attributes = []
        for attribute in self.attributes:
            if attribute.name == name:
                attributes.append(attribute)
        return attributes

    def get_attributes_list_by_name_and_origin(self, name: str, origin: AttributeOrigin = None) -> list[ASPAttribute]:
        attributes = []
        for attribute in self.get_attributes_list_by_name(name):
            if is_same_origin(attribute.origin, origin):
                attributes.append(attribute)
        return attributes

    def __str__(self) -> str:
        string = ''
        string += 'not ' if self.negated else ''
        string += f'{self.name}('
        if Utility.PRINT_WITH_FUNCTIONS:
            visited = []
            for attribute1 in self.attributes:
                if attribute1 in visited:
                    continue
                visited.append(attribute1)
                if attribute1.origin and attribute1.origin.name != self.name:
                    tmp_atom = ASPAtom(attribute1.origin.name, [ASPAttribute(attribute1.name, attribute1.get_value(),
                                                                             attribute1.origin.origin)])
                    for attribute2 in self.attributes:
                        if attribute2 in visited:
                            continue
                        if attribute2.origin and attribute1.origin.name == attribute2.origin.name:
                            visited.append(attribute2)
                            tmp_atom.attributes.append(ASPAttribute(attribute2.name, attribute2.get_value(),
                                                                    attribute2.origin.origin))
                    string += str(tmp_atom) + ','
                else:
                    string += str(attribute1) + ','
            if string[-1] == ',':
                string = string[0:-1]
            return string + ')'
        else:
            return string + f'{",".join([str(x) for x in self.attributes])})'

    def __eq__(self, other):
        if not isinstance(other, ASPAtom):
            return False
        return self.name == other.name and self.attributes == other.attributes

    def __repr__(self):
        return str(self)
