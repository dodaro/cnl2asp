from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.ASP_elements.asp_rule import ASPRule


class ASPProgram(ASPElement):
    def __init__(self, name: str = ''):
        self.name: str = name

        self._rules: list[ASPRule] = []

    def add_rule(self, rule: ASPRule):
        self._rules.append(rule)

    def __str__(self) -> str:
        program = f'\n#program {self.name}.\n' if self.name else ''
        for rule in self._rules:
            program += str(rule)
        return program
