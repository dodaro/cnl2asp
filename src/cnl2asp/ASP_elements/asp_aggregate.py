from cnl2asp.ASP_elements.asp_atom import ASPAtom
from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.ASP_elements.asp_attribute import ASPAttribute
from cnl2asp.ASP_elements.asp_conjunction import ASPConjunction
from cnl2asp.specification.aggregate_component import AggregateOperator


class ASPAggregate(ASPElement):
    symbols = {
        AggregateOperator.SUM: 'sum',
        AggregateOperator.COUNT: 'count',
        AggregateOperator.MAX: 'max',
        AggregateOperator.MIN: 'min'
    }

    def __init__(self, operator: AggregateOperator, discriminant: list[ASPAttribute], body: ASPConjunction):
        self.operator: AggregateOperator = operator
        self.discriminant = discriminant
        self.body = body

    def get_atom_list(self) -> list[ASPElement]:
        return self.body.get_atom_list()

    def remove_element(self, element: ASPElement):
        self.body.remove_element(element)

    def get_discriminant_attributes_value(self):
        attributes = []
        for elem in self.discriminant:
            if isinstance(elem, ASPAttribute):
                attributes.append(elem.get_value())
            elif isinstance(elem, ASPAtom):
                for attribute in elem.attributes:
                    attributes.append(attribute)
        return attributes

    def __str__(self) -> str:
        return f'#{ASPAggregate.symbols[self.operator]}{{' \
               f'{",".join([str(x) for x in self.discriminant])}' \
               f': {str(self.body)}}}'
