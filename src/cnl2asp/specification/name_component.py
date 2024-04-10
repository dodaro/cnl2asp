from typing import Any

import inflect

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.specification.component import Component



class NameComponent(Component):
    def convert(self, converter: Converter) -> Any:
        return self.name

    def copy(self) -> Any:
        return NameComponent(self.name)

    def __init__(self, name: str):
        self.name = name
        self.singular_and_plural_name = [self.__singular(name), self.__plural(name), name]

    def removesuffix(self, suffix):
        self.name = self.name.removesuffix(suffix)
        for value in self.singular_and_plural_name:
            value = value.removesuffix(suffix)

    def __singular(self, string: str):
        if not string:
            return string
        singular = inflect.engine().singular_noun(string)
        return singular if singular else string

    def __plural(self, string: str):
        if not string:
            return string
        plural = inflect.engine().plural(string)
        return plural if plural != self.__singular(string) else string

    def strip(self):
        return self.name.strip()

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, str):
            return other in self.singular_and_plural_name
        if not isinstance(other, NameComponent):
            return False
        return self.name in other.singular_and_plural_name or other.name in self.singular_and_plural_name

    def __contains__(self, item):
        return item in self.name

    def __gt__(self, other):
        if isinstance(other, NameComponent):
            return self.name > other.name
