from multipledispatch import dispatch

from cnl2asp.ASP_elements.asp_attribute import ASPAttribute
from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.proposition.signaturemanager import SignatureManager



class ASPConjunction(ASPElement):
    def __init__(self, conjunction: list[ASPElement]):
        self.conjunction = conjunction

    @dispatch(list)
    def add_element(self, element: list[ASPElement]):
        self.conjunction += element

    @dispatch(ASPElement)
    def add_element(self, element: ASPElement):
        self.conjunction.append(element)

    def remove_element(self, element: ASPElement):
        self.conjunction.remove(element)

    def get_atom_list(self) -> list[ASPElement]:
        return self.conjunction

    def to_string(self) -> str:
        return ', '.join([x.to_string() for x in self.conjunction])

    def __eq__(self, other):
        if not isinstance(other, ASPConjunction):
            return False
        return self.conjunction == other.conjunction

    def __repr__(self):
        self.to_string()
