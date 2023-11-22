from __future__ import annotations

from typing import TYPE_CHECKING

from cnl2asp.specification.operation_component import Operators
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

    def _operator_to_symbol(self, operator):
        return ASPOperation.operators[self.operator]

    def __str__(self) -> str:
        string = ''
        for operand in self.operands:
            if not isinstance(operand, ASPOperation):
                string += str(operand)
            else:
                string += f'({str(operand)})'
            string += f' {self._operator_to_symbol(self.operator)} '
        return string.removesuffix(f' {self._operator_to_symbol(self.operator)} ')

    def __repr__(self):
        return str(self)


class ASPAngleOperation(ASPOperation):
    def __init__(self, operator: Operators, *operands: ASPElement):
        super(ASPAngleOperation, self).__init__(operator, *operands)

    def __str__(self) -> str:
        if self.operator != Operators.SUM and self.operator != Operators.DIFFERENCE and \
                self.operator != Operators.MULTIPLICATION and self.operator != Operators.DIVISION:
            return f' {ASPOperation.operators[self.operator]} '.join(
                ['(' + str(operand) + ')/360' for operand in self.operands])
        else:
            return super(ASPAngleOperation, self).__str__()


class ASPTemporalOperation(ASPOperation):
    asp_temporal_operators = {
        Operators.CONJUNCTION: '&',
        Operators.DISJUNCTION: '|',
        Operators.LEFT_IMPLICATION: '<-',
        Operators.RIGHT_IMPLICATION: '->',
        Operators.EQUIVALENCE: '<>',
        Operators.NEGATION: '~',
        Operators.PREVIOUS: '<',
        Operators.WEAK_PREVIOUS: '<:',
        Operators.TRIGGER: '<*',
        Operators.ALWAYS_BEFORE: '<*',
        Operators.SINCE: '<?',
        Operators.EVENTUALLY_BEFORE: '<?',
        Operators.PRECEDE: '<;',
        Operators.WEAK_PRECEDE: '<:;',
        Operators.NEXT: '>',
        Operators.WEAK_NEXT: '>:',
        Operators.RELEASE: '>*',
        Operators.ALWAYS_AFTER: '>*',
        Operators.UNTIL: '>?',
        Operators.EVENTUALLY_AFTER: '>?',
        Operators.FOLLOW: ';>',
        Operators.WEAK_FOLLOW: ';>:',
    }

    def __init__(self, operator: Operators, *operands: ASPElement):
        super(ASPTemporalOperation, self).__init__(operator, *operands)

    def _operator_to_symbol(self, operator):
        return ASPTemporalOperation.asp_temporal_operators.get(operator)

    def __str__(self) -> str:
        if len(self.operands) > 1:
            return f'{super(ASPTemporalOperation, self).__str__()}'
        else:
            # return f'{self._operator_to_symbol(self.operator)} {self.operands[0]}'
            string = ''
            string += f'{self._operator_to_symbol(self.operator)} '
            operand = self.operands[0]
            if not isinstance(operand, ASPOperation):
                string += str(operand)
            else:
                string += f'({str(operand)})'
            return string
