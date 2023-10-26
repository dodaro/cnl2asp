from __future__ import  annotations

from typing import TYPE_CHECKING

from cnl2asp.proposition.operation_component import Operators
from cnl2asp.ASP_elements.asp_element import ASPElement

if TYPE_CHECKING:
    from cnl2asp.ASP_elements.asp_atom import ASPAtom


class ASPOperation(ASPElement):
    operators = {
        Operators.SUM: '+',
        Operators.DIFFERENCE: '-',
        Operators.MULTIPLICATION: '*',
        Operators.DIVISION: '\\',
        Operators.EQUALITY: '=',
        Operators.INEQUALITY: '!=',
        Operators.GREATER_THAN: '>',
        Operators.LESS_THAN: '<',
        Operators.GREATER_THAN_OR_EQUAL_TO: '>=',
        Operators.LESS_THAN_OR_EQUAL_TO: '<='
    }

    def __init__(self, operator: Operators, *operands: ASPElement):
        self.operator = operator
        self.operands = [operand for operand in operands]

    def get_atom_list(self) -> list[ASPAtom]:
        atom_list: list[ASPAtom] = []
        for operand in self.operands:
            atom_list += operand.get_atom_list()
        return atom_list

    def remove_element(self, element):
        if element in self.operands:
            self.operands.remove(element)
        else:
            for elem in self.operands:
                if element in elem.get_atom_list():
                    elem.remove_element(element)


    def to_string(self) -> str:
        return f' {ASPOperation.operators[self.operator]} '.join([operand.to_string() for operand in self.operands])

    def __repr__(self):
        self.to_string()


class ASPAngleOperation(ASPOperation):
    def __init__(self, operator: Operators, *operands: ASPElement):
        super(ASPAngleOperation, self).__init__(operator, *operands)

    def to_string(self) -> str:
        if self.operator != Operators.SUM and self.operator != Operators.DIFFERENCE and \
                self.operator != Operators.MULTIPLICATION and self.operator != Operators.DIVISION:
            return f' {ASPOperation.operators[self.operator]} '.join(['(' + operand.to_string() + ')/360' for operand in self.operands])
        else:
            return super(ASPAngleOperation, self).to_string()
