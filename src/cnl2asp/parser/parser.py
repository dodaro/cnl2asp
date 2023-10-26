from __future__ import annotations
import re

from enum import Enum
from uuid import uuid4

import lark
from lark import Transformer, v_args

from cnl2asp.exception.cnl2asp_exceptions import LabelNotFound, ParserError, AttributeNotFound, EntityNotFound, \
    EntityNotFound, CompilationError, DuplicatedTypedEntity
from cnl2asp.parser.command import SubstituteVariable, Command, DurationClause, CreateSignature
from cnl2asp.parser.proposition_builder import PropositionBuilder, PreferencePropositionBuilder
from cnl2asp.proposition.attribute_component import AttributeComponent, ValueComponent, RangeValueComponent, AttributeOrigin
from cnl2asp.proposition.component import Component
from cnl2asp.proposition.constant_component import ConstantComponent
from cnl2asp.proposition.entity_component import EntityComponent, EntityType, TemporalEntityComponent, \
    SetOfTypedEntities, SetEntityComponent
from cnl2asp.proposition.problem import Problem
from cnl2asp.proposition.proposition import Proposition, NewKnowledgeComponent, ConditionComponent, \
    CardinalityComponent, PREFERENCE_PROPOSITION_TYPE, \
    PREFERENCE_PRIORITY_LEVEL
from cnl2asp.proposition.relation_component import RelationComponent
from cnl2asp.proposition.aggregate_component import AggregateComponent, AggregateOperation
from cnl2asp.proposition.operation_component import Operators, OperationComponent
from cnl2asp.utility.utility import Utility
from cnl2asp.exception.cnl2asp_exceptions import TypeNotFound


class QUANTITY_OPERATOR(Enum):
    EXACTLY = 0
    AT_MOST = 1
    AT_LEAST = 2


PRONOUNS = ['i', 'you', 'he', 'she', 'it', 'we', 'you', 'they']  # they are skipped if subject


def new_field_value(name: str = '') -> ValueComponent:
    if name:
        result = re.sub(r'[AEIOU]', '', name, flags=re.IGNORECASE)
        return ValueComponent(result.upper())
    return ValueComponent(f'X_{str(uuid4()).replace("-", "_")}')


class CNLTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self._problem: Problem = Problem()
        self._proposition: PropositionBuilder = PropositionBuilder()
        self._delayed_operations: list[Command] = []
        self._operation_parameter_queue: list[OperationComponent] = []

    def start(self, elem) -> Problem:
        return self._problem

    def _clear(self):
        self._proposition = PropositionBuilder()
        self._delayed_operations = []

    def explicit_definition_proposition(self, elem):
        if elem[0]:
            self._problem.add_signature(elem[0])
        self._clear()

    @v_args(meta=True)
    def explicit_definition_proposition_err(self, meta, elem):
        raise ParserError("Domain definitions should go at the beginning.", meta.line)

    def standard_definition(self, elem) -> EntityComponent:
        entity_keys = []
        if elem[1]:
            for key in elem[1]:
                if not key.origin:
                    key.origin = AttributeOrigin(elem[0])
                entity_keys.append(key)
        entity_attributes = []
        if elem[2]:
            for attributes in elem[2:]:
                for attribute in attributes:
                    if not attribute.origin:
                        attribute.origin = AttributeOrigin(elem[0])
                    entity_attributes.append(attribute)
        return EntityComponent(elem[0].lower(), '', entity_keys, entity_attributes)

    def keys_list(self, list_parameters) -> list[AttributeComponent]:
        res = []
        # Discard prepositions
        for elem in list_parameters:
            for attribute in elem:
                res.append(attribute)
        return res

    def parameter_definition(self, parameter) -> list[AttributeComponent]:
        name = parameter[:]
        # part of the parameter name can be the definition of the origin.
        # e.g. user id. we have an attribute id with origin user
        origin = self._parameter_origin_builder(name)
        if origin and not name:
            # if origin and not name the user imply the key of the last "origin"
            keys = self._problem.get_signature(parameter[-1]).get_keys()
            res = []
            for key in keys:
                key_origin = AttributeOrigin(origin.name, key.origin)
                res.append(AttributeComponent(key.name, ValueComponent(Utility.NULL_VALUE), key_origin))
            return res
        else:
            name = '_'.join(name)
        return [AttributeComponent(name.strip(), ValueComponent(Utility.NULL_VALUE), origin)]

    def temporal_concept_definition(self, elem):
        SetOfTypedEntities().add_entity(TemporalEntityComponent(elem[0], '', elem[2], elem[3], elem[4], elem[1]))
        return TemporalEntityComponent(elem[0], '', elem[2], elem[3], elem[4], elem[1])

    def temporal_value(self, elem):
        if len(elem) == 1:
            # string or number
            return elem[0]
        if elem[2].isnumeric():
            # date
            return f'{elem[0]}/{elem[1]}/{elem[2]}'
        # time
        return f'{elem[0]}:{elem[1]} {elem[2]}'

    @v_args(meta=True)
    def set_concept_definition(self, meta, elem):
        try:
            set_entity = SetEntityComponent(elem[0])
            SetOfTypedEntities().add_entity(set_entity)
            return set_entity
        except DuplicatedTypedEntity as e:
            raise CompilationError(str(e), meta.line)

    @v_args(meta=True)
    def set_elements_definition(self, meta, elem):
        try:
            set_entity: SetEntityComponent = SetOfTypedEntities().update_entity(elem[0])
            set_entity.values = elem[1]
        except EntityNotFound as e:
            CompilationError(str(e), line=meta.line)

    def implicit_definition_proposition(self, elem) -> None:
        for command in self._delayed_operations:
            command.execute()
        if elem[0]:
            self._problem.add_signature(elem[0])
        self._problem.add_propositions(self._proposition.get_propositions())
        self._clear()


    def constant_definition_clause(self, elem):
        value = ValueComponent(elem[1]) if elem[1] else ValueComponent('')
        self._problem.add_constant(ConstantComponent(elem[0], value))

    def compounded_range_clause(self, elem) -> EntityComponent:
        name: str = elem[0].lower()
        value = RangeValueComponent(elem[1], elem[2])
        entity = EntityComponent(name, '', [],
                                 [AttributeComponent(Utility.DEFAULT_ATTRIBUTE, value, AttributeOrigin(name))])
        self._proposition.add_new_knowledge(NewKnowledgeComponent(entity))
        return entity

    def simple_definition(self, elem) -> EntityComponent:
        name: str = elem[1].lower()
        attribute_name = Utility.DEFAULT_ATTRIBUTE
        try:
            signature = self._problem.get_signature(name)
            attributes = signature.get_keys_and_attributes()
            if len(attributes) == 1:
                attribute_name = attributes[0].name
        except EntityNotFound:
            pass
        entity = EntityComponent(name, '', [],
                               [AttributeComponent(attribute_name,
                                                   ValueComponent(elem[0]))])
        self._proposition.add_new_knowledge(NewKnowledgeComponent(entity))
        return entity

    @v_args(meta=True)
    def compounded_match_clause(self, meta, elem) -> EntityComponent:
        name: str = elem[0].lower()
        tail_attributes: list[(str, ValueComponent)] = elem[2] if elem[2] else []
        defined_entities: list[EntityComponent] = []
        for value in elem[1]:
            defined_entities.append(EntityComponent(name, '', [], [AttributeComponent(Utility.DEFAULT_ATTRIBUTE,
                                                                                      value, AttributeOrigin(name))]))
        for name, values in tail_attributes:
            if len(values) != len(defined_entities):
                raise CompilationError("Compounded tail has size different from values declared", meta.line)
            for i in range(len(values)):
                attribute = AttributeComponent(name, values[i])
                defined_entities[i].attributes.append(attribute)
        for entity in defined_entities[1:]:
            new_proposition = self._proposition.copy_proposition()
            new_proposition.new_knowledge.append(NewKnowledgeComponent(entity))
        self._proposition._original_rule.new_knowledge.append(NewKnowledgeComponent(defined_entities[0]))
        return defined_entities[0]

    def compounded_match_tail(self, elem) -> list[(str, ValueComponent)]:
        attributes: (str, ValueComponent) = []
        for name, value in zip(elem[0::2], elem[1::2]):
            attributes.append((name, value))
        return attributes


    def enumerative_definition_clause(self, elem):
        subject = elem[0]
        try:
            signature = self._problem.get_signature(subject.name)
        except:
            signature = self._proposition.create_new_signature(subject)
            self._problem.add_signature(signature)
        copy: EntityComponent = signature.copy()
        copy.set_attributes_value(subject.keys + subject.attributes)
        subject.keys = copy.keys
        subject.attributes = copy.attributes
        verb = elem[1]
        if subject.label or subject.attributes:
            self._proposition.add_requisite(subject)
            self._problem.add_signature(elem[0])  # we can have new definitions in subject position for this proposition
        else:
            # subject is an attribute value of the verb
            verb.attributes.append(AttributeComponent('id', ValueComponent(subject.name), AttributeOrigin(verb.name)))
        object_list = elem[2] if elem[2] else []
        for idx, object_entity in enumerate(object_list):
            # replace the object elements with the proper signature if same of the subject
            for entity in object_entity.get_entities():
                if entity.name == subject.name:
                    entity_signature = self._problem.get_signature(entity.name)
                    entity_signature.label = entity.label
                    entity_signature.set_attributes_value(entity.get_keys_and_attributes())
                    object_list[idx] = entity_signature
        self._proposition.add_new_knowledge(NewKnowledgeComponent(verb,
                                                                  ConditionComponent([])))
        # In this proposition we have a particular construction of the signature
        # we always have subjects and objects keys linked to the verb
        for key in self._problem.get_signature(subject.name).get_keys():
            verb.attributes.append(key.copy())
        for entity in object_list:
            for key in entity.get_keys():
                copy = key.copy()
                copy.value = ValueComponent(Utility.NULL_VALUE)
                verb.attributes.append(copy)
        signature = self._proposition.create_new_signature(verb)
        self._problem.add_signature(signature)
        self._proposition.add_requisite_list(object_list)
        for proposition in self._proposition.get_propositions():
            if subject.label or subject.attributes:
                object_list.insert(0, subject)
            self._make_new_knowledge_relations(proposition, object_list)

    @v_args(meta=True)
    def standard_proposition(self, meta, elem):
        try:
            for command in self._delayed_operations:
                command.execute()
            self._problem.add_propositions(self._proposition.get_propositions())
            self._clear()
        except Exception as e:
            raise CompilationError(str(e), meta.line)

    def _make_new_knowledge_relations(self, proposition: Proposition, components: list[Component] = None):
        if components:
            for component in components:
                for entity in component.get_entities():
                    for new_knowledge in proposition.new_knowledge:
                        proposition.relations.append(RelationComponent(new_knowledge.new_entity, entity))
        for new_knowledge in proposition.new_knowledge:
            for condition_entity in new_knowledge.condition.components:
                for entity in condition_entity.get_entities():
                    proposition.relations.append(
                            RelationComponent(new_knowledge.new_entity, entity))

    def whenever_then_clause_proposition(self, elem):
        for proposition in self._proposition.get_propositions():
            entities = [elem[1]] if elem[1] else []
            for components in proposition.requisite.components:
                for entity in components.get_entities():
                    entities.append(entity)
            self._make_new_knowledge_relations(proposition, entities)

    def whenever_clause(self, elem):
        if elem[0]:
            elem[1].negated = True
        self._proposition.add_requisite(elem[1])

    def then_clause(self, elem) -> [EntityComponent | str, Proposition]:
        subject = elem[0]
        # if can and not cardinality we have a
        # choice with cardinality = Null else we take the cardinality
        cardinality = CardinalityComponent(None, None) \
            if elem[1] == 'can' and not self._proposition.get_cardinality() else self._proposition.get_cardinality()
        self._proposition.add_cardinality(cardinality)
        return subject

    def fact_proposition(self, elem):
        self._proposition.add_new_knowledge(NewKnowledgeComponent(elem[0]))

    def quantified_choice_proposition(self, elem):
        subject: EntityComponent = elem[0]
        cardinality = CardinalityComponent(0, 1) \
            if elem[1] == 'can' and not self._proposition.get_cardinality() else self._proposition.get_cardinality()
        self._proposition.add_cardinality(cardinality)
        self._proposition.add_requisite(subject)
        for proposition in self._proposition.get_propositions():
            self._make_new_knowledge_relations(proposition, [subject])

    def foreach_clause(self, elem):
        objects: list[EntityComponent] = elem[0]
        self._proposition.add_requisite_list(objects)
        for proposition in self._proposition.get_propositions():
            for new_knowledge in proposition.new_knowledge:
                for entity in elem[0]:
                    proposition.relations.append(RelationComponent(new_knowledge.new_entity, entity))

    def constraint_proposition(self, elem):
        if elem[0] == "It is required that":
            if isinstance(elem[1], list):
                for e in elem[1]:
                    e.negate()
            else:
                elem[1].negate()

    def simple_clause_conjunction(self, elem):
        entities = []
        for entities_list in elem:
            for idx, entity in enumerate(entities_list):
                if idx == 1:
                    entities.append(entity)
                self._proposition.add_requisite(entity)
        return entities

    def simple_clause_wrv(self, elem) -> list[EntityComponent]:
        subject = elem[0]
        verb = elem[1]
        objects = elem[2] if elem[2] else []
        entities = [subject, verb, *objects]
        relations = [RelationComponent(subject, verb)]
        for object_elem in objects:
            relations.append(RelationComponent(verb, object_elem))
        self._proposition.add_relations(relations)
        return entities

    def simple_clause(self, elem):
        subject = elem[0]
        verb = elem[1]
        objects = elem[2] if elem[2] else []
        self._proposition.add_requisite_list([subject, verb] + objects)
        relations = [RelationComponent(subject, verb)]
        for object_elem in objects:
            relations.append(RelationComponent(verb, object_elem))
        self._proposition.add_relations(relations)

    def when_then_clause(self, elem):
        return elem[1]

    def quantified_simple_clause(self, elem):
        for i, entity_i in enumerate(elem[0][0:]):
            self._proposition.add_requisite(entity_i)
            for j, entity_j in enumerate(elem[i+1:]):
                self._proposition.add_relations([RelationComponent(entity_i, entity_j)])
        return elem[0][1]

    @v_args(meta=True)
    def temporal_constraint(self, meta, elem):
        try:
            temporal_entity = SetOfTypedEntities().get_entity_from_value(elem[2])
        except EntityNotFound as e:
            raise CompilationError(str(e), meta.line)
        if elem[2].isnumeric():
            elem[2] = int(elem[2])
        try:
            temporal_value = temporal_entity.get_temporal_value_id(elem[2])
        except KeyError as e:
            raise CompilationError(str(e), meta.line)
        subject: EntityComponent = elem[0]
        new_var = new_field_value('_'.join([temporal_entity.name, subject.name]))
        try:
            subject.set_attributes_value([AttributeComponent(temporal_entity.name, ValueComponent(new_var))])
        except:
            RuntimeError(f'Compilation error in line {meta.line}')
        operator = elem[1]
        self._proposition.add_requisite(subject)
        operation = OperationComponent(operator, new_var, ValueComponent(temporal_value))
        self._proposition.add_requisite(operation)
        return operation

    def ORDERING_OPERATOR(self, elem):
        if elem == 'after':
            return Operators.GREATER_THAN
        else:
            return Operators.LESS_THAN

    def terminal_clauses(self, elem):
        return [e for e in elem if e]

    def variable_substitution(self, elem):
        self._delayed_operations.append(SubstituteVariable(self._proposition, elem[0], elem[1]))

    def string_list(self, elem):
        return [ValueComponent(string) for string in elem]

    @v_args(inline=True)
    def parameter_entity_link(self, attribute: AttributeComponent, entity: EntityComponent):
        if attribute.value == Utility.NULL_VALUE:
            attribute.value = new_field_value('_'.join([entity.name, attribute.name]))
            entity.set_attributes_value([attribute])
        self._proposition.add_requisite(entity)
        return entity.get_attributes_by_name_and_origin(attribute.name, attribute.origin)[0]

    def arithmetic_operation_comparison(self, elem):
        arithmetic = OperationComponent(elem[0], *[x for x in elem[1:-2]])
        comparison = OperationComponent(elem[-2], arithmetic, elem[-1])
        self._proposition.add_requisite(comparison)
        return comparison

    def variable_comparison(self, elem):
        variable_comparison = OperationComponent(elem[1], elem[0], elem[2])
        self._proposition.add_requisite(variable_comparison)
        return variable_comparison

    def aggregate_comparison(self, elem):
        aggregate = elem[0]
        if elem[3]:
            aggregate.body += elem[3]
        aggregate = OperationComponent(elem[1], aggregate, elem[2])
        self._proposition.add_requisite(aggregate)
        return aggregate

    def simple_aggregate(self, elem):
        discriminant = [elem[1]]
        body = [elem[1]]
        aggregate = AggregateComponent(elem[0], discriminant, body)
        return aggregate

    def simple_aggregate_with_parameter(self, elem):
        discriminant = [elem[1]]
        body = [elem[2]]
        aggregate = AggregateComponent(elem[0], discriminant, body)
        return aggregate

    def aggregate_active_clause(self, elem) -> AggregateComponent:
        discriminant = [elem[1], elem[2]] if elem[2] else [elem[1]]
        body = [elem[3]]
        if elem[4]:
            body += elem[4]
            for entity in elem[4]:
                self._proposition.add_relations([RelationComponent(entity, elem[3])])
        return AggregateComponent(elem[0], discriminant, body)

    @v_args(meta = True)
    def aggregate_passive_clause(self, meta, elem) -> AggregateComponent:
        discriminant = [elem[1], elem[3]] if elem[3] else [elem[1]]
        verb: EntityComponent = elem[5]
        if elem[2]:
            try:
                verb.set_attributes_value(elem[2])
            except AttributeNotFound as e:
                raise CompilationError(str(e), meta.line)
        body = [verb]
        AggregateComponent(elem[0], discriminant, body)
        subject = elem[4]
        self._proposition.add_requisite(subject)
        self._proposition.add_relations([RelationComponent(subject, verb)])
        if elem[6]:
            body += elem[6]
            for entity in elem[6]:
                self._proposition.add_relations([RelationComponent(entity, verb)])
        return AggregateComponent(elem[0], discriminant, body)

    def predicate_with_objects_wrv(self, elem) -> list[EntityComponent]:
        verb = elem[0]
        objects = elem[1]
        if objects:
            return [verb, *objects]
        else:
            return [verb]

    def predicate_with_simple_clause_wrv(self, elem) -> list[EntityComponent]:
        verb = elem[0]
        entities = elem[1]
        return [verb, *entities]

    def such_that_clause(self, elem):
        return elem[0]

    def preference_with_aggregate_clause(self, elem):
        if elem[3]:
            new_var = new_field_value()
            self._proposition.add_requisite(OperationComponent(Operators.EQUALITY, elem[3],
                                                               new_field_value(new_var)))
            self._proposition.add_weight(new_var)

    def preference_with_variable_minimization(self, elem):
        self._proposition.add_weight(elem[4])

    @v_args(meta=True)
    def single_quantity_cardinality(self, meta, elem):
        cardinality = None
        if elem[0] == QUANTITY_OPERATOR.EXACTLY:
            cardinality = CardinalityComponent(elem[1], elem[1])
        elif elem[0] == QUANTITY_OPERATOR.AT_MOST:
            cardinality = CardinalityComponent(None, elem[1])
        elif elem[0] == QUANTITY_OPERATOR.AT_LEAST:
            cardinality = CardinalityComponent(elem[1], None)
        if self._proposition.get_cardinality() and self._proposition.get_cardinality() != cardinality:
            raise CompilationError('Error multiple cardinality provided in the same proposition', meta.line)
        else:
            self._proposition.add_cardinality(cardinality)

    @v_args(meta=True)
    def range_quantity_cardinality(self, meta, elem):
        cardinality = CardinalityComponent(elem[0], elem[1])
        if self._proposition.get_cardinality() and self._proposition.get_cardinality() != cardinality:
            raise CompilationError('Error multiple cardinality provided in the same proposition', meta.line)
        else:
            self._proposition.add_cardinality(cardinality)

    def conjunctive_object_list(self, elem):
        return [x for x in elem]

    def predicate_with_objects(self, elem) -> [NewKnowledgeComponent, CardinalityComponent]:
        verb: EntityComponent = elem[0]
        objects: list[Component] = elem[2]
        new_knowledge = NewKnowledgeComponent(verb, ConditionComponent(objects))
        if elem[-1]:
            self._delayed_operations.append(DurationClause(self._proposition, new_knowledge, elem[-2], elem[-1]))
        self._proposition.add_new_knowledge(new_knowledge)

    def predicate_with_simple_clause(self, elem):
        verb = elem[0]
        condition = elem[2]
        self._proposition.add_new_knowledge(NewKnowledgeComponent(verb, ConditionComponent(condition)))

    def parameter_list(self, list_parameters) -> list[AttributeComponent]:
        res = []
        # Discard prepositions
        for elem in list_parameters:
            if not isinstance(elem, lark.Token):
                res.append(elem)
        return list(res)

    def _parameter_origin_builder(self, name: list[str]):
        try:
            self._problem.get_signature(name[0])
            return AttributeOrigin(name.pop(0), self._parameter_origin_builder(name))
        except:
            return None

    def parameter(self, parameter) -> EntityComponent | AttributeComponent:
        name = parameter[:-4]
        try:
            entity = self._proposition.get_entity_by_label(parameter[-4])
            if entity.name == name[0]:
                return entity
        except LabelNotFound:
            pass
        # part of the parameter name can be the definition of the origin.
        # e.g. user id. we have an attribute id with origin user
        origin = self._parameter_origin_builder(name)
        if origin and not name:
            # if origin and not name the user imply the key of the last "origin"
            name = self._problem.get_signature(parameter[-5]).get_keys()[0].name
        else:
            name = '_'.join(name)
        value = parameter[-4] if parameter[-4] else Utility.NULL_VALUE
        operations = []
        if parameter[-3]:
            if parameter[-3] == Operators.EQUALITY and value == Utility.NULL_VALUE:
                value = parameter[-2]
            else:
                if value == Utility.NULL_VALUE:
                    value = new_field_value(name)
                operations = [OperationComponent(parameter[-3], value, parameter[-2])]
        attribute = AttributeComponent(name.strip(), ValueComponent(value), origin, operations)
        self._proposition.add_discriminant([attribute])
        return attribute

    def parameter_temporal_ordering(self, elem):
        name = SetOfTypedEntities.get_entity_from_type(elem[1]).name
        return AttributeComponent(name, ValueComponent(f'{elem[2]}{elem[0]}1'))

    def EXPRESSION(self, elem):
        return ''.join(elem)

    def _is_label(self, string: str) -> bool:
        if isinstance(string, EntityComponent):
            return False
        if string.isupper():
            return True
        return False

    def _is_variable(self, string: str) -> bool:
        if string.isupper():
            return True
        return False

    def entity_temporal_order_constraint(self, elem):
        return [elem[0], elem[1]]

    def _is_pronouns(self, elem: str) -> bool:
        return elem in PRONOUNS

    @v_args(meta=True, inline=True)
    def entity(self, meta, name, label, entity_temporal_order_constraint, define_subsequent_event,
               parameter_list, new_definition=False) -> EntityComponent | str:
        if self._is_label(name):
            try:
                return self._proposition.get_entity_by_label(name)
            except LabelNotFound as e:
                raise CompilationError(str(e), meta.line)
        name = name.lower()
        label = label if label else ''
        parameter_list = parameter_list if parameter_list else []
        if self._is_pronouns(name):
            return ''
        try:
            if not label:
                raise LabelNotFound("")
            entity = self._proposition.get_entity_by_label(label)
        except (LabelNotFound, AttributeNotFound):
            try:
                entity = self._problem.get_signature(name)
                entity.label = label
            except EntityNotFound as e:
                # this is the case that we are defining a new entity
                if new_definition:
                    parameter_list.sort(key=lambda x: x.name)
                    entity = EntityComponent(name, label, [],
                                             [attribute for attribute in parameter_list if
                                              isinstance(attribute, AttributeComponent)])
                else:
                    raise CompilationError(str(e), meta.line)
        try:
            entity.set_attributes_value(parameter_list, self._proposition)
        except AttributeNotFound as e:
            raise CompilationError(str(e), meta.line)
        if entity_temporal_order_constraint:
            self.temporal_constraint(meta, [entity] + entity_temporal_order_constraint)
        if define_subsequent_event:
            try:
                self.__substitute_subsequent_event(entity, define_subsequent_event[0], define_subsequent_event[1])
            except TypeNotFound as e:
                raise CompilationError(str(e), meta.line)
        if entity.label_is_key_value():
            entity.set_label_as_key_value()
        return entity

    @v_args(meta=True)
    def set_entity(self, meta, elem):
        try:
            set_entity: SetEntityComponent = SetOfTypedEntities.get_entity(elem[1])
            if not self._is_variable(elem[0].value):
                if not set_entity.is_value_in_set(elem[0].value):
                    raise AttributeError(f'Value \"{elem[0].value}\" not declared '
                                         f'in set {set_entity.get_entity_identifier()}')
            set_entity.set_attribute_value('element', elem[0])
            return set_entity
        except EntityNotFound as e:
            raise CompilationError(str(e), meta.line)

    def set_entity_parameter(self, elem):
        return self.parameter(elem)

    def __substitute_subsequent_event(self, entity, operator: str, entity_type: EntityType):
        attribute_name = ''
        for attribute in entity.get_keys_and_attributes():
            if SetOfTypedEntities.is_temporal_entity(attribute.name) and \
                    SetOfTypedEntities.get_entity(attribute.name).entity_type == entity_type:
                attribute_name = attribute.name
        for declared_entity in self._proposition.get_entities():
            if not declared_entity is entity:
                try:
                    attribute_value = declared_entity.get_attributes_by_name(attribute_name)[0].value
                    entity.set_attributes_value([AttributeComponent(attribute_name,
                                                                    ValueComponent(f'{attribute_value}{operator}1'))])
                    return
                except AttributeNotFound:
                    pass
        raise TypeNotFound(f'Entity "{entity.name}" do not have type {entity_type}')

    def define_subsequent_event(self, elem):
        return elem[0], elem[1]

    @v_args(meta=True)
    def verb(self, meta, elem):
        elem[1] = elem[1][0:-1] if elem[1][-1] == 's' else elem[1]  # remove 3rd person final 's'
        verb_name = '_'.join([elem[1], elem[3]]) if elem[3] else elem[1]
        verb_name = verb_name.lower()
        entity = self.entity(meta, verb_name, '', None, None, elem[2], new_definition=True)
        if elem[0]:
            entity.negated = True
        self._delayed_operations.append(CreateSignature(self._problem, self._proposition, entity))
        return entity

    def PREFERENCE(self, elem):
        self._proposition = PreferencePropositionBuilder()

    def OPTIMIZATION_STATEMENT(self, elem):
        if elem == 'as much as possible':
            self._proposition.add_type(PREFERENCE_PROPOSITION_TYPE.MAXIMIZATION)
        elif elem == 'as little as possible':
            self._proposition.add_type(PREFERENCE_PROPOSITION_TYPE.MINIMIZATION)

    def OPTIMIZATION_OPERATOR(self, elem):
        if elem == 'maximized':
            self._proposition.add_type(PREFERENCE_PROPOSITION_TYPE.MAXIMIZATION)
        elif elem == 'minimized':
            self._proposition.add_type(PREFERENCE_PROPOSITION_TYPE.MINIMIZATION)

    def PRIORITY_LEVEL(self, elem):
        if elem == 'low':
            self._proposition.add_level(PREFERENCE_PRIORITY_LEVEL.LOW)
        elif elem == 'medium':
            self._proposition.add_level(PREFERENCE_PRIORITY_LEVEL.MEDIUM)
        elif elem == 'high':
            self._proposition.add_level(PREFERENCE_PRIORITY_LEVEL.HIGH)

    def NUMBER(self, elem) -> ValueComponent:
        return ValueComponent(elem.value)

    def STRING(self, elem) -> ValueComponent:
        if self._is_label(elem.value):
            return ValueComponent(elem.value)
        return ValueComponent(elem.value.removesuffix('s'))

    def PREPOSITION(self, preposition) -> None:
        return preposition

    def ASSIGNMENT_VERB(self, verb):
        return verb

    def VERB_NEGATION(self, negation) -> bool:
        return True

    def QUANTITY_OPERATOR(self, quantity):
        if quantity == 'exactly':
            return QUANTITY_OPERATOR.EXACTLY
        elif quantity == 'at most':
            return QUANTITY_OPERATOR.AT_MOST
        elif quantity == 'at least':
            return QUANTITY_OPERATOR.AT_LEAST
        else:
            raise ParserError(f"Unrecognized token {quantity}")

    def COMPARISON_OPERATOR(self, elem):
        operator = elem.value
        if operator == "the same as" or operator == "equal to":
            return Operators.EQUALITY
        if operator == "different from":
            return Operators.INEQUALITY
        if operator == "more than" or operator == "greater than":
            return Operators.GREATER_THAN
        if operator == "less than":
            return Operators.LESS_THAN
        if operator == "greater than or equal to":
            return Operators.GREATER_THAN_OR_EQUAL_TO
        if operator == "less than or equal to":
            return Operators.LESS_THAN_OR_EQUAL_TO
        if operator == "not after":
            return Operators.LESS_THAN_OR_EQUAL_TO

    def ARITHMETIC_OPERATOR(self, elem):
        operator = elem.value
        if operator == "the sum":
            return Operators.SUM
        if operator == "the difference":
            return Operators.DIFFERENCE
        if operator == "the product":
            return Operators.MULTIPLICATION
        if operator == "the division":
            return Operators.DIVISION

    def PARAMETER_NAME(self, elem):
        return elem.value

    def TEMPORAL_TYPE(self, elem):
        if elem == "minutes" or elem == "minute":
            return EntityType.TIME
        elif elem == "days" or elem == "day":
            return EntityType.DATE
        elif elem == "steps" or elem == "step":
            return EntityType.STEP

    def SHIFT_OPERATOR(self, elem):
        if elem == 'the previous':
            return '-'
        else:
            return '+'

    def AGGREGATE_OPERATOR(self, elem):
        operator = elem.value
        if operator == "the number":
            return AggregateOperation.COUNT
        if operator == "the total":
            return AggregateOperation.SUM
        if operator == "the highest" or operator == "the biggest":
            return AggregateOperation.MIN
        if operator == "the lowest" or operator == "the smallest":
            return AggregateOperation.MIN
        raise ParserError(f"Aggregate operator {operator} not recognized")

    def VARIABLE(self, elem):
        return ValueComponent(elem.value)

    def COPULA(self, elem):
        return lark.Discard

    def INDEFINITE_ARTICLE(self, elem):
        return lark.Discard

    def QUANTIFIER(self, elem):
        return lark.Discard

    def NUMBER(self, elem):
        return elem.value

    def END_OF_LINE(self, end_of_line) -> None:
        return lark.Discard
