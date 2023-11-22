from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from proposition.entity_component import EntityComponent
    from converter.converter_interface import Converter


class Component(ABC):
    @abstractmethod
    def convert(self, converter: Converter) -> Any:
        """Convert self"""

    @abstractmethod
    def copy(self) -> Any:
        """Return a copy of the component"""

    def get_entities(self) -> list[EntityComponent]:
        return []

    def negate(self):
        pass

    def is_angle(self) -> bool:
        return False

