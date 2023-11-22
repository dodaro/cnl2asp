from __future__ import annotations

from typing import Any

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.specification.attribute_component import ValueComponent
from cnl2asp.specification.component import Component
from cnl2asp.specification.constant_component import ConstantComponent
from cnl2asp.specification.entity_component import EntityComponent
from cnl2asp.specification.proposition import Proposition
from cnl2asp.specification.signaturemanager import SignatureManager
from cnl2asp.utility.utility import Utility


class Problem(Component):
    def __init__(self, name: str = None, propositions: list[Proposition] = None):
        self.name = name
        if propositions is None:
            propositions = []
        self._propositions = propositions


    def add_proposition(self, proposition: Proposition):
        self._propositions.append(proposition)

    def add_propositions(self, propositions: list[Proposition]):
        for proposition in propositions:
            if not proposition.is_empty():
                self._propositions.append(proposition)

    def get_propositions(self) -> list[Proposition]:
        return self._propositions

    def convert(self, converter: Converter) -> Any:
        return converter.convert_problem(self)

    def copy(self):
        propositions = [proposition.copy() for proposition in self._propositions]
        constants = [constant.copy() for constant in self._constants]
        return Problem(self.name, propositions, constants)
