from __future__ import annotations
from multipledispatch import dispatch

from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.specification.signaturemanager import SignatureManager


class ASPConjunction(ASPElement):
    def __init__(self, conjunction: list[ASPElement]):
        self.conjunction = conjunction

    def remove_null_atoms(self):
        for atom in self.conjunction:
            if atom.is_null():
                self.remove_element(atom)
        for elem in self.conjunction:
            for atom in elem.get_atom_list():
                if atom.is_null():
                    elem.remove_element(atom)

    @dispatch(list)
    def add_element(self, element: list[ASPElement]):
        self.conjunction += element

    @dispatch(ASPElement)
    def add_element(self, element: ASPElement):
        if isinstance(element, ASPConjunction):
            for elem in element.conjunction:
                self.add_element(elem)
        else:
            self.conjunction.append(element)

    def remove_element(self, element: ASPElement):
        self.conjunction.remove(element)

    def get_atom_list(self) -> list[ASPElement]:
        atom_list = []
        for x in self.conjunction:
            atom_list += x.get_atom_list()
        return atom_list

    def __str__(self) -> str:
        return ', '.join([str(x) for x in self.conjunction if str(x)])

    def __eq__(self, other):
        if not isinstance(other, ASPConjunction):
            return False
        return self.conjunction == other.conjunction

    def __repr__(self):
        return str(self)
