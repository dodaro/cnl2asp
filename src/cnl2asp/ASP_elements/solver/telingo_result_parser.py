import clingo

from cnl2asp.ASP_elements.solver.clingo_result_parser import ClingoResultParser


class TelingoResultParser(ClingoResultParser):
    def parse_model(self):
        self._get_new_knowledge()
        model = ''
        for state in str(self.model).split("State"):
            if not state.strip():
                continue
            state = state.splitlines()
            model += f"In the {state[0].strip().removesuffix(':')} state:\n"
            for line in state[1:]:
                for elem in line.split(" "):
                    if elem:
                        elem = clingo.parse_term(elem.strip())
                        if elem.name in self.target_predicates:
                            model += self._clingo_symbol_to_sentence(elem) + '\n'
        return model
