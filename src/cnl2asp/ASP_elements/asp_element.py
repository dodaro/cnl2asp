from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cnl2asp.ASP_elements.asp_atom import ASPAtom


class ASPElement:
    def get_attributes_list(self, name):
        raise Exception("Looking for attribute in a non-ASPAtom element.")

    def get_atom_list(self) -> list[ASPAtom]:
        return []

    def remove_element(self, element):
        pass

    def is_null(self):
        return False
