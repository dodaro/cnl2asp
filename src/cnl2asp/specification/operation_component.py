from __future__ import annotations

from enum import Enum
from functools import total_ordering

from cnl2asp.converter.converter_interface import Converter, OperationConverter
from cnl2asp.specification.attribute_component import ValueComponent
from cnl2asp.specification.component import Component
from cnl2asp.specification.entity_component import EntityComponent


@total_ordering
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
    BETWEEN = 10
    NOTBETWEEN = 11
    ABSOLUTE_VALUE = 12
    CONJUNCTION = 13
    DISJUNCTION = 14
    LEFT_IMPLICATION = 15
    RIGHT_IMPLICATION = 16
    EQUIVALENCE = 17
    NEGATION = 18
    PREVIOUS = 19
    WEAK_PREVIOUS = 20
    TRIGGER = 21
    ALWAYS_BEFORE = 22
    SINCE = 23
    EVENTUALLY_BEFORE = 24
    PRECEDE = 25
    WEAK_PRECEDE = 26
    NEXT = 27
    WEAK_NEXT = 28
    RELEASE = 29
    ALWAYS_AFTER = 30
    UNTIL = 31
    EVENTUALLY_AFTER = 32
    FOLLOW = 33
    WEAK_FOLLOW = 34

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


operators_negation = {
    Operators.EQUALITY: Operators.INEQUALITY,
    Operators.INEQUALITY: Operators.EQUALITY,
    Operators.GREATER_THAN: Operators.LESS_THAN_OR_EQUAL_TO,
    Operators.LESS_THAN: Operators.GREATER_THAN_OR_EQUAL_TO,
    Operators.GREATER_THAN_OR_EQUAL_TO: Operators.LESS_THAN,
    Operators.LESS_THAN_OR_EQUAL_TO: Operators.GREATER_THAN,
    Operators.BETWEEN: Operators.NOTBETWEEN
}


class OperationComponent(Component):
    def __init__(self, operator: Operators, *operands: Component):
        self.operator = operator
        self.operands = []
        if self.operator == Operators.BETWEEN:
            operands = self.between_operator(operands)
        for operand in operands:
            if not isinstance(operand, Component):
                operand = ValueComponent(operand)
            self.operands.append(operand)


    def between_operator(self, operands):
        operands = list(operands)
        if self.operator == Operators.BETWEEN:
            self.operator = Operators.LESS_THAN_OR_EQUAL_TO
        elif self.operator == Operators.NOTBETWEEN:
            raise NotImplemented("Operator not between not implemented")
        for operand in operands:
            if isinstance(operand, list):
                operands.insert(0, operand[0])
                operands.append(operand[1])
                operands.remove(operand)
        return operands


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