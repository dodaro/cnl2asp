import lark
from lark import Transformer
from dataclasses import dataclass

negation_of_comparison_ops = {'more than': 'at most', 'less than': 'at least', 'different from': 'equal to',
                              'equal to': 'different from', 'at least': 'less than', 'at most': 'more than'}

negation_of_ordering_ops = {'before': 'after', 'after': 'before'}


class CNLTransformer(Transformer):
    def start(self, elem):
        return CNLContentTree(elem)

    def negative_strong_constraint_clause(self, elem):
        simple_clauses = [x for x in elem if type(x) == SimpleClause]
        aggregate_clause = [x for x in elem if type(x) == AggregateClause]
        comparison_clause = [x for x in elem if type(x) == ComparisonClause]
        where_clause = [x for x in elem if type(x) == WhereClause]
        quantified_constraint = [x for x in elem if type(x) == QuantifiedConstraint]

        simple_clauses += [quantified_constraint[0].body] if quantified_constraint else []
        clauses = simple_clauses if simple_clauses else aggregate_clause[0]
        comparison_clause = comparison_clause[0] if comparison_clause else []
        where_clause = where_clause[0] if where_clause else []

        return StrongConstraintClause(clauses, comparison_clause, where_clause)

    def positive_strong_constraint(self, elem):
        aggregate_clause = [x for x in elem if type(x) == AggregateClause]
        when_then_clause = [x for x in elem if type(x) == WhenThenClause]
        comparison_clause = [x for x in elem if type(x) == ComparisonClause]
        where_clause = [x for x in elem if type(x) == WhereClause]
        quantified_constraint = [x for x in elem if type(x) == QuantifiedConstraint]

        clauses = []
        comparison_clause = comparison_clause[0] if comparison_clause else []
        where_clause = where_clause[0] if where_clause else []
        if aggregate_clause:
            comparison_clause.condition_operator = negation_of_comparison_ops[comparison_clause.condition_operator]
            clauses = aggregate_clause[0]
        elif quantified_constraint:
            clause = quantified_constraint[0].body
            clause.verb_clause.verb_negated = True
            clauses += [clause]
        else:
            for clause in when_then_clause[0].clause_body[1]:
                clause.verb_clause.verb_negated = not clause.verb_clause.verb_negated
            clauses = when_then_clause[0].clause_body[0] + when_then_clause[0].clause_body[1]

        return StrongConstraintClause(clauses, comparison_clause, where_clause)

    def weak_constraint(self, elem):
        where_clause = [x for x in elem if type(x) == WhereClause]
        where_clause = where_clause[0] if where_clause else []

        return WeakConstraintClause(elem[1], elem[2], elem[3], where_clause)

    def definition_clause(self, elem):
        return DefinitionClause(elem[0])

    def constant_definition_clause(self, elem):
        return ConstantDefinitionClause(elem[0], elem[1])

    def quantified_choice_clause(self, elem):
        foreach_clause = [x for x in elem if type(x) == ForeachClause]
        quantified_range_clause = [x for x in elem if type(x) == QuantifiedRangeClause]
        quantified_object_clause = [x for x in elem if type(x) == QuantifiedObjectClause]
        foreach_clause = foreach_clause[0] if foreach_clause else []

        quantified_range_clause = quantified_range_clause[0] if quantified_range_clause else []
        quantified_object_clause = quantified_object_clause[0] if quantified_object_clause else []

        if type(elem[2]) is not lark.Token:
            return QuantifiedChoiceClause(elem[0], elem[1], elem[2], quantified_range_clause, quantified_object_clause,
                                          foreach_clause)
        else:
            return QuantifiedChoiceClause(elem[0], elem[1], elem[3], quantified_range_clause, quantified_object_clause,
                                          foreach_clause)

    def property_clause(self, elem):
        return PropertyClause(elem[0], elem[1])

    def ordering_definition(self, elem):
        return OrderingDefinition(elem[1])

    def ordering_clause(self, elem):
        return OrderingClause(elem[0], elem[1], elem[2])

    def ordering_element(self, elem):
        return OrderingElement(elem[0], elem[1])

    def condition_ordering_clause(self, elem):
        return ConditionOrderingClause(elem[0], elem[1], elem[2], elem[3])

    def condition_comparison_clause(self, elem):
        return ConditionComparisonClause(elem[0], elem[1]) if elem[0] != 'not' else ConditionComparisonClause(
            negation_of_comparison_ops[elem[1]], elem[2])

    def object_windowed_range(self, elem):
        return ObjectWindowedRange(elem[0], elem[1])

    def object_binary_range(self, elem):
        return ObjectBinaryRange(elem[0], elem[1])

    def isa_clause(self, elem):
        return IsAClause(elem[1], elem[0], elem[2:])

    def isa_with_clause(self, elem):
        return WithClause(elem[0], elem[1])

    def compounded_clause(self, elem):
        return CompoundedClause(elem[0], elem[1], elem[2:])

    def simple_clause(self, elem):
        if type(elem[1]) is not lark.Token:
            return SimpleClause(elem[0], elem[1], True)
        else:
            return SimpleClause(elem[0], elem[2], True)

    def comparison_clause(self, elem):
        return ComparisonClause(elem[0], elem[1])

    def subject_clause(self, elem):
        subject = []
        variable = []
        ordering = []
        if len(elem) == 1:
            subject = elem[0]
        if len(elem) == 2:
            if type(elem[0]) == SubjectOrderingClause:
                subject = elem[1]
                ordering = elem[0]
            else:
                subject = elem[0]
                variable = elem[1]
        return SubjectClause(subject, variable, ordering)

    def verb_clause(self, elem):
        verb_name = elem[0] if 'not' not in elem[0] else elem[1]
        negated = True if 'not' in elem[0] else False
        verb_object_clause = [x for x in elem if type(x) == VerbObjectClause]
        composition_clause = [x for x in elem if type(x) == CompositionClause]
        tuple_clause = [x for x in elem if type(x) == TupleClause]
        object_clause = verb_object_clause + composition_clause + tuple_clause
        object_clause = object_clause[0] if object_clause else []
        return VerbClause(verb_name, object_clause, negated)

    def object_clause(self, elem):
        return ObjectClause(elem[0], []) if len(elem) == 1 else ObjectClause(elem[0], elem[1])

    def compounded_clause_match_tail(self, elem):
        return CompoundedClauseMatchTail(elem[0], elem[1])

    def object_range(self, elem):
        return ObjectRange(elem[0], elem[1])

    def compounded_list(self, elem):
        return elem

    def compounded_clause_range(self, elem):
        return CompoundedClauseRange(elem[0], elem[1])

    def compounded_clause_match(self, elem):
        (elem,) = elem
        return CompoundedClauseMatch(elem)

    def property_definition(self, elem):
        (elem,) = elem
        return PropertyDefinition(elem)

    def definition_object(self, elem):
        (elem,) = elem
        return str(elem)

    def definition_subject(self, elem):
        (elem,) = elem
        return str(elem)

    def ordering_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def subject_name(self, elem):
        (elem,) = elem
        return str(elem)

    def verb_name(self, elem):
        return str(elem[0])

    def verb_name_with_preposition(self, elem):
        return str(elem[0]) + " " + str(elem[1])

    def object_name(self, elem):
        (elem,) = elem
        return str(elem)

    def condition_expression(self, elem):
        return elem

    def condition_expression_value(self, elem):
        (elem,) = elem
        return elem

    def condition_operation(self, elem):
        return ConditionOperation(elem[1], elem[0], elem[2])

    def range_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def where_clause(self, elem):
        return WhereClause(elem)

    def condition_clause(self, elem):
        return ConditionClause(elem[0], elem[2])

    def condition_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def aggregate_clause(self, elem):
        ranging_clause = [x for x in elem if type(x) == RangingClause]
        ranging_clause = ranging_clause[0] if ranging_clause else []
        return AggregateClause(elem[0], elem[1], ranging_clause)

    def aggregate_active_clause(self, elem):
        subject_clause = [x for x in elem if type(x) == SubjectClause][0]
        verb_clause = [x for x in elem if type(x) == AggregateVerbClause][0]
        object_clause = [x for x in elem if type(x) == VerbObjectClause or type(x) == CompositionClause or
                         type(x) == TupleClause]
        for_clause = [x for x in elem if type(x) == list]

        for_clause = for_clause[0] if for_clause else []
        object_clause = object_clause[0] if object_clause else []

        return AggregateBodyClause(subject_clause, verb_clause, object_clause, for_clause, True)

    def aggregate_passive_clause(self, elem):
        subject_clause = [x for x in elem if type(x) == SubjectClause][0]
        verb_clause = [x for x in elem if type(x) == AggregateVerbClause][0]
        object_clause = [x for x in elem if type(x) == VerbObjectClause or type(x) == CompositionClause or
                         type(x) == TupleClause][0]
        for_clause = [x for x in elem if type(x) == list]

        for_clause = for_clause[0] if for_clause else []

        return AggregateBodyClause(subject_clause, verb_clause, object_clause, for_clause, False)

    def quantified_exact_quantity_clause(self, elem):
        return QuantifiedRangeClause('between', elem[1], elem[1])

    def quantified_range_clause(self, elem):
        return QuantifiedRangeClause(elem[0], elem[1], elem[2])

    def quantified_object_clause(self, elem):
        return QuantifiedObjectClause(elem)

    def foreach_clause(self, elem):
        return ForeachClause(elem)

    def simple_object(self, elem):
        return SimpleObject(elem[0], elem[1])

    def quantifier(self, elem):
        (elem,) = elem
        return str(elem)

    def quantified_exact_quantity(self, elem):
        (elem,) = elem
        return str(elem)

    def exact_quantity_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def variable(self, elem):
        (elem,) = elem
        return str(elem)

    def constant(self, elem):
        (elem,) = elem
        return str(elem)

    def number(self, elem):
        (elem,) = elem
        return str(elem)

    def verb_negation(self, elem):
        (elem,) = elem
        return str(elem)

    def aggregate_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def range_lhs(self, elem):
        (elem,) = elem
        return str(elem)

    def range_rhs(self, elem):
        (elem,) = elem
        return str(elem)

    def aggregate_variables(self, elem):
        return elem

    def passive_verb_negation(self, elem):
        (elem,) = elem
        return str(elem)

    def comparison_value(self, elem):
        (elem,) = elem
        return elem

    def end_of_line(self, elem):
        return '.'

    def question_mark(self, elem):
        (elem,) = elem
        return str(elem)

    def compounded_clause_granularity(self, elem):
        return CompoundedClauseGranularity(elem)

    def subject_ordering_clause(self, elem):
        return SubjectOrderingClause(elem[0], []) if len(elem) == 1 else SubjectOrderingClause(elem[0], elem[1])

    def consecution_clause(self, elem):
        return ConsecutionClause(elem[0], elem[1])

    def aggregate_object_clause(self, elem):
        return elem[0]

    def verb_object_clause(self, elem):
        name = elem[0]
        rest = elem[1:]
        variable = [x for x in rest if type(x) == str]
        ob_range = [x for x in rest if type(x) == ObjectRange]
        ordering = [x for x in rest if type(x) == VerbObjectOrderingClause]
        consecution = [x for x in rest if type(x) == VerbObjectConsecutionClause]

        variable = variable[0] if variable else []
        ob_range = ob_range[0] if ob_range else []
        ordering = ordering[0] if ordering else []
        consecution = consecution[0] if consecution else []

        return VerbObjectClause(name, variable, ob_range, ordering, consecution)

    def verb_object_ordering_clause(self, elem):
        return VerbObjectOrderingClause(elem[0], elem[1])

    def verb_object_consecution_clause(self, elem):
        return VerbObjectConsecutionClause(elem[0], elem[1], elem[2])

    def composition_clause(self, elem):
        return CompositionClause(elem[0], elem[1])

    def tuple_clause(self, elem):
        return TupleClause([x for x in elem if type(x) != lark.visitors.Discard])

    def tuple_operator(self, elem):
        return lark.Discard

    def composition_operator(self, elem):
        return lark.Discard

    def shift_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def consecution_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def condition_match_clause(self, elem):
        return ConditionMatchClause(elem[0], elem[2], len(elem[2]))

    def aggregate_verb_clause(self, elem):
        if 'not' in elem[0]:
            return AggregateVerbClause(elem[1], True) if len(elem) == 2 else AggregateVerbClause(elem[2], True)
        else:
            return AggregateVerbClause(elem[0], False) if len(elem) == 1 else AggregateVerbClause(elem[1], False)

    def aggregate_determinant(self, elem):
        (elem,) = elem
        return str(elem)

    def aggregate_for_clause(self, elem):
        return [AggregateForClause(elem[i][0], elem[i][1]) for i, x in enumerate(elem)]

    def aggregate_determinant_clause(self, elem):
        return [elem[1], elem[0]]

    def condition_match_group(self, elem):
        return ConditionMatchGroup(elem)

    def condition_bound_clause(self, elem):
        return ConditionBoundClause(elem[0], elem[1])

    def when_then_clause(self, elem):
        when_part = [x.body for x in elem if type(x) is WhenPart]
        then_part = [x for x in elem if type(x) is not WhenPart]
        return WhenThenClause(when_part + then_part)

    def when_part(self, elem):
        return WhenPart(elem)

    def then_part(self, elem):
        return elem

    def weak_priority_clause(self, elem):
        (elem,) = elem
        return str(elem)

    def weak_optimization_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def condition_expression_operator(self, elem):
        return ConditionExpressionOperator(str(elem[0]), True) if len(elem) == 2 else ConditionExpressionOperator(
            str(elem[0]), False)

    def absolute_value_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def enumerative_definition_clause(self, elem):
        objects_list = [x for x in elem[3:] if type(x) is SubjectClause]
        where_clause = [x for x in elem[3:] if type(x) is WhereClause]
        when_part = [x for x in elem[3:] if type(x) is WhenPart]

        where_clause = where_clause[0] if where_clause else []
        when_part = when_part[0].body if when_part else []
        return EnumerativeDefinitionClause(elem[0], elem[2], objects_list, when_part, where_clause)

    def ranging_clause(self, elem):
        return RangingClause(elem[0], elem[1])

    def quantified_constraint(self, elem):
        return QuantifiedConstraint(elem[0], elem[1])

    def CNL_END_OF_LINE(self, elem):
        return lark.Discard


@dataclass(frozen=True)
class RangingClause:
    ranging_lhs: str
    ranging_rhs: str


@dataclass(frozen=True)
class WhenPart:
    body: list


@dataclass(frozen=True)
class ConditionExpressionOperator:
    operator: str
    absolute_value: bool


@dataclass(frozen=True)
class ConditionBoundClause:
    bound_lower: str
    bound_upper: str


@dataclass(frozen=True)
class ConditionMatchClause:
    condition_variable: str
    condition_list: list[str]
    list_len: int


@dataclass(frozen=True)
class ConditionMatchGroup:
    group_list: list[ConditionMatchClause]


@dataclass(frozen=True)
class ObjectWindowedRange:
    window_value: str
    object_type: str


@dataclass(frozen=True)
class ObjectBinaryRange:
    range_lhs: str
    range_rhs: str


@dataclass(frozen=True)
class ObjectRange:
    range_operator: str
    range_expression: ObjectWindowedRange | ObjectBinaryRange


@dataclass(frozen=True)
class VerbObjectOrderingClause:
    verb_ordering_operator: str
    verb_ordering_variable: str


@dataclass(frozen=True)
class VerbObjectConsecutionClause:
    verb_consecution_count: str
    verb_consecution_operator: str
    verb_consecution_object_name: str


@dataclass(frozen=True)
class VerbObjectClause:
    verb_object_name: str
    verb_object_variable: str
    verb_object_range: ObjectRange
    verb_object_ordering: VerbObjectOrderingClause
    verb_object_consecution: VerbObjectConsecutionClause


@dataclass(frozen=True)
class TupleClause:
    tuple_objects: list[VerbObjectClause]


@dataclass(frozen=True)
class CompositionClause:
    composition_lhs: VerbObjectClause
    composition_rhs: VerbObjectClause


@dataclass(frozen=True)
class CompoundedClauseGranularity:
    granularity_hierarchy: list[str]


@dataclass(frozen=True)
class ConsecutionClause:
    consecution_count: str
    consecution_operator: str


@dataclass(frozen=True)
class SubjectOrderingClause:
    ordering_operator: str
    consecution_clause: ConsecutionClause


@dataclass(frozen=True)
class SubjectClause:
    subject_name: str
    subject_variable: str
    subject_ordering: SubjectOrderingClause


@dataclass(frozen=True)
class IfSameClause:
    object: SubjectClause


@dataclass(frozen=True)
class ObjectClause:
    object_name: str
    object_variable: str


@dataclass(frozen=True)
class AggregateForClause:
    for_object: ObjectClause
    clause_determinant: str


@dataclass
class VerbClause:
    verb_name: str
    object_clause: [ObjectClause]
    verb_negated: bool


@dataclass(frozen=True)
class IfClauseBody:
    clause_body: VerbClause | IfSameClause


@dataclass(frozen=True)
class IfClause:
    subjects: list[SubjectClause]
    clauses: list[IfClauseBody]


@dataclass(frozen=True)
class AggregateVerbClause:
    verb_name: str
    verb_negated: bool


@dataclass
class SimpleClause:
    subject: SubjectClause
    verb_clause: VerbClause
    active_form: bool


@dataclass(frozen=True)
class QuantifiedConstraint:
    quantifier: str
    body: SimpleClause


@dataclass(frozen=True)
class WhenThenClause:
    clause_body: list[SimpleClause]


@dataclass(frozen=True)
class ConditionOrderingClause:
    count_value: str
    object_type: str
    ordering_operator: str
    ordering_object: str



@dataclass(frozen=True)
class SimpleObject:
    object_name: str
    object_variable: str


@dataclass(frozen=True)
class ForeachClause:
    objects: [SimpleObject]


@dataclass(frozen=True)
class AggregateBodyClause:
    aggregate_subject_clause: SubjectClause
    aggregate_verb_clause: AggregateVerbClause
    aggregate_object_clause: VerbObjectClause | CompositionClause | TupleClause
    aggregate_for_clauses: list[AggregateForClause]
    active_form: bool


@dataclass(frozen=True)
class AggregateClause:
    aggregate_operator: str
    aggregate_body: AggregateBodyClause
    ranging_clause: RangingClause


@dataclass(frozen=True)
class ConditionOperation:
    expression_lhs: str | AggregateClause
    expression_operator: ConditionExpressionOperator
    expression_rhs: str | AggregateClause


@dataclass(frozen=True)
class ConditionComparisonClause:
    condition_operator: str
    condition_expression: ConditionOperation


@dataclass(frozen=True)
class ConditionClause:
    condition_variable: str
    condition_clause: ConditionComparisonClause | ConditionOrderingClause


@dataclass(frozen=True)
class WhereClause:
    conditions: [ConditionClause]


@dataclass(frozen=True)
class EnumerativeDefinitionClause:
    subject: SubjectClause
    verb_name: str
    object_list: list[SubjectClause]
    when_part: list
    where_clause: WhereClause


@dataclass(frozen=True)
class WeakConstraintClause:
    priority_level: str
    constraint_body: ConditionOperation | AggregateClause
    optimization_operator: str
    where_clause: WhereClause


@dataclass(frozen=True)
class WithClause:
    subject: str
    definition: str


@dataclass(frozen=True)
class IsAClause:
    subject: str
    definition: str
    with_clause: WithClause


@dataclass(frozen=True)
class CompoundedClauseRange:
    compounded_range_lhs: str
    compounded_range_rhs: str


@dataclass(frozen=True)
class CompoundedClauseMatch:
    compounded_match_list: list[str]


@dataclass(frozen=True)
class CompoundedClauseMatchTail:
    subject: str
    definition_list: list[str]


@dataclass(frozen=True)
class CompoundedClause:
    subject: str
    definition: CompoundedClauseMatch | CompoundedClauseRange
    tail: list[CompoundedClauseMatchTail | CompoundedClauseGranularity]


@dataclass(frozen=True)
class ConstantDefinitionClause:
    subject: str
    constant: str


@dataclass(frozen=True)
class DefinitionClause:
    clause: CompoundedClause | ConstantDefinitionClause | EnumerativeDefinitionClause


@dataclass(frozen=True)
class PropertyClause:
    property_subject: str
    property_definition: str


@dataclass(frozen=True)
class OrderingDefinition:
    ordering_list: list[str]


@dataclass(frozen=True)
class OrderingElement:
    element_type: str
    element: str


@dataclass(frozen=True)
class OrderingClause:
    ordering_subject: OrderingElement
    ordering_operator: str
    ordering_object: OrderingElement


@dataclass(frozen=True)
class PropertyDefinition:
    definition: OrderingDefinition


@dataclass
class ComparisonClause:
    condition_operator: str
    comparison_value: str


@dataclass(frozen=True)
class StrongConstraintClause:
    clauses: list[SimpleClause] | AggregateClause
    comparison_clause: ComparisonClause
    where_clause: WhereClause


@dataclass(frozen=True)
class QuantifiedExactQuantity:
    quantity: str


@dataclass(frozen=True)
class QuantifiedRangeClause:
    quantified_range_operator: str
    quantified_range_lhs: str
    quantified_range_rhs: str


@dataclass(frozen=True)
class QuantifiedObjectClause:
    objects: [SimpleObject]


@dataclass(frozen=True)
class QuantifiedChoiceClause:
    quantifier: str
    subject_clause: SubjectClause
    verb_name: str
    range: QuantifiedExactQuantity | QuantifiedRangeClause
    object_clause: QuantifiedObjectClause
    foreach_clause: ForeachClause


@dataclass(frozen=True)
class CNLContentTree:
    sentences: [StrongConstraintClause | DefinitionClause | QuantifiedChoiceClause | PropertyClause | OrderingClause]
