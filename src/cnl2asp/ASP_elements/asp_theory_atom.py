from cnl2asp.ASP_elements.asp_element import ASPElement


class TheoryAtom(ASPElement):

    def __init__(self, predicate: str, body: list[ASPElement], negated=False):
        self.predicate = predicate
        self.body = body
        self.negated = negated

    def __str__(self):
        res = "not " if self.negated else ""
        return f'{res}&{self.predicate} {{{" ".join(map(str, self.body))}}}'
