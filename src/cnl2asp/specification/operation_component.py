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
    BEFORE = 20
    WEAK_PREVIOUS = 21
    TRIGGER = 22
    ALWAYS_BEFORE = 23
    SINCE = 24
    EVENTUALLY_BEFORE = 25
    PRECEDE = 26
    WEAK_PRECEDE = 27
    NEXT = 28
    AFTER = 29
    WEAK_NEXT = 30
    RELEASE = 31
    ALWAYS_AFTER = 32
    UNTIL = 33
    EVENTUALLY_AFTER = 34
    FOLLOW = 35
    WEAK_FOLLOW = 36

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

class OperationComponent(Component):
    def __init__(self, operator: Operators, *operands: Component, negated = False):
        self.operation = operator
        self.operands = []
        self.negated = negated
        if self.operation == Operators.BETWEEN:
            operands = self.between_operator(operands)
        for operand in operands:
            if not isinstance(operand, Component):
                operand = ValueComponent(operand)
            self.operands.append(operand)
        self.auxiliary_verb = None


    def between_operator(self, operands):
        operands = list(operands)
        if self.operation == Operators.BETWEEN:
            self.operation = Operators.LESS_THAN_OR_EQUAL_TO
        elif self.operation == Operators.NOTBETWEEN:
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

    def get_entities_to_link_with_new_knowledge(self) -> list[EntityComponent]:
        entities = []
        for operand in self.operands:
            entities += operand.get_entities_to_link_with_new_knowledge()
        return entities

    def convert(self, converter: Converter) -> OperationConverter:
        return converter.convert_operation(self)

    def copy(self):
        operands = [component for component in self.operands]
        return OperationComponent(self.operation, *operands, negated = self.negated)

    def is_angle(self) -> False:
        for operand in self.operands:
            if operand.is_angle():
                return True
        return False

    def negate(self):
        self.negated = True
