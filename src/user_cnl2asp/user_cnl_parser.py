from cnl2asp.parser.parser import CNLTransformer
from cnl2asp.specification.aggregate_component import AggregateComponent
from cnl2asp.specification.attribute_component import ValueComponent, AttributeComponent
from cnl2asp.specification.component import Component
from cnl2asp.specification.operation_component import OperationComponent
from cnl2asp.specification.problem import Problem
from cnl2asp.specification.proposition import Proposition, PreferenceProposition, CardinalityComponent, \
    NewKnowledgeComponent, ConditionComponent
from .operation_functions import *
from .aggregate_functions import *


def transform_to_attribute_component(string: str):
    if isinstance(string, str):
        return AttributeComponent(string, ValueComponent(string))
    return string


def transform_to_entity_component(string: Component | str):
    if isinstance(string, str):
        try:
            entity = SignatureManager.get_signature(string)
        except:
            entity = EntityComponent(string, '', [], [])
            SignatureManager.add_signature(entity)
        return entity
    return string


def preference(elem):
    DynamicTransformer.proposition = PreferenceProposition(DynamicTransformer.proposition.requisite,
                                                           DynamicTransformer.proposition.relations)
    add_proposition()
    DynamicTransformer.proposition = Proposition()


def choice(elem):
    DynamicTransformer.proposition.cardinality = CardinalityComponent(None, None)
    add_proposition()
    DynamicTransformer.proposition = Proposition()


def constraint(elem):
    add_proposition()
    DynamicTransformer.proposition = Proposition()


def assignment(elem):
    add_proposition()
    DynamicTransformer.proposition = Proposition()


def add_proposition():
    DynamicTransformer.problem.add_proposition(DynamicTransformer.proposition)


def aggregate(elements):
    discriminant = []
    body = []
    operator = None
    for element in elements:
        if element[1] == "OPERATOR":
            operator = element[0]
        elif element[1] == "DISCRIMINANT":
            discriminant.append(element[0])
        elif element[1] == "BODY":
            body.append(element[0])
    return AggregateComponent(operator, discriminant, body)


def operation(elements):
    operands = []
    operator = None
    for elem in elements:
        if elem[1] == "OPERATOR":
            operator = elem[0]
        elif elem[1] == "OPERAND":
            operands.append(elem[0])
    return OperationComponent(operator, *operands)


def add_requisite(entity: Component | str):
    entity = transform_to_entity_component(entity[0])
    DynamicTransformer.proposition.add_requisite([entity])


def add_condition(entity: Component | str):
    entity = transform_to_entity_component(entity[0])
    try:
        DynamicTransformer.proposition.new_knowledge[0].condition.components += [
            entity]
    except Exception:
        DynamicTransformer.proposition.new_knowledge.append(NewKnowledgeComponent(EntityComponent('', '', [], []),
                                                                                  ConditionComponent([entity])))


def add_new_knowledge(entity: Component | str):
    entity = transform_to_entity_component(entity[0])
    try:
        DynamicTransformer.proposition.new_knowledge[0].new_entity = entity
    except Exception:
        DynamicTransformer.proposition.new_knowledge.append(
            NewKnowledgeComponent(entity))


class DynamicTransformer(CNLTransformer):
    problem: Problem = Problem()
    proposition: Proposition = Proposition()

    def __init__(self, functions: dict[str, str]):
        super().__init__()
        for function_name, function in functions.items():
            setattr(self, function_name, globals()[function])

    def standard_definition(self, elem):
        entity = super(DynamicTransformer, self).standard_definition(elem)
        SignatureManager.add_signature(entity)
