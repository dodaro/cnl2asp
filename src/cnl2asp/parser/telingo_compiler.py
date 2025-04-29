from __future__ import annotations
from lark import v_args
from cnl2asp.parser.asp_compiler import ASPTransformer
from cnl2asp.specification.attribute_component import ValueComponent
from cnl2asp.specification.entity_component import EntityComponent
from cnl2asp.specification.operation_component import Operators, OperationComponent


class TelingoTransformer(ASPTransformer):
    def __init__(self):
        super().__init__()

    def PROBLEM_IDENTIFIER(self, elem):
        if elem == "The following propositions apply in the initial state:":
            self._problem.name = 'initial'
        elif elem == "The following propositions always apply except in the initial state:":
            self._problem.name = 'dynamic'
        elif elem == "The following propositions always apply:":
            self._problem.name = 'always'
        elif elem == "The following propositions apply in the final state:":
            self._problem.name = 'final'

    def whenever_telingo_operation(self, elem):
        self.whenever_clause([None] + elem)

    def telingo_operation(self, elem):
        operand = elem[2]
        if elem[3] and elem[3][0]:
            operand = OperationComponent(Operators.NEGATION, operand)
        if elem[1] and elem[3] and elem[3][1]:
            TELINGO_TEMPORAL_RELATIONSHIP = elem[1].removeprefix('since ')
            TELINGO_TEMPORAL_OPERATOR = elem[3][1].removeprefix('since ')
            operator = f'{TELINGO_TEMPORAL_RELATIONSHIP}_{TELINGO_TEMPORAL_OPERATOR}' if TELINGO_TEMPORAL_OPERATOR == 'before' or TELINGO_TEMPORAL_OPERATOR == 'after' else f'{TELINGO_TEMPORAL_OPERATOR}_{TELINGO_TEMPORAL_RELATIONSHIP}'
            operation = OperationComponent(Operators[operator.upper()], operand)
        elif elem[1]:
            operator = elem[1]
            operation = OperationComponent(Operators[operator.upper()], operand)
        else:
            operation = operand
        TELINGO_DUAL_OPERATOR = elem[4]
        telingo_operation = elem[5]
        if TELINGO_DUAL_OPERATOR:
            operation = OperationComponent(TELINGO_DUAL_OPERATOR, operation, telingo_operation)
        if elem[3] and elem[3][1] == 'since before':
            operation = OperationComponent(Operators.PREVIOUS, operation)
        elif elem[3] and elem[3][1] == 'since after':
            operation = OperationComponent(Operators.NEXT, operation)
        if elem[0]:
            operation.negated = True
        return operation

    def prefixed_telingo_operation(self, elem):
        elem[0], elem[1] = elem[1], elem[0]
        return self.telingo_operation(elem)

    def hold_condition(self, elem):
        if elem[0] == True:
            return True, elem[1]
        else:
            return False, elem[1]

    def telingo_operand(self, elem):
        if not elem[1]:
            return elem[0]
        else:
            return OperationComponent(elem[1], elem[0], elem[2])

    def TELINGO_CONSTANT(self, elem):
        if elem == "it is the initial state":
            return ValueComponent("&initial")
        if elem == "it is the final state":
            return ValueComponent("&final")
        if elem == "the true constant":
            return ValueComponent("&true")
        if elem == "the false constant":
            return ValueComponent("&false")

    def TELINGO_TEMPORAL_RELATIONSHIP(self, elem):
        return elem.value

    def telingo_temporal_operator(self, elem):
        return elem[0]

    def TELINGO_TEMPORAL_OPERATOR(self, elem):
        return elem.value

    def TELINGO_DUAL_OPERATOR(self, elem):
        if elem == "and":
            return Operators.CONJUNCTION
        elif elem == "or":
            return Operators.DISJUNCTION
        elif elem == "implies" or elem == "imply":
            return Operators.LEFT_IMPLICATION
        elif elem == "equivalent to":
            return Operators.EQUIVALENCE
        elif elem == "trigger" or elem == "triggers":
            return Operators.TRIGGER
        elif elem == "since":
            return Operators.SINCE
        elif elem == "precede":
            return Operators.PRECEDE
        elif elem == "release" or elem == "releases":
            return Operators.RELEASE
        elif elem == "until":
            return Operators.UNTIL
        elif elem == "follow":
            return Operators.FOLLOW

    def telingo_there_is(self, elem):
        self._proposition.add_requisite(elem[0])
        return elem[0]

    def entity(self, elem):
        if elem[0] == "previously":
            elem[1].is_before = True
        elif elem[0] == "subsequently":
            elem[1].is_after = True
        elif elem[0] == "initially":
            elem[1].is_initial = True
        elif elem[0] == "finally":
            elem[1].is_final = True
        return elem[1]

    def TELINGO_ENTITY_TEMPORAL_OPERATOR(self, elem):
        return elem.value

    @v_args(meta=True)
    def verb(self, meta, elem: list):
        telingo_temporal_operator = elem[3]
        del elem[3]
        entity = super().verb(meta, elem)
        if telingo_temporal_operator:
            entity = self.entity([telingo_temporal_operator, entity])
        return entity

    def telingo_verb(self, elem):
        verb: EntityComponent = elem[2]
        if elem[1] and elem[3]:
            TELINGO_TEMPORAL_RELATIONSHIP = elem[1].removeprefix('since ')
            TELINGO_TEMPORAL_OPERATOR = elem[3].removeprefix('since ')
            operator = f'{TELINGO_TEMPORAL_RELATIONSHIP}_{TELINGO_TEMPORAL_OPERATOR}' if TELINGO_TEMPORAL_OPERATOR == 'before' or TELINGO_TEMPORAL_OPERATOR == 'after' else f'{TELINGO_TEMPORAL_OPERATOR}_{TELINGO_TEMPORAL_RELATIONSHIP}'
        else:
            operator = elem[1]
        operation = OperationComponent(Operators[operator.upper()], verb)
        if elem[0]:
            operation.negated = True
        return operation
