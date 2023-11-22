from typing import Any

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.specification.attribute_component import ValueComponent
from cnl2asp.specification.component import Component


class ConstantComponent(Component):
    def __init__(self, name: str, value: ValueComponent):
        self.name = name
        self.value = value

    def convert(self, converter: Converter):
        return converter.convert_constant(self)

    def copy(self) -> Any:
        return ConstantComponent(self.name, self.value.copy())
