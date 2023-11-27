from cnl2asp.specification.aggregate_component import AggregateOperation
from cnl2asp.specification.entity_component import EntityComponent
from cnl2asp.specification.signaturemanager import SignatureManager


def aggregate_sum(elem):
    return AggregateOperation.SUM


def aggregate_count(elem):
    return AggregateOperation.COUNT


def aggregate_max(elem):
    return AggregateOperation.MAX


def aggregate_min(elem):
    return AggregateOperation.MIN


def aggregate_operator(elem):
    return elem[0], "OPERATOR"


def aggregate_discriminant(elem):
    from user_cnl2asp.user_cnl_parser import transform_to_attribute_component
    return transform_to_attribute_component(elem[0]), "DISCRIMINANT"


def aggregate_body(elem):
    try:
        entity = SignatureManager.get_signature(elem[0])
    except:
        entity = EntityComponent(elem[0], '', [], [])
        SignatureManager.add_signature(entity)
    return entity, "BODY"