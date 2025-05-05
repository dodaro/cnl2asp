from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from cnl2asp.specification.entity_component import EntityComponent
    from cnl2asp.converter.converter_interface import Converter


class Component(ABC):
    @abstractmethod
    def convert(self, converter: Converter) -> Any:
        """Convert self"""

    def get_entities(self) -> list[EntityComponent]:
        return []

    def get_entities_to_link_with_new_knowledge(self) -> list[EntityComponent]:
        return []

    def negate(self):
        pass

    def is_angle(self) -> bool:
        return False

