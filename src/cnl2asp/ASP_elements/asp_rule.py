from cnl2asp.ASP_elements.asp_aggregate import ASPAggregate
from cnl2asp.ASP_elements.asp_attribute import ASPAttribute
from cnl2asp.ASP_elements.asp_element import ASPElement
from cnl2asp.ASP_elements.asp_atom import ASPAtom
from cnl2asp.ASP_elements.asp_conjunction import ASPConjunction


class ASPRuleHead(ASPElement):
    def __init__(self, choice_element: ASPAtom, condition: ASPConjunction = None):
        if condition is None:
            condition = ASPConjunction([])
        self.choice_element = choice_element
        self.condition = condition

    def __str__(self) -> str:
        head = f'{str(self.choice_element)}'
        condition = str(self.condition)
        if condition:
            head += f': {condition}'
        return head

    def __eq__(self, other):
        if not isinstance(other, ASPRuleHead):
            return False
        return self.choice_element == other.choice_element and self.condition == other.condition


class ASPRule(ASPElement):
    def __init__(self, body: ASPConjunction = ASPConjunction([]), head=None,
                 cardinality: (int | None, int | None) = None):
        if head is None:
            head = []
        self.head = head
        self.body = body
        self.cardinality = cardinality
        self._clear_rule()

    def _clear_rule(self):
        self._remove_duplicates()

    def _remove_duplicates(self):
        if self.body:
            to_remove = self._get_duplicates(self.body.conjunction, self.body.conjunction)
            for elem in to_remove:
                self.body.remove_element(elem)
        for head in self.head:
            if head.condition and self.body:
                to_remove = self._get_duplicates(head.condition.get_atom_list(), self.body.get_atom_list())
                for elem in to_remove:
                    head.condition.remove_element(elem)

    def _get_duplicates(self, default_list: list[ASPAtom], comparison_list: list[ASPAtom]) -> list[ASPAtom]:
        to_remove = []
        for component_1 in default_list:
            for component_2 in comparison_list:
                if (not component_1 is component_2) and not any(component_2 is x for x in to_remove) and component_1 == component_2:
                    to_remove.append(component_1)
                    break
        return to_remove

    def _is_choice_rule(self):
        if self.cardinality:
            return True
        return False

    def __str__(self) -> str:
        rule = ''
        separator = ' | '
        if self._is_choice_rule():
            separator = " ; "
        if self.head:
            for idx, element in enumerate(self.head):
                if idx > 0:
                    rule += separator
                rule += str(element)
            if self.cardinality:
                rule = f'{str(self.cardinality[0]) + " <= " if self.cardinality[0] else ""}' \
                       f'{{{rule}}}' \
                       f'{" <= " + str(self.cardinality[1]) if self.cardinality[1] else ""}'
        rule = rule.strip()
        if self.body.conjunction:
            body = str(self.body)
            if self.head:
                rule += f' '
                for elem in body.split(','):
                    if elem.strip().startswith('&tel'):
                        body = body.replace(elem, f'not not {elem.strip()}')
            rule += f':- {body}'
        rule += '.\n'
        return rule

    def __eq__(self, other):
        if not isinstance(other, ASPRule):
            return False
        return self.head == other.head and self.body == other.body and self.cardinality == other.cardinality

    def __repr__(self):
        return str(self)


class ASPWeakConstraint(ASPRule):
    def __init__(self, body: ASPConjunction, weight: str, level: int, discriminant: list[ASPAttribute]):
        super().__init__(body)
        self.weight = weight
        self.level = level
        self.discriminant = discriminant

    def __str__(self) -> str:
        weak_constraint = super().__str__()
        weak_constraint = weak_constraint.replace(':-', ':~')
        weak_constraint = weak_constraint.replace('\n', ' ')
        weak_constraint += f'[{self.weight}@{self.level}'
        if self.discriminant:
            added = set()
            attributes = []
            for attribute in self.discriminant:
                str_attr = str(attribute)
                if str_attr not in added:
                    attributes.append(str_attr)
                    added.add(str_attr)
            weak_constraint += f',{",".join(attributes)}]\n'
        else:
            weak_constraint += ']\n'
        return weak_constraint

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        super().__eq__(other)
        if not isinstance(other, ASPWeakConstraint):
            return False
        return self.weight == other.weight and self.level == other.level and self.discriminant == other.discriminant
