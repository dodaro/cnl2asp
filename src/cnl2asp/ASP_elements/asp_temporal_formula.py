from cnl2asp.ASP_elements.asp_element import ASPElement


class ASPTemporalFormula(ASPElement):

    def __init__(self, operations: list[ASPElement]):
        self.operations = operations

    def __str__(self):
        return f'&tel {{{" ".join([str(formula).replace("not", "~") for formula in self.operations])}}}'
