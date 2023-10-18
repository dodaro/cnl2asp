from cnl2asp.ASP_elements.asp_attribute import ASPAttribute
from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.ASP_elements.asp_atom import ASPAtom
from cnl2asp.ASP_elements.asp_conjunction import ASPConjunction


class ASPRuleHead(ASPElement):
    def __init__(self, choice_element: ASPAtom, condition: ASPConjunction = None):
        self.choice_element = choice_element
        self.condition = condition

    def to_string(self) -> str:
        head = f'{self.choice_element.to_string()}'
        if self.condition:
            head += f': {self.condition.to_string()}'
        return head

    def __eq__(self, other):
        if not isinstance(other, ASPRuleHead):
            return False
        return self.choice_element == other.choice_element and self.condition == other.condition


class ASPRule(ASPElement):
    def __init__(self, body: ASPConjunction = ASPConjunction([]), head: list[ASPRuleHead] = [],
                 cardinality: (int | None, int | None) = None):
        self.head = head
        self.body = body
        self.cardinality = cardinality
        self.remove_duplicates()

    def remove_duplicates(self):
        if self.body:
            to_remove = self.get_duplicates(self.body.get_atom_list(), self.body.get_atom_list())
            for elem in to_remove:
                self.body.remove_element(elem)
        for head in self.head:
            if head.condition and self.body:
                to_remove = self.get_duplicates(head.condition.get_atom_list(), self.body.get_atom_list())
                for elem in to_remove:
                    head.condition.remove_element(elem)

    def get_duplicates(self, default_list: list[ASPAtom], comparison_list: list[ASPAtom]) -> list[ASPAtom]:
        to_remove = []
        for component_1 in default_list:
            for component_2 in comparison_list:
                if (not component_1 is component_2) and not any(component_2 is x for x in to_remove) and component_1 == component_2:
                    to_remove.append(component_1)
                    break
        return to_remove

    def to_string(self) -> str:
        rule = ''
        if self.head:
            for idx, element in enumerate(self.head):
                if idx > 0:
                    rule += '; '
                rule += element.to_string()
            if self.cardinality:
                rule = f'{str(self.cardinality[0]) if self.cardinality[0] else ""} ' \
                       f'{{{rule}}} ' \
                       f'{str(self.cardinality[1]) if self.cardinality[1] else ""}'
            else:
                for head in self.head:
                    if head.condition:
                        rule = f'{{{rule}}}'
        if self.body.conjunction:
            rule += f'{" " if self.head else ""}:- '
            rule += f'{self.body.to_string()}'
        rule += '.\n'
        return rule

    def __eq__(self, other):
        if not isinstance(other, ASPRule):
            return False
        return self.head == other.head and self.body == other.body and self.cardinality == other.cardinality

    def __repr__(self):
        return self.to_string()


class ASPWeakConstraint(ASPRule):
    def __init__(self, body: ASPConjunction, weight: str, level: int, discriminant: list[ASPAttribute]):
        super().__init__(body)
        self.weight = weight
        self.level = level
        self.discriminant = discriminant

    def to_string(self) -> str:
        weak_constraint = super().to_string()
        weak_constraint = weak_constraint.replace(':-', ':~')
        weak_constraint = weak_constraint.replace('\n', ' ')
        weak_constraint += f'[{self.weight}@{self.level}'
        if self.discriminant:
            weak_constraint += f',{",".join([attribute.to_string() for attribute in self.discriminant])}]\n'
        else:
            weak_constraint += ']\n'
        return weak_constraint

    def __repr__(self):
        return self.to_string()

    def __eq__(self, other):
        super().__eq__(other)
        if not isinstance(other, ASPWeakConstraint):
            return False
        return self.weight == other.weight and self.level == other.level and self.discriminant == other.discriminant