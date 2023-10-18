from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.ASP_elements.asp_rule import ASPRule
from cnl2asp.proposition.signaturemanager import SignatureManager


class ASPProgram(ASPElement):
    def __init__(self):
        self._constants: list[(str, str)] = []
        self._rules: list[ASPRule] = []

    def is_constant(self, var: str) -> bool:
        for constant in self._constants:
            if constant[0] == var:
                return True
        return False

    def add_constant(self, constant: (str, str)):
        self._constants.append(constant)

    def add_rule(self, rule: ASPRule):
        self._rules.append(rule)

    def to_string(self) -> str:
        program = ''
        for constant in self._constants:
            if constant[1]:
                program += f'#const {constant[0]} = {constant[1]}.\n'
        for rule in self._rules:
            program += rule.to_string()
        return program
