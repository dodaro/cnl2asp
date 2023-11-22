from cnl2asp.ASP_elements.asp_element import ASPElement


class ASPTemporalFormula(ASPElement):

    def __init__(self, temporal_formulas: list[ASPElement]):
        self.temporal_formulas = temporal_formulas

    def __str__(self):
        return f'&tel {{{" ".join([str(formula) for formula in self.temporal_formulas])}}}'
