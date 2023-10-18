from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.proposition.operation_component import Operators


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
