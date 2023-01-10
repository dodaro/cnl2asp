from ast import Param
from statistics import variance
import lark
from lark import Transformer
from dataclasses import dataclass

negation_of_comparison_ops = {'more than': 'at most', 'less than': 'at least', 'different from': 'equal to',
                              'equal to': 'different from', 'at least': 'less than', 'at most': 'more than'}

negation_of_ordering_ops = {'before': 'after', 'after': 'before'}


class CNLTransformer(Transformer):
    def start(self, elem):
        return CNLContentTree(elem)

    def atom_key(self, elem):
        return PrimaryKey([x for x in elem])

    def domain_definition(self, elem):
        subject = None
        primary_key = []
        parameters = []
        for x in elem:
            if type(x) == SubjectClause:
                subject = x
            elif type(x) == PrimaryKey:
                primary_key = x.parameters
            elif type(x) == Parameter:
                parameters.append(x)
        if subject.subject_variable:
            subject.subject_name = f'{subject.subject_name} {subject.subject_variable}'
            subject.subject_variable = ''
        return DomainDefinition(subject, primary_key, parameters)

    def fact_definition(self, elem):
        subject = elem[0]
        return FactDefinition(subject)

    def constant_definition(self, elem):
        subject = elem[0]
        value = elem[1]
        return ConstantDefinition(subject, value)
    def whenever_then_clause(self, elem):
        whever_clause = []
        then_clause = ''
        duration_clause = ''
        for clause in elem:
            if type(clause) == WheneverClause:
                whever_clause.append(clause)
            elif type(clause) == ThenClause:
                then_clause = clause

        return WheneverThenClause(whever_clause, then_clause)
    
    def temporal_concept_definition(self,elem):
        a = elem[1].value
        if len(elem) == 5:
            return TemporalConceptClause(elem[0], elem[1].value, elem[2], elem[3], int(elem[4].value))
        return TemporalConceptClause(elem[0], elem[1].value, elem[2], elem[3], 1)

    def temporal_range_start(self,elem):
        # simple number
        if len(elem) == 1:
            return elem[0].value
        # date
        if elem[2].isnumeric():
            return f'{elem[0].value}/{elem[1].value}/{elem[2].value}'
        # time
        return f'{elem[0].value}:{elem[1].value} {elem[2].value}'

    def temporal_range_end(self,elem):
        # simple number
        if len(elem) == 1:
            return elem[0].value
        # date
        if elem[2].isnumeric():
            return f'{elem[0].value}/{elem[1].value}/{elem[2].value}'
        # time
        return f'{elem[0].value}:{elem[1].value} {elem[2].value}'

    def whenever_clause(self, elem):
        subject_clause = ''
        temporal_constraint = ''
        verb_negation = False
        for clause in elem:
            if clause == 'not':
                verb_negation = True
            if type(clause) == list and len(clause) > 1:
                subject_clause = clause[0]
                temporal_constraint = clause[1]
            if type(clause) == SubjectClause:
                subject_clause = clause
        return WheneverClause(subject_clause, temporal_constraint, verb_negation)

    def then_clause(self, elem):
        subject = [x for x in elem if type(x) == SubjectClause][0]
        assignment_verb = elem[1]
        cardinality = [x for x in elem if type(x) == Cardinality]
        cardinality = cardinality[0] if len(cardinality) else None
        # quantified_range_clause = [x for x in elem if type(x) == QuantifiedRangeClause]
        # quantified_range_clause = quantified_range_clause[0] if quantified_range_clause else []
        verb_name = [x for x in elem if type(x) == VerbName][0]
        for i, x in enumerate(elem):
            if type(x) == VerbName and type(elem[i - 1]) == lark.Token and \
                    elem[i - 1].value in ["have ", "have a ","have an ", "has ","has a ","has an "]:
                verb_name = VerbName(x.name, '', x.parameters, x.ordering) if x.preposition == 'to' else x
        verb_name = VerbName(f'{verb_name.name} {verb_name.preposition}'.strip(), verb_name.preposition, verb_name.parameters, verb_name.ordering)
        object_clause = [x for x in elem if type(x) == ObjectClause]
        duration_clause = [x for x in elem if type(x) == DurationClause]
        duration_clause = duration_clause[0] if duration_clause else []
        return ThenClause(elem[0], assignment_verb, verb_name, object_clause,
                      cardinality, duration_clause)

    def parameter_list(self, elem):
        parameters = [x for idx, x in enumerate(elem) if
                      type(x) == Parameter and ((idx + 1 >= len(elem)) or type(elem[idx + 1]) == Parameter)]
        parameters_definition = [ParameterDefinition(x.name, elem[idx + 1]) for idx, x in enumerate(elem) if
                                 not (idx + 1 >= len(elem)) and type(x) == Parameter and type(elem[idx + 1]) == str]
        temporal_ordering = [x for x in elem if type(x) == TemporalOrdering]
        comparison_clause = []
        for idx, x in enumerate(elem):
            if not (idx + 1 >= len(elem)) and type(x) == Parameter and type(elem[idx + 1]) == ComparisonClause:
                if len(elem[idx + 1].comparison_value) == 2:
                    comparison_clause += [ConditionOperation(x, elem[idx + 1].condition_operator,
                                                        ParameterDefinition(elem[idx + 1].comparison_value[1].name,
                                                                            elem[idx + 1].comparison_value[0]), '')]
                else:
                    comparison_clause += [ConditionOperation(x, elem[idx + 1].condition_operator, elem[idx + 1].comparison_value[0], '')]

        return parameters + parameters_definition + comparison_clause + temporal_ordering

    def parameter_definition(self, elem):
        if len(elem) == 1:
            return str(elem[0])
        elif len(elem) == 3:
            return ComparisonClause(elem[0].value, [elem[1], elem[2]])
        else:
            return ComparisonClause(elem[0].value, [elem[1]])

    def temporal_constraint(self, elem):
        return TemporalConstraint(elem[0], elem[1], elem[2])

    def value(self, elem):
        (elem,) = elem
        return str(elem)

    def parameter(self, elem):
        if type(elem[0]) == TemporalOrdering: return elem[0]
        if(elem[0].value == 'and'):
            elem.remove(elem[0])
        if(elem[0].value == 'a' or elem[0].value == 'an'):
            elem.remove(elem[0])
        parameter_name = '_'.join([x.value for x in elem if type(x) == lark.Token])
        variable = elem[len(elem) - 1] if not type(elem[len(elem) - 1]) == lark.Token else ''
        return Parameter(parameter_name, variable)

    def temporal_ordering_with_respect_specified(self,elem):
        return TemporalOrdering(elem[0], elem[1], elem[2])

    def negative_strong_constraint_clause(self, elem):
        if ([x for x in elem if type(x) == WheneverClause]):
            aggregate_clause = [x for x in elem if type(x) == AggregateClause]
            simple_clause = [x for x in elem if type(x) == SimpleClause]
            condition_clause = [x for x in elem if type(x) == ConditionClause]
            whenever_clause = [x for x in elem if type(x) == WheneverClause]
            comparison_clause = [x for x in elem if type(x) == ComparisonClause]
            temporal_clause = [x for x in elem if type(x) == TemporalConstraint]
            clause = aggregate_clause + temporal_clause + simple_clause
            return StrongConstraintClause(clause, comparison_clause, "", condition_clause, whenever_clause, False)
        simple_clauses = [x for x in elem if type(x) == SimpleClause]
        aggregate_clause = [x for x in elem if type(x) == AggregateClause]
        comparison_clause = [x for x in elem if type(x) == ComparisonClause]
        where_clause = [x for x in elem if type(x) == WhereClause]
        quantified_constraint = [x for x in elem if type(x) == QuantifiedConstraint]

        simple_clauses += [quantified_constraint[0].body] if quantified_constraint else []
        clauses = simple_clauses if simple_clauses else aggregate_clause[0]
        comparison_clause = comparison_clause[0] if comparison_clause else []
        where_clause = where_clause[0] if where_clause else []

        return StrongConstraintClause(clauses, comparison_clause, where_clause, '', '', False)

    def positive_strong_constraint(self, elem):
        if([x for x in elem if type(x) == WheneverClause]):
            aggregate_clause = [x for x in elem if type(x) == AggregateClause]
            simple_clause = [x for x in elem if type(x) == SimpleClause]
            condition_clause = [x for x in elem if type(x) == ConditionClause]
            whenever_clause = [x for x in elem if type(x) == WheneverClause]
            comparison_clause = [x for x in elem if type(x) == ComparisonClause]
            temporal_clause = [x for x in elem if type(x) == TemporalConstraint]
            clause = aggregate_clause + temporal_clause + simple_clause
            return StrongConstraintClause(clause, comparison_clause, "", condition_clause, whenever_clause, True)
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

        return StrongConstraintClause(clauses, comparison_clause, where_clause, '', '', True)

    def weak_constraint(self, elem):
        if [x for x in elem if type(x) == WheneverClause]:
            priority_level = elem[1] if elem[1].type == str else elem[2]
            optimization_operator = elem[len(elem)-1]
            if elem[1].type == 'CNL_WEAK_OPTIMIZATION':
                optimization_operator = elem[1].value
            subject = [x for x in elem if type(x) == SubjectClause]
            verb = [x for x in elem if type(x) == VerbName][0]
            object = [x for x in elem if type(x) == ObjectClause]
            whenever_clause = [x for x in elem if type(x) == WheneverClause]
            for i, x in enumerate(elem):
                if type(x) == VerbName and type(elem[i - 1]) == lark.Token and \
                        elem[i - 1].value in ["have ", "have a ", "have an ", "has ", "has a ", "has an "]:
                    verb = VerbName(x.name, '', x.parameters) if x.preposition == 'to' else x
            verb = VerbName(f'{verb.name} {verb.preposition}'.strip(), verb.preposition,
                                 verb.parameters)
            return WeakConstraintClause(priority_level, '', optimization_operator, '', subject, verb, object, whenever_clause)
        else:
            where_clause = [x for x in elem if type(x) == WhereClause]
            where_clause = where_clause[0] if where_clause else []
            return WeakConstraintClause(elem[1], elem[2], elem[3], where_clause, '', '', '', '')

    def definition_clause(self, elem):
        return DefinitionClause(elem[0])

    def constant_definition_clause(self, elem):
        return ConstantDefinitionClause(elem[0], elem[1])

    def duration_clause(self, elem):
        if type(elem[0][0]) == Parameter:
            return DurationClause(elem[0][0], elem[1])
        else:
            (elem[0],) = elem[0]
            return DurationClause(str(elem[0]), elem[1])

    def duration_value(self, elem):
        return elem

    def quantified_choice_clause(self, elem):
        foreach_clause = [x for x in elem if type(x) == ForeachClause]
        parameters = [parameter for x in elem if type(x) == list for parameter in x if type(parameter) == Parameter]
        parametersDefinition = [parameter_definition for x in elem if type(x) == list for parameter_definition in x if
                                type(parameter_definition) == ParameterDefinition]
        quantified_range_clause = [x for x in elem if type(x) == QuantifiedRangeClause]
        quantified_object_clause = [x for x in elem if
                                    type(x) == QuantifiedObjectClause or type(x) == DisjunctionClause]
        foreach_clause = foreach_clause[0] if foreach_clause else []

        quantified_range_clause = quantified_range_clause[0] if quantified_range_clause else []
        quantified_object_clause = quantified_object_clause[0] if quantified_object_clause else []
        verb_name = [x for x in elem if type(x) == VerbName][0]
        # for i, x in enumerate(elem):
        #     if type(x) == VerbName and type(elem[i - 1]) == lark.Token and elem[i - 1].value in ["have ", "have a ",
        #                                                                                          "have an ", "has ", "has a ",
        #                                                                                          "has an "]:
        #         verb_name = VerbName(x.name,'', '') if x.preposition == 'to' else x
        duration_clause = [x for x in elem if type(x) == DurationClause]
        duration_clause = duration_clause[0] if duration_clause else []
        return QuantifiedChoiceClause(elem[0], elem[1], parameters, parametersDefinition,
                                      verb_name, quantified_range_clause,
                                      quantified_object_clause,
                                      duration_clause, foreach_clause)

    def disjunction_clause(self, elem):
        return DisjunctionClause(elem)

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

    def cardinality(self,elem):
        return Cardinality(elem[0])

    def quantified_maximum_quantity(self,elem):
        return QuantifiedMaximumQuantity(elem[0])

    def condition_comparison_clause(self, elem):
        if type(elem[1]) == lark.Token: elem[1] = elem[1].value
        elem[1] = elem[1] if type(elem[1]) == list else [elem[1]]
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
        subject = [x for x in elem if type(x) == SubjectClause][0]
        verb = [x for x in elem if type(x) == VerbClause][0]
        parameter_list = [x for x in elem if type(x) == list]
        if parameter_list:
            parameter_list = [x for x in parameter_list[0] if type(x) == Parameter]
        return SimpleClause(subject, parameter_list, verb, True)

    def comparison_clause(self, elem):
        return ComparisonClause(elem[0], elem[1])

    def parameter_variable(self,elem):
        res = ''
        for item in elem:
            res += item.value
        return res

    def subject_clause(self, elem):
        subject = []
        variable = []
        ordering = []
        parameters = []
        if len(elem) == 1:
            subject = elem[0]
        if len(elem) == 2:
            if type(elem[0]) == SubjectOrderingClause:
                subject = elem[1]
                ordering = elem[0]
            elif type(elem[1]) == str:
                subject = elem[0]
                variable = elem[1]
                variable = '' if variable == 'does' else variable
            elif type(elem[1]) == list:
                subject = elem[0]
                parameters = elem[1]
        if len(elem) >= 3:
            subject = elem[0]
            variable = elem[1] if elem[1].isupper() else ''
            ordering = [x.value for x in elem if type(x) == lark.Token]
            parameters = [x for x in elem if type(x) == list]
            parameters = [] if parameters == [] else parameters[0]
            if 'after' in elem or 'before' in elem:
                for idx, value in enumerate(elem):
                    if value == 'before' or value == 'after':
                        return [SubjectClause(subject, variable, ordering, parameters), TemporalConstraint(SubjectClause(subject, variable, ordering, parameters), elem[idx], elem[idx+1])]
        variable = '' if type(variable) == list and len(variable) == 0 else variable
        return SubjectClause(subject, variable, ordering, parameters)

    def verb_clause(self, elem):
        verb_name = f'{elem[0].name} {elem[0].preposition}'.strip() if type(
            elem[0]) != str else f'{elem[1].name} {elem[1].preposition}'.strip()
        negated = True if type(elem[0]) == str and 'not' in elem[0] else False
        verb_object_clause = [x for x in elem if type(x) == VerbObjectClause]
        composition_clause = [x for x in elem if type(x) == CompositionClause]
        tuple_clause = [x for x in elem if type(x) == TupleClause]
        object_clause = verb_object_clause + composition_clause + tuple_clause
        object_clause = object_clause[0] if len(object_clause) == 1 else object_clause if len(object_clause) > 1 else []
        parameters = elem[0].parameters if type(elem[0]) != str else elem[1].parameters
        return VerbClause(verb_name, object_clause, negated, parameters)

    def object_clause(self, elem):
        return ObjectClause(elem[0], []) if len(elem) == 1 else ObjectClause(elem[0], elem[1])

    def object_clause_l(self, elem):
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
        parameters = [ x for x in elem if type(x) == list]
        parameters = parameters[0] if len(parameters) > 0 else []
        temporal_ordering = [x for x in elem if type(x) == TemporalOrdering]
        temporal_ordering = temporal_ordering[0] if len(temporal_ordering) > 0 else []
        return VerbName(str(elem[0]), '', parameters, temporal_ordering)

    def temporal_ordering(self,elem):
        return TemporalOrdering(elem[0],'', elem[1].value)

    def verb_name_with_preposition(self, elem):
        name = ''
        parameters = []
        preposition = ''
        if len(elem) == 3:
            name = elem[0].value
            parameters = elem[1]
            preposition = elem[2].value
        if len(elem) == 2:
            name = elem[0].value
            preposition = elem[1].value
        return VerbName(name, preposition, parameters, '')

    def object_name(self, elem):
        (elem,) = elem
        return str(elem)

    def condition_expression(self, elem):
        return elem

    def condition_expression_value(self, elem):
        if len(elem) == 1:
            (elem,) = elem
            return elem
        elif len(elem) == 3 and elem[0].type == "CNL_NUMBER":
            return [elem[1], elem[2], elem[0]]
        else:
            return elem

    def condition_operation(self, elem):
        factors = None
        if len(elem) > 3:
            for i, element in enumerate(elem):
                if i > 2:
                    factors = []
                    factors.append(element)
        elem[2] = elem[2] if type(elem[2]) == list else [elem[2]]
        return ConditionOperation(elem[1], elem[0], elem[2], factors)

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
        parameter = [x for x in elem if type(x) == Parameter]
        aggregateBodyClause = [x for x in elem if type(x) == AggregateBodyClause][0]
        ranging_clause = [x for x in elem if type(x) == RangingClause]
        ranging_clause = ranging_clause[0] if ranging_clause else []
        return AggregateClause(elem[0], parameter, aggregateBodyClause, ranging_clause)

    def aggregate_active_clause(self, elem):
        subject_clause = [x for x in elem if type(x) == SubjectClause][0]
        parameters = [x for x in elem if type(x) == Parameter]
        verb_clause = [x for x in elem if type(x) == AggregateVerbClause]
        verb_clause = verb_clause[0] if (len(verb_clause) == 1) else verb_clause
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
        if len(elem) == 1:
            return elem[0]
        else:
            return elem

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
        return str(elem[0].value)

    def consecution_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def condition_match_clause(self, elem):
        return ConditionMatchClause(elem[0], elem[2], len(elem[2]))

    def aggregate_verb_clause(self, elem):
        if type(elem[0]) == str and 'not' in elem[0]:
            parameter = elem[1].parameters
            return AggregateVerbClause(f'{elem[1].name} {elem[1].preposition}'.strip(), True, parameter) if len(
                elem) == 2 else AggregateVerbClause(f'{elem[2].name} {elem[2].preposition}'.strip(), True, parameter)
        else:
            parameter = elem[0].parameters
            return AggregateVerbClause(f'{elem[0].name} {elem[0].preposition}'.strip(), False, parameter) if len(
                elem) == 1 else AggregateVerbClause(f'{elem[1].name} {elem[1].preposition}'.strip(), False, parameter)

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

    def temporal_type(self,elem):
        return str(elem[0].value)

    def weak_priority_clause(self, elem):
        (elem,) = elem
        return str(elem)

    def weak_optimization_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def condition_expression_operator(self, elem):
        if elem[0].type == "CNL_NUMBER":
            return ConditionExpressionOperator(str(elem[1]), True, elem[0]) if len(elem) == 3 else ConditionExpressionOperator(
                str(elem[1]), False, elem[0].value)
        return ConditionExpressionOperator(str(elem[0]), True, '') if len(elem) == 2 else ConditionExpressionOperator(
            str(elem[0]), False, '')

    def absolute_value_operator(self, elem):
        (elem,) = elem
        return str(elem)

    def enumerative_definition_clause(self, elem):
        objects_list = [x for x in elem[2:] if type(x) is SubjectClause]
        where_clause = [x for x in elem[3:] if type(x) is WhereClause]
        when_part = [x for x in elem[3:] if type(x) is WhenPart]
        verb = f'{elem[2].name} {elem[2].preposition}' if type(
            elem[2]) is VerbName else f'{elem[1].name} {elem[1].preposition}'
        if type(elem[1]) == lark.Token and elem[1].value in ["have ", "have a ","have an ", "has ","has a ","has an "]:
            verb = verb.replace(' to', '')
        verb = verb.strip()
        where_clause = where_clause[0] if where_clause else []
        when_part = when_part[0].body if when_part else []
        return EnumerativeDefinitionClause(elem[0], verb, objects_list, when_part, where_clause)

    def ranging_clause(self, elem):
        return RangingClause(elem[0], elem[1])

    def quantified_constraint(self, elem):
        return QuantifiedConstraint(elem[0], elem[1])

    def CNL_END_OF_LINE(self, elem):
        return lark.Discard



@dataclass(frozen=True)
class TemporalOrdering:
    shift_operator: str
    temporal_type: str
    parameter: str

@dataclass(frozen=True)
class Parameter:
    name: str
    variable: str

@dataclass(frozen=True)
class VerbName:
    name: str
    preposition: str
    parameters: list[Parameter]
    ordering: TemporalOrdering = ''

@dataclass(frozen=True)
class RangingClause:
    ranging_lhs: str
    ranging_rhs: str


@dataclass(frozen=True)
class PrimaryKey:
    parameters: list[Parameter]


@dataclass(frozen=True)
class WhenPart:
    body: list


@dataclass(frozen=True)
class ConditionExpressionOperator:
    operator: str
    absolute_value: bool
    modulo: str


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
class DurationClause:
    value: str | Parameter
    parameter: Parameter


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


@dataclass()
class SubjectClause:
    subject_name: str
    subject_variable: str
    subject_ordering: SubjectOrderingClause
    parameters: list[Parameter]


@dataclass(frozen=True)
class IfSameClause:
    object: SubjectClause


@dataclass(frozen=True)
class ObjectClause:
    object_name: str
    object_variable: str
    #object_parameters: list[str]


@dataclass(frozen=True)
class AggregateForClause:
    for_object: ObjectClause
    clause_determinant: str


@dataclass
class VerbClause:
    verb_name: str
    object_clause: list[ObjectClause]
    verb_negated: bool
    parameters: list[Parameter]


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
    parameters: Parameter


@dataclass
class SimpleClause:
    subject: SubjectClause
    parameter_list: list[Parameter]
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
    objects: list[SimpleObject]


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
    parameter: Parameter
    aggregate_body: AggregateBodyClause
    ranging_clause: RangingClause


@dataclass(frozen=True)
class ConditionOperation:
    expression_lhs: str | AggregateClause
    expression_operator: ConditionExpressionOperator
    expression_rhs: str | AggregateClause
    more_expression_factors: list[str] | None


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
    conditions: list[ConditionClause]


@dataclass(frozen=True)
class EnumerativeDefinitionClause:
    subject: SubjectClause
    verb_name: str
    object_list: list[SubjectClause]
    when_part: list
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
class QuantifiedMaximumQuantity:
    value: str

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
class QuantifiedExactQuantity:
    quantity: str


@dataclass(frozen=True)
class QuantifiedRangeClause:
    quantified_range_operator: str
    quantified_range_lhs: str
    quantified_range_rhs: str


@dataclass(frozen=True)
class QuantifiedObjectClause:
    objects: list[SimpleObject]


@dataclass(frozen=True)
class DisjunctionClause:
    objects: ObjectClause


@dataclass(frozen=True)
class ParameterDefinition:
    name: str
    variable: str


@dataclass(frozen=True)
class QuantifiedChoiceClause:
    quantifier: str
    subject_clause: SubjectClause
    parameters: list[Parameter]
    parameters_definitions: list[ParameterDefinition]
    verb_name: str
    range: QuantifiedExactQuantity | QuantifiedRangeClause
    object_clause: QuantifiedObjectClause | DisjunctionClause
    duration_clause: DurationClause
    foreach_clause: ForeachClause


@dataclass(frozen=True)
class DomainDefinition:
    subject: SubjectClause
    primary_key_parameters: list[Parameter]
    parameters: list[Parameter]


@dataclass(frozen=True)
class FactDefinition:
    subject: SubjectClause


@dataclass(frozen=True)
class ParameterList:
    parameters: list[Parameter]
    parameters_definitions: list[ParameterDefinition]

@dataclass(frozen=True)
class Cardinality:
    clause: QuantifiedMaximumQuantity | QuantifiedExactQuantity | QuantifiedRangeClause

@dataclass(frozen=True)
class ThenClause:
    subject: SubjectClause
    assignment_verb: str
    verb: VerbClause
    object: ObjectClause
    cardinality: Cardinality
    duration: DurationClause

@dataclass(frozen= True)
class TemporalConceptClause:
    name: str
    type: str
    lhs_range: str
    rhs_range: str
    step: int

@dataclass(frozen=True)
class TemporalConstraint:
    subject_clause: SubjectClause
    temporal_operator: str
    temporal_value: str

@dataclass(frozen=True)
class WheneverClause:
    subject: SubjectClause
    temporal_constraint: TemporalConstraint
    verb_negation: bool = False

@dataclass(frozen=True)
class WheneverThenClause:
    wheneverClause: WheneverClause
    thenClause: ThenClause

@dataclass(frozen=True)
class StrongConstraintClause:
    clauses: list[SimpleClause] | AggregateClause
    comparison_clause: ComparisonClause
    where_clause: WhereClause
    condition_clause: ConditionOperation
    whenever_clause: WheneverClause
    positive: True | False

@dataclass(frozen=True)
class WeakConstraintClause:
    priority_level: str
    constraint_body: ConditionOperation | AggregateClause
    optimization_operator: str
    where_clause: WhereClause
    subject: SubjectClause
    verb: VerbName
    object: ObjectClause
    whenever_clause: WheneverClause

@dataclass(frozen=True)
class ConstantDefinition:
    subject: SubjectClause
    value: str

@dataclass(frozen=True)
class DefinitionClause:
    clause: CompoundedClause | ConstantDefinitionClause | EnumerativeDefinitionClause | DomainDefinition | FactDefinition | ConstantDefinition

@dataclass(frozen=True)
class CNLContentTree:
    sentences: list[
        StrongConstraintClause | DefinitionClause | QuantifiedChoiceClause | PropertyClause | OrderingClause]
