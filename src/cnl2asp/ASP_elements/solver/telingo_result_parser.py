from functools import cmp_to_key

import clingo
from clingo import SolveHandle

from cnl2asp.ASP_elements.solver.clingo_result_parser import ClingoResultParser
from cnl2asp.specification.specification import SpecificationComponent


class TelingoResultParser(ClingoResultParser):

    def __init__(self, specification: SpecificationComponent):
        super().__init__(specification)
        self._old_states = []

    def compare(self, item1: str, item2: str):
        if item1 in self._old_states and item2 not in self._old_states:
            return -1
        if item2 in self._old_states and item1 not in self._old_states:
            return 1
        if item1.startswith('There is'):
            return -1
        if item2.startswith('There is'):
            return 1
        return item1 < item2

    def parse_model(self, model: str):
        self._get_new_knowledge()
        res = ''
        for state in model.split("State"):
            if not state.strip():
                continue
            state = state.splitlines()
            res += f"-- In the {state[0].strip().removesuffix(':')} state:\n"
            atoms = []
            for line in state[1:]:
                for elem in line.split(" "):
                    if elem:
                        elem = clingo.parse_term(elem.strip())
                        if elem.name in self.target_predicates:
                            atoms.append(self._clingo_symbol_to_sentence(elem))
            atoms.sort(key=cmp_to_key(self.compare))
            res += '\n'.join(atoms) + '\n'
            self._old_states += atoms
        return res
