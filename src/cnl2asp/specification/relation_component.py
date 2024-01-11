from __future__ import annotations

from typing import TYPE_CHECKING

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.specification.component import Component

if TYPE_CHECKING:
    from cnl2asp.specification.entity_component import EntityComponent


class RelationComponent(Component):
    def __init__(self, entity_1: EntityComponent, entity_2: EntityComponent):
        self.relation_component_1 = entity_1
        self.relation_component_2 = entity_2

    def convert(self, converter: Converter):
        converter.convert_relation(self.relation_component_1, self.relation_component_2)

    def copy(self):
        return RelationComponent(self.relation_component_1.copy(), self.relation_component_2.copy())

    def get_entities(self) -> list[EntityComponent]:
        entities: list[EntityComponent] = []
        for entity in self.relation_component_1.get_entities():
            entities += entity.get_entities()
        for entity in self.relation_component_2.get_entities():
            entities += entity.get_entities()
        return entities

