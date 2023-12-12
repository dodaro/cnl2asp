from __future__ import annotations
from typing import Any

from cnl2asp.converter.converter_interface import Converter
from cnl2asp.specification.component import Component
from cnl2asp.specification.constant_component import ConstantComponent
from cnl2asp.specification.problem import Problem


class SpecificationComponent(Component):
    def __init__(self, problems: list[Problem] = None, constants: list[ConstantComponent] = None):
        if problems is None:
            problems = []
        if constants is None:
            constants = []
        self._problems: list[Problem] = problems
        self._constants = constants

    def add_constant(self, constant: ConstantComponent):
        self._constants.append(constant)

    def get_constants(self) -> list[ConstantComponent]:
        return self._constants


    def get_problems(self) -> list[Problem]:
        return self._problems

    def add_problem(self, problem: Problem):
        self._problems.append(problem)

    def convert(self, converter: Converter) -> Any:
        return converter.convert_specification(self)

    def copy(self) -> SpecificationComponent:
        problems = []
        for problem in self._problems:
            problems.append(problem.copy())
        return SpecificationComponent(problems)
