from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.ASP_elements.asp_attribute import ASPAttribute
from cnl2asp.ASP_elements.asp_conjunction import ASPConjunction
from cnl2asp.proposition.signaturemanager import SignatureManager
from cnl2asp.proposition.aggregate_component import AggregateOperation


class ASPAggregate(ASPElement):
    symbols = {
        AggregateOperation.SUM: 'sum',
        AggregateOperation.COUNT: 'count',
        AggregateOperation.MAX: 'max',
        AggregateOperation.MIN: 'min'
    }

    def __init__(self, operation: AggregateOperation, discriminant: list[ASPAttribute], body: ASPConjunction):
        self.operation: AggregateOperation = operation
        self.discriminant = discriminant
        self.body = body

    def to_string(self) -> str:
        return f'#{ASPAggregate.symbols[self.operation]}{{' \
               f'{",".join([x.to_string() for x in self.discriminant])}' \
               f': {self.body.to_string()}}}'
