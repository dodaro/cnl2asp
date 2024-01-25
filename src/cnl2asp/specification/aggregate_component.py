from __future__ import annotations

from enum import Enum

from cnl2asp.specification.attribute_component import AttributeComponent
from cnl2asp.specification.component import Component
from cnl2asp.converter.converter_interface import Converter, AggregateConverter
from cnl2asp.specification.entity_component import EntityComponent


class AggregateOperation(Enum):
    COUNT = 0
    SUM = 1
    MAX = 2
    MIN = 3


class AggregateComponent(Component):
    def __init__(self, operation: AggregateOperation, discriminant: list[AttributeComponent], body: list[Component]):
        self.operation = operation
        self.discriminant = discriminant
        self.body = body

    def convert(self, converter: Converter) -> AggregateConverter:
        return converter.convert_aggregate(self)

    def copy(self):
        return AggregateComponent(self.operation, [discriminant.copy() for discriminant in self.discriminant])

    def get_entities(self) -> list[EntityComponent]:
        entities = []
        for entity in self.body:
            entities += entity.get_entities()
        return entities
