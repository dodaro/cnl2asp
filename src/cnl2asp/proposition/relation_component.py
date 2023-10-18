from __future__ import annotations

from typing import TYPE_CHECKING

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.proposition.component import Component

if TYPE_CHECKING:
    from cnl2asp.proposition.entity_component import EntityComponent


class RelationComponent(Component):
    def __init__(self, entity_1: EntityComponent, entity_2: EntityComponent):
        self.entity_1 = entity_1
        self.entity_2 = entity_2

    def convert(self, converter: Converter):
        converter.convert_relation(self)

    def copy(self):
        return RelationComponent(self.entity_1.copy(), self.entity_2.copy())

    def get_entities(self) -> list[EntityComponent]:
        entities: list[EntityComponent] = []
        for entity in self.entity_1.get_entities():
            entities += entity.get_entities()
        for entity in self.entity_2.get_entities():
            entities += entity.get_entities()
        return entities

