from __future__ import annotations

from typing import Any

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.proposition.component import Component
from cnl2asp.proposition.constant_component import ConstantComponent
from cnl2asp.proposition.entity_component import EntityComponent
from cnl2asp.proposition.proposition import Proposition
from cnl2asp.proposition.signaturemanager import SignatureManager


class Problem(Component):
    def __init__(self, propositions: list[Proposition] = None,
                 constants: list[ConstantComponent] = None):
        if propositions is None:
            propositions = []
        if constants is None:
            constants = []
        self._propositions = propositions
        self._constants = constants

    def add_proposition(self, proposition: Proposition):
        self._propositions.append(proposition)

    def add_propositions(self, propositions: list[Proposition]):
        for proposition in propositions:
            if not proposition.is_empty():
                self._propositions.append(proposition)

    def get_propositions(self) -> list[Proposition]:
        return self._propositions

    def add_constant(self, constant: ConstantComponent):
        self._constants.append(constant)

    def get_constant(self) -> list[ConstantComponent]:
        return self._constants

    @staticmethod
    def add_signature(entity: EntityComponent):
        signature = entity.copy()
        signature.label = ''
        SignatureManager.add_signature(signature)

    @staticmethod
    def get_signature(name: str) -> EntityComponent:
        return SignatureManager.get_signature(name)

    def convert(self, converter: Converter) -> Any:
        return converter.convert_problem(self)

    def copy(self):
        propositions = [proposition.copy() for proposition in self._propositions]
        constants = [constant.copy() for constant in self._constants]
        return Problem(propositions, constants)
