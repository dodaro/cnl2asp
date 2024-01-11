from cnl2asp.ASP_elements.asp_element import ASPElement


class ASPTemporalFormula(ASPElement):

    def __init__(self, operations: list[ASPElement], negated=False):
        self.operations = operations
        self.negated = negated

    def __str__(self):
        res = "not " if self.negated else ""
        return f'{res}&tel {{{" ".join([formula.temporal_formula_string() for formula in self.operations])}}}'
