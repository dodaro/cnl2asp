from __future__ import annotations

from enum import Enum

from cnl2asp.converter.converter_interface import Converter, OperationConverter
from cnl2asp.proposition.attribute_component import ValueComponent
from cnl2asp.proposition.component import Component
from cnl2asp.proposition.entity_component import EntityComponent


class Operators(Enum):
    SUM = 0
    DIFFERENCE = 1
    MULTIPLICATION = 2
    DIVISION = 3
    EQUALITY = 4
    INEQUALITY = 5
    GREATER_THAN = 6
    LESS_THAN = 7
    GREATER_THAN_OR_EQUAL_TO = 8
    LESS_THAN_OR_EQUAL_TO = 9


operators_negation = {
    Operators.EQUALITY: Operators.INEQUALITY,
    Operators.INEQUALITY: Operators.EQUALITY,
    Operators.GREATER_THAN: Operators.LESS_THAN_OR_EQUAL_TO,
    Operators.LESS_THAN: Operators.GREATER_THAN_OR_EQUAL_TO,
    Operators.GREATER_THAN_OR_EQUAL_TO: Operators.LESS_THAN,
    Operators.LESS_THAN_OR_EQUAL_TO: Operators.GREATER_THAN
}


class OperationComponent(Component):
    def __init__(self, operator: Operators, *operands: Component):
        self.operator = operator
        self.operands = []
        for operand in operands:
            if not isinstance(operand, Component):
                operand = ValueComponent(operand)
            self.operands.append(operand)

    def get_entities(self) -> list[EntityComponent]:
        entities = []
        for operand in self.operands:
            entities += operand.get_entities()
        return entities

    def convert(self, converter: Converter) -> OperationConverter:
        return converter.convert_operation(self)

    def copy(self):
        operands = [component for component in self.operands]
        return OperationComponent(self.operator, *operands)

    def is_angle(self) -> False:
        for operand in self.operands:
            if operand.is_angle():
                return True
        return False

    def negate(self):
        self.operator = operators_negation[self.operator]