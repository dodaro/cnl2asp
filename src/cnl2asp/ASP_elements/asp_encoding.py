from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.ASP_elements.asp_program import ASPProgram


class ASPEncoding(ASPElement):
    def __init__(self):
        self._programs: list[ASPProgram] = []
        self._constants: list[(str, str)] = []
        self._telingo_constants: list[str] = ["&true", "&initial", "&false", "&final"]

    def add_constant(self, constant: (str, str)):
        self._constants.append(constant)

    def is_constant(self, var: str) -> bool:
        if var in self._telingo_constants:
            return True
        for constant in self._constants:
            if constant[0] == var:
                return True
        return False

    def add_program(self, program: ASPProgram):
        self._programs.append(program)

    def __str__(self):
        string = ''
        for constant in self._constants:
            if constant[1]:
                string += f'#const {constant[0]} = {constant[1]}.\n'
        for program in self._programs:
            string += str(program)
        return string.strip() + '\n'
