from cnl2asp.specification.operation_component import Operators


def operation_operator(elem):
    return elem[0], "OPERATOR"


def operation_operand(elem):
    from user_cnl2asp.user_cnl_parser import transform_to_attribute_component
    return transform_to_attribute_component(elem[0]), "OPERAND"


def operation_sum(elem):
    return Operators.SUM


def operation_difference(elem):
    return Operators.DIFFERENCE


def operation_multiplication(elem):
    return Operators.MULTIPLICATION


def operation_division(elem):
    return Operators.DIVISION


def operation_equality(elem):
    return Operators.EQUALITY


def operation_inequality(elem):
    return Operators.INEQUALITY


def operation_greater_than(elem):
    return Operators.GREATER_THAN


def operation_less_than(elem):
    return Operators.LESS_THAN


def operation_greater_than_or_equal_to(elem):
    return Operators.GREATER_THAN_OR_EQUAL_TO


def operation_less_than_or_equal_to(elem):
    return Operators.LESS_THAN_OR_EQUAL_TO


def operation_conjunction(elem):
    return Operators.CONJUNCTION


def operation_disjunction(elem):
    return Operators.DISJUNCTION


def operation_left_implication(elem):
    return Operators.LEFT_IMPLICATION


def operation_right_implication(elem):
    return Operators.RIGHT_IMPLICATION


def operation_equivalence(elem):
    return Operators.EQUIVALENCE


def operation_negation(elem):
    return Operators.NEGATION


def operation_previous(elem):
    return Operators.PREVIOUS


def operation_weak_previous(elem):
    return Operators.WEAK_PREVIOUS


def operation_trigger(elem):
    return Operators.TRIGGER


def operation_always_before(elem):
    return Operators.ALWAYS_BEFORE


def operation_since(elem):
    return Operators.SINCE


def operation_eventually_before(elem):
    return Operators.EVENTUALLY_BEFORE


def operation_precede(elem):
    return Operators.PRECEDE


def operation_weak_precede(elem):
    return Operators.WEAK_PRECEDE


def operation_next(elem):
    return Operators.NEXT


def operation_weak_next(elem):
    return Operators.WEAK_NEXT


def operation_release(elem):
    return Operators.RELEASE


def operation_always_after(elem):
    return Operators.ALWAYS_AFTER


def operation_until(elem):
    return Operators.UNTIL


def operation_eventually_after(elem):
    return Operators.EVENTUALLY_AFTER


def operation_follow(elem):
    return Operators.FOLLOW


def operation_weak_follow(elem):
    return Operators.WEAK_FOLLOW
