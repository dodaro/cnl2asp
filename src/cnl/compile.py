import copy
import re
import time
from uuid import uuid4
import os.path
import logging
from datetime import datetime, timedelta
from typing import TextIO

from lark import Lark
from cnl.parse import *
from dataclasses import *

debug: bool = False

comparison_relations = {'more than': ">", 'greater than': ">", 'less than': '<', 'different from': '!=',
                        'equal to': '=', 'at least': '>=', 'greater than or equal to': ">=", 'less than or equal to': "<=",
                        'at most': '<=', 'not after': '<='}
negated_relations = {'more than': "<=", 'greater than': "<=", 'less than': '>=', 'different from': '==',
                     'equal to': '!=',
                     'at least': '<', 'greater than or equal to': "<", 'less than or equal to': ">",
                     'at most': '>='}
aggregate_operators = {'number': 'count', 'total': 'sum', "highest": "max", "biggest": "max", "lowest": 'min',
                       "smallest": 'min'}
priority_levels_map = {'low': 1, 'medium': 2, 'high': 3}
condition_operation = {'the sum': '+', 'the difference': '-', 'the product': '*', 'the division': '/'}
temporal_to_comparison_relations = {'after': 'more than', 'before': 'less than'}
negated_temporal_to_comparison_relations = {'after': 'less than', 'before': 'more than'}
alphabetic_constants_set: set[str] = set()
ordered_constant_dict: dict[str, int] = {}
constant_definitions_dict: dict[str, str] = {}  # dict of defined constants


def get_list_bounds(input_list: list):
    return 1, len(input_list)


def get_ordering_number(of: str):
    return ordered_constant_dict[of]


class DefinitionError(Exception):

    def __init__(self, message):
        super().__init__(message)


class CNLFile:
    cnl_parser = Lark(open(os.path.join(os.path.dirname(__file__), "grammar/cnl_grammar.lark"), "r").read())

    def __init__(self, cnl_file: TextIO):
        content_tree: CNLContentTree = CNLTransformer().transform(self.cnl_parser.parse(cnl_file.read()))
        self.definitions: list[DefinitionClause] = [content_tree.sentences[i] for i in
                                                    range(len(content_tree.sentences)) if
                                                    type(content_tree.sentences[i]) is DefinitionClause]
        self.quantifiers: list[QuantifiedChoiceClause] = [content_tree.sentences[i] for i in
                                                          range(len(content_tree.sentences)) if
                                                          type(content_tree.sentences[i]) is QuantifiedChoiceClause]
        self.strongConstraints: list[StrongConstraintClause] = [content_tree.sentences[i] for i in
                                                                range(len(content_tree.sentences)) if
                                                                type(content_tree.sentences[i])
                                                                is StrongConstraintClause]
        self.weakConstraints: list[StrongConstraintClause | WeakConstraintClause] = \
            [content_tree.sentences[i] for i in
             range(len(content_tree.sentences)) if
             type(content_tree.sentences[i])
             is WeakConstraintClause]


class Signature:
    def __init__(self, subject: str, object_list: list[str], granularity_hierarchy: list[str] = [],
                 ordering_bounds: dict[str, int] = None, indexed_by_parameter: bool = False,
                 primary_key: list[str] = []):
        self.subject = subject
        self.object_list = object_list
        self.primary_key = primary_key
        self.granularity_hierarchy = granularity_hierarchy
        self.ordering_bounds = ordering_bounds if ordering_bounds is not None else {'lower': None, 'upper': None}
        if indexed_by_parameter:
            self.object_list = [self.subject + '_ord'] + self.object_list
        self.indexed_by_parameter = indexed_by_parameter

    def __repr__(self):
        return f"Signature(subject={str(self.subject)}, object_list={str(self.object_list)}, " \
               f"granularity_hierarchy={str(self.granularity_hierarchy)}, " \
               f"ordering_bounds=[lower={self.ordering_bounds['lower']}, " \
               f"upper={self.ordering_bounds['upper']}], " \
               f"primary_key={self.primary_key})"


class Atom:

    def __init__(self, atom_name: str, atom_parameters: dict[str, list[str]], ordering_index: int = None,
                 negated: bool = False):
        self.atom_name = atom_name.replace(' ', '_')  # predicate
        self.atom_parameters = atom_parameters  # List of the atom parameters. dict [predicate, value]
        self.ordering_index = ordering_index  # Ordered list index
        self.label = ''
        self.negated = negated

    def initializeVariables(self, signature, is_temporal_concept=False):
        if (len(self.atom_parameters) == 1 or is_temporal_concept) and self.label:
            if self.atom_parameters[list(self.atom_parameters.keys())[0]][0] == '_':
                self.atom_parameters[list(self.atom_parameters.keys())[0]][0] = self.label
        for parameter in signature.primary_key:
            if type(parameter) == Signature:
                self.atom_parameters[parameter.subject][0].initializeVariables(parameter)
            elif len(signature.primary_key) == 1 and self.label:
                self.atom_parameters[parameter][0] = self.label
            else:
                variable = f'X_{str(uuid4()).replace("-", "_")}'
                if self.atom_parameters[parameter][0] == '_':
                    self.atom_parameters[parameter][0] = variable

    def get_parameter_value(self, parameter_name):
        if len(self.atom_parameters.keys()) == 1: parameter_name = list(self.atom_parameters.keys())[0]
        for key, value in self.atom_parameters.items():
            if key == parameter_name:
                res = value[0]
                if type(value[0]) == Atom:
                    res = value[0].get_parameter_value(parameter_name)
                return res

    def has_parameter_value(self, parameter_value):
        for key, value in self.atom_parameters.items():
            if value[0] == parameter_value:
                return True
        return False

    def compute_signature(self):
        signature_objects = []
        for key, value in self.atom_parameters.items():
            if type(value[0]) == Atom:
                signature_objects.append(value[0].compute_signature())
            elif type(value[0]) == str:
                signature_objects.append(key)
        return Signature(self.atom_name.replace('_',' '), signature_objects)

    def get_parameter_name_from_parameter_value(self, parameter_value):
        for key, value in self.atom_parameters.items():
            if value[0] == parameter_value:
                return key
        return ''

    def copy(self):
        return Atom(copy.deepcopy(self.atom_name),
                    copy.deepcopy(self.atom_parameters),
                    copy.deepcopy(self.ordering_index),
                    copy.deepcopy(self.negated))

    # set the parameter variable
    def set_parameter_variable(self, parameter_name: str, new_variable: str, force: bool = False, index: int = None,
                               newDefinition: bool = False):
        if type(new_variable) == str and new_variable.isalpha() and not new_variable.isupper() and not (new_variable.lower() in list(constant_definitions_dict.keys())):
            new_variable = f'"{new_variable}"'
        elif type(new_variable) == str and new_variable.isalpha() and not new_variable.isupper() and new_variable.lower() in list(constant_definitions_dict.keys()) and constant_definitions_dict[new_variable.lower()]:
            new_variable = constant_definitions_dict[new_variable.lower()]



        # If the parameter name is not defined in the atom, add the new name and variable
        if parameter_name not in self.atom_parameters.keys() and parameter_name.split('_')[
            0] not in self.atom_parameters.keys():
            if (newDefinition):
                self.atom_parameters[parameter_name] = [new_variable]
            elif len(self.atom_parameters.keys()) == 1:
                self.set_parameter_variable(list(self.atom_parameters.keys())[0], new_variable)
            else:
                return
        else:
            # if it is given the index in input, substitute the value of the parameter with the new variable
            if index is not None:
                self.atom_parameters[parameter_name][index] = new_variable
                return self
            if (parameter_name in self.atom_parameters.keys()):
                for i, elem in enumerate(self.atom_parameters[parameter_name]):
                    # if the parameter was '_' replace it with the value of the new variable
                    if (elem == '_' and new_variable != '_') or force:
                        self.atom_parameters[parameter_name][i] = new_variable
                        return self
                    if (type(elem) == Atom and elem.atom_name == parameter_name):
                        elem.set_parameter_variable(parameter_name, new_variable)
                        return self
            else:
                splitted_parameter_name = parameter_name.split('_')
                for i, elem in enumerate(self.atom_parameters[splitted_parameter_name[0]]):
                    if (elem == '_' and new_variable != '_') or force:
                        self.atom_parameters[splitted_parameter_name[1]][i] = new_variable
                        return self
                    if (type(elem) == Atom and elem.atom_name == splitted_parameter_name[0]):
                        elem.set_parameter_variable(splitted_parameter_name[1], new_variable)
                        return self
            # if none of the above append the new variable
            if self.atom_parameters[parameter_name][0] != new_variable:
                self.atom_parameters[parameter_name].append(new_variable)
        return self

    # set the value of a parameter variable
    def set_variable_value(self, variable: str, value: str):
        for parameter, dict_variable_list in self.atom_parameters.items():
            for i, dict_variable in enumerate(dict_variable_list):
                if dict_variable == variable:
                    # if the value corresponds force the sobstitution
                    # this happens when a parameter is initialized with a variable and later on 
                    # it is given a value to this variable
                    self.set_parameter_variable(parameter, value, force=True, index=i)
                    return True
        return False

    def __str__(self):
        string: str = "" if self.negated is False else "not "
        string += f"{self.atom_name}("
        if self.ordering_index is not None:
            string += f"{self.ordering_index + 1},"
        for (i, parameter) in enumerate(self.atom_parameters.keys()):
            for j, elem in enumerate(self.atom_parameters[parameter]):
                string += str(elem)
                if j < len(self.atom_parameters[parameter]) - 1:
                    string += ","
            if i < len(self.atom_parameters.keys()) - 1:
                string += ","

        return string + ")"

    def __repr__(self):
        return self.__str__()


@dataclass(frozen=True)
class Aggregate:
    aggregate_operator: str
    aggregate_variables_list: list[str]
    aggregate_body: list[Atom | str]
    aggregate_head: list[Atom] | None

    def set_variable_value(self, variable: str, value: str):
        for atom in self.aggregate_body:
            found: bool = False
            if type(atom) is not str:
                found = atom.set_variable_value(variable, value)
            if found:
                self.aggregate_variables_list.remove(variable)

    def __str__(self):
        if self.aggregate_head is not None and len(self.aggregate_head) != 0:
            return f"{str(Conjunction(self.aggregate_head))}, #{aggregate_operators[self.aggregate_operator]}{{" \
                   f"{','.join(self.aggregate_variables_list)}: {str(Conjunction(self.aggregate_body))}}}"
        else:
            return f"#{aggregate_operators[self.aggregate_operator]}{{" \
                   f"{','.join(self.aggregate_variables_list)}: {str(Conjunction(self.aggregate_body))}}}"


@dataclass()
class Comparison:
    comparison_operator: str
    comparison_target: str | Aggregate
    lhs_parameter_name: str = ''
    comparison_value: str = ''
    rhs_parameter_name: str = ''
    comparison_lhs_modulo: str = ''
    comparison_rhs_modulo: str = ''
    negated: bool = False

    def set_variable_value(self, variable: str, value: str):
        if type(self.comparison_target) == Aggregate:
            self.comparison_target.set_variable_value(variable, value)
        if self.comparison_value == variable:
            self.comparison_value = value

    def isAngle(self, parameter: str):
        if 'angle' in parameter:
            return True
        return False

    def __str__(self):
        lhs = ''
        rhs = ''
        if self.comparison_lhs_modulo or self.isAngle(str(self.lhs_parameter_name)):
            if self.isAngle(str(self.lhs_parameter_name)):
                self.comparison_lhs_modulo = '360'
            lhs = f"({str(self.comparison_target)})\{self.comparison_lhs_modulo}"
        else:
            lhs = f"{str(self.comparison_target)}"
        if self.comparison_rhs_modulo or self.isAngle(str(self.rhs_parameter_name)):
            if self.isAngle(str(self.rhs_parameter_name)):
                self.comparison_rhs_modulo = '360'
            rhs = f"({str(self.comparison_value)})\{self.comparison_rhs_modulo}"
        else:
            rhs = f"{str(self.comparison_value)}"
        if type(lhs) == str and lhs.isalpha() and not lhs.isupper() and not lhs.lower() in list(constant_definitions_dict.keys()): lhs = f'"{lhs}"'
        if type(lhs) == str and lhs.isalpha() and not lhs.isupper() and lhs.lower() in list(constant_definitions_dict.keys()) and constant_definitions_dict[lhs.lower()]: lhs = constant_definitions_dict[lhs.lower()]
        if type(rhs) == str and rhs.isalpha() and not lhs.isupper() and not rhs.lower() in list(constant_definitions_dict.keys()): rhs = f'"{rhs}"'
        if type(rhs) == str and rhs.isalpha() and not rhs.isupper() and rhs.lower() in list(constant_definitions_dict.keys()) and constant_definitions_dict[rhs.lower()]: rhs = constant_definitions_dict[rhs.lower()]
        if self.negated:
            # check the current operator and replace it
            return f"{lhs} {negated_relations[self.comparison_operator]}" \
                   f" {rhs}"
        return f"{lhs} {comparison_relations[self.comparison_operator]}" \
               f" {rhs}"


class BoundedVariable:

    def __init__(self, variable_name: str, variable_bounds: dict[str, int | str]):
        self.__variable_name: str = variable_name
        self.__variable_bounds: dict[str, int] = variable_bounds

    def change_variable_name(self, new_name: str):
        self.__variable_name = new_name

    def change_variable_bounds(self, new_bounds: dict[str, int]):
        self.__variable_bounds = new_bounds

    def check_variable_name(self, with_string: str):
        return self.__variable_name == with_string

    def __str__(self):
        return f'{self.__variable_name} >= {self.__variable_bounds["lower"]}, ' \
               f'{self.__variable_name} <= {self.__variable_bounds["upper"]}'


class Conjunction:

    def __init__(self, body: list[Atom | Comparison | BoundedVariable | str]):
        self.body = body

    def copy(self):
        return Conjunction(copy.deepcopy(self.body))

    def set_variable_value(self, parameter: str, value: str):
        for elem in self.body:
            try:
                elem.set_variable_value(parameter, value)
            except AttributeError:
                if debug:
                    logging.warning(f'Method {self.set_variable_value.__name__} not implemented for type {type(elem)}. '
                                    f'Skipping...')

    def set_bounded_variable_bounds(self, variable_name: str, new_bounds: dict[str, int]):
        for elem in self.body:
            if type(elem) is BoundedVariable and elem.check_variable_name(variable_name):
                elem.change_variable_bounds(new_bounds)

    def extract_maybe_unsafe_atoms(self):
        result: list[Atom] = []
        for elem in self.body:
            if type(elem) is Atom and elem.negated:
                result.append(elem)
        return result

    def extract_safe_variables(self):
        result: set[str] = set()
        for elem in self.body:
            if type(elem) is Atom and not elem.negated:
                for parameter in elem.atom_parameters.keys():
                    for variable in elem.atom_parameters[parameter]:
                        if (match := re.search(r'(X(_[a-z0-9]+){5}|[A-Z]([A-Z0-9a-z_])*)', variable)) \
                                is not None:
                            result.add(match.group(1))
            if type(elem) is Comparison:
                if type(elem.comparison_target) is Aggregate:
                    for x in elem.comparison_target.aggregate_head:
                        if type(x) is Atom:
                            for x_parameter in x.atom_parameters.keys():
                                for x_variable in x.atom_parameters[x_parameter]:
                                    if (match := re.search(r'(X(_[a-z0-9]+){5}|[A-Z]([A-Z0-9a-z_])*)', x_variable)) \
                                            is not None:
                                        result.add(match.group(1))
        return result

    def __str__(self):
        string: str = ""
        for (i, atom) in enumerate(self.body):
            string += str(atom)
            if i < len(self.body) - 1:
                string += ", "

        return string


class ShortDisjunction:

    def __init__(self, lower_bound: str | None, upper_bound: str | None, is_bound_strict: dict[str, bool],
                 target_atom: Atom, variable_atoms: Conjunction):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.is_bound_strict = is_bound_strict
        self.target_atom = target_atom
        self.variable_atoms = variable_atoms

    def __str__(self):
        lower_bound_rel: str = '<' if self.is_bound_strict['lower'] is True else '<='
        upper_bound_rel: str = '<' if self.is_bound_strict['upper'] is True else '<='
        string: str = f'{{{str(self.target_atom)}'
        if self.variable_atoms.body:
            string += f':{str(self.variable_atoms)}'
        string += '}'
        if self.lower_bound is not None:
            string = f'{self.lower_bound} {lower_bound_rel} ' + string
        if self.upper_bound is not None:
            string = string + f' {upper_bound_rel} {self.upper_bound}'
        return string


@dataclass(frozen=True)
class SimpleDisjunction:
    body: list[Atom]

    def __str__(self):
        string: str = ""
        for (i, atom) in enumerate(self.body):
            string += str(atom)
            if i < len(self.body) - 1:
                string += " | "

        return string


@dataclass()
class ComplexDisjunction:

    def __init__(self, body: list[Atom], objects):
        self.body: list[Atom] = body
        self.object: dict() = objects

    def __str__(self):
        string: str = '{'
        for (i, head) in enumerate(self.body):
            string += f'{str(head)} : '
            for (j, body) in enumerate(self.object.get(head.atom_name)):
                string += f'{str(body)}'
            if (i < len(self.body) - 1):
                string += '; '
        string += '}'
        return string


@dataclass(frozen=True)
class Rule:
    head: ShortDisjunction | SimpleDisjunction | ComplexDisjunction
    body: Conjunction
    cost: list[str] = field(default_factory=list)
    discriminants: list[str] = field(default_factory=list)

    def __str__(self):
        string: str = ""
        if self.head is not None:
            string += f"{str(self.head)}"
        if self.body is not None:
            if self.head is not None:
                string += f" "
            if not self.cost:
                string += f":- {str(self.body)}.\n"
            else:
                string += f":~ {str(self.body)}. [{self.cost[0]}@{self.cost[1]}"
                if self.discriminants:
                    string += ', '
                    for (i, discriminant) in enumerate(self.discriminants):
                        string += discriminant
                        if i < len(self.discriminants) - 1:
                            string += ", "
                string += ']\n'
        else:
            string += ".\n"
        return string


@dataclass
class Operation:
    operation_lhs: str
    operator: str
    operation_rhs: str
    operation_eq_variable: str | None
    absolute_value: bool = False
    more_factors: str = None

    def set_variable_value(self, parameter: str, value: str):
        if self.operation_lhs == parameter:
            self.operation_lhs = value
        if self.operation_rhs == parameter:
            self.operation_rhs = value

    def __str__(self):
        string: str = f'{self.operation_eq_variable} = ' if self.operation_eq_variable is not None else ''
        lhs = self.operation_lhs
        rhs = self.operation_rhs
        if type(lhs) == str and lhs.isalpha() and not lhs.isupper() and not lhs.lower() in list(
            constant_definitions_dict.keys()): lhs = f'"{lhs}"'
        if type(lhs) == str and lhs.isalpha() and not lhs.isupper() and lhs.lower() in list(
            constant_definitions_dict.keys()) and constant_definitions_dict[lhs.lower()]: lhs = \
        constant_definitions_dict[lhs.lower()]
        if type(rhs) == str and rhs.isalpha() and not lhs.isupper() and not rhs.lower() in list(
            constant_definitions_dict.keys()): rhs = f'"{rhs}"'
        if type(rhs) == str and rhs.isalpha() and not rhs.isupper() and rhs.lower() in list(
            constant_definitions_dict.keys()) and constant_definitions_dict[rhs.lower()]: rhs = \
        constant_definitions_dict[rhs.lower()]

        if not self.absolute_value:
            string += f"{lhs} {condition_operation[self.operator]} {rhs}"
            if self.more_factors:
                for factor in self.more_factors:
                    if type(factor) == str and factor.isalpha() and not factor.isupper() and not factor.lower() in list(
                            constant_definitions_dict.keys()): factor = f'"{factor}"'
                    if type(factor) == str and factor.isalpha() and not factor.isupper() and factor.lower() in list(
                            constant_definitions_dict.keys()) and constant_definitions_dict[factor.lower()]: factor = \
                        constant_definitions_dict[factor.lower()]
                    string += f' {condition_operation[self.operator]} {factor}'
        else:
            string += f"|{lhs} {condition_operation[self.operator]} {rhs}"
            if self.more_factors:
                for factor in self.more_factors:
                    string += f' {string} {condition_operation[self.operator]} {factor}'
            string += "|"
        return string


@dataclass(frozen=True)
class OrderingShift:
    shift_operation: str
    target_variables: tuple[str, str]
    shift_count: int

    def __str__(self):
        if self.shift_operation == 'before':
            return f"{self.target_variables[0]}+{self.shift_count} == {self.target_variables[1]}"
        elif self.shift_operation == 'after':
            return f"{self.target_variables[1]}+{self.shift_count} == {self.target_variables[0]}"


class SubjectOrdering:

    def __init__(self, subject_ordering_in_clause: SubjectOrderingClause):
        self.ordering_direction = subject_ordering_in_clause.ordering_operator
        self.ordering_count = 1 if not subject_ordering_in_clause.consecution_clause else \
            int(subject_ordering_in_clause.consecution_clause.consecution_count)
        self.consecutive = True if subject_ordering_in_clause.consecution_clause else False

    def get_ordering_shift_string(self, from_value: str, ordering_memory: int) -> (str, int):
        if self.ordering_direction == 'the next':
            return f'{from_value}+{abs(ordering_memory + self.ordering_count)}', self.ordering_count
        else:
            return f'{from_value}-{abs(ordering_memory - self.ordering_count)}', -1 * self.ordering_count


class VerbObjectOrdering:

    def __init__(self, verb_object_ordering_in_clause: VerbObjectOrderingClause):
        self.ordering_operator = verb_object_ordering_in_clause.verb_ordering_operator
        self.ordering_variable = verb_object_ordering_in_clause.verb_ordering_variable

    def get_ordering_string(self, first_variable: str, second_variable: str, signature_bounds: dict[str, int]) -> str:
        variable = second_variable if second_variable is not None else self.ordering_variable
        if self.ordering_operator == 'before':
            return f'{first_variable} < {variable} <= {signature_bounds["upper"]}'
        else:
            return f'{signature_bounds["lower"]} >= {first_variable} > {variable}'


class VerbObjectConsecution:

    def __init__(self, verb_object_consecution_in_clause: VerbObjectConsecutionClause):
        self.consecution_object_name = verb_object_consecution_in_clause.verb_consecution_object_name.removesuffix("s")
        self.consecution_operator = verb_object_consecution_in_clause.verb_consecution_operator
        self.consecution_count = int(verb_object_consecution_in_clause.verb_consecution_count)


class VerbObjectBinaryRange:

    def __init__(self, binary_range_in_clause: ObjectBinaryRange):
        self.range_lower_bound = binary_range_in_clause.range_lhs
        self.range_upper_bound = binary_range_in_clause.range_rhs


class VerbObjectWindowedRange:

    def __init__(self, windowed_range_in_clause: ObjectWindowedRange):
        self.range_object = windowed_range_in_clause.object_type
        self.range_window = windowed_range_in_clause.window_value


class Subject:

    def __init__(self, subject_in_clause: SubjectClause):
        self.name = subject_in_clause.subject_name.removesuffix("s")
        self.name = self.name.lower()
        if not subject_in_clause.subject_variable:
            self.variable = f'X_{str(uuid4()).replace("-", "_")}'
        else:
            if subject_in_clause.subject_variable.isupper():
                self.variable = subject_in_clause.subject_variable
            else:
                self.variable = subject_in_clause.subject_variable.lower()
        if not subject_in_clause.subject_ordering:
            self.ordering = None
        else:
            self.ordering = SubjectOrdering(subject_in_clause.subject_ordering)


class Verb:

    def __init__(self, verb_in_clause: AggregateVerbClause | VerbClause):
        self.name = " ".join([substr.strip().removesuffix("s") for substr in verb_in_clause.verb_name.split(' ')])
        self.name = self.name.lower()
        self.is_negated = verb_in_clause.verb_negated


class Object:

    def __init__(self, object_in_clause: ObjectClause):
        self.name = object_in_clause.object_name.removesuffix("s")
        self.name = self.name.lower()
        if not object_in_clause.object_variable:
            self.variable = f'X_{str(uuid4()).replace("-", "_")}'
        else:
            if object_in_clause.object_variable.isupper():
                self.variable = object_in_clause.object_variable
            else:
                self.variable = object_in_clause.object_variable.lower()
        self.name.lower()


class AggregateForObject:
    def __init__(self, for_object_in_clause: AggregateForClause):
        self.for_object = Object(for_object_in_clause.for_object)
        self.in_aggregate_body = True if for_object_in_clause.clause_determinant == 'any' else False


class VerbObject:

    def __init__(self, verb_object_in_clause: VerbObjectClause):
        if not type(verb_object_in_clause.verb_object_range) == ObjectRange:
            self.range = None
            self.name = verb_object_in_clause.verb_object_name.removesuffix("s")
        else:
            self.name = verb_object_in_clause.verb_object_name.removesuffix("s") if \
                verb_object_in_clause.verb_object_name != 'occurrences' else \
                verb_object_in_clause.verb_object_range.range_expression.object_type.removesuffix("s")
            if type(verb_object_in_clause.verb_object_range.range_expression) == ObjectWindowedRange:
                self.range = VerbObjectWindowedRange(verb_object_in_clause.verb_object_range.range_expression)
            elif type(verb_object_in_clause.verb_object_range.range_expression) == ObjectBinaryRange:
                self.range = VerbObjectBinaryRange(verb_object_in_clause.verb_object_range.range_expression)
        if not verb_object_in_clause.verb_object_variable:
            self.variable = f'X_{str(uuid4()).replace("-", "_")}'
        else:
            self.variable = verb_object_in_clause.verb_object_variable
        if not verb_object_in_clause.verb_object_ordering:
            self.ordering = None
        else:
            self.ordering = VerbObjectOrdering(verb_object_in_clause.verb_object_ordering)
        if not verb_object_in_clause.verb_object_consecution:
            self.consecution = None
        else:
            self.consecution = VerbObjectConsecution(verb_object_in_clause.verb_object_consecution)
        self.name = self.name.lower()


class ClauseBlockMemory:

    def __init__(self):
        self.subject_in_block: Subject | None = None
        self.__time_windows: dict[str, int] = {}
        self.__atoms_memory: list[Atom] = []
        self.__time_variables_memory: dict[str, str] = {}
        self.__inequalities_memory: list[str] = []
        self.__bounded_variables_memory: list[BoundedVariable] = []
        self.__ordering_variable_mappings_memory: dict[str, str] = {}

    def set_subject_of_block(self, block_subject: Subject):
        self.subject_in_block = block_subject

    def add_time_variable_to_memory(self, variable_name: str, variable_value: str):
        if variable_name not in self.__time_variables_memory.keys():
            self.__time_variables_memory[variable_name] = variable_value

    def get_time_variable_value(self, variable_name: str):
        if variable_name not in self.__time_variables_memory.keys():
            return None
        return self.__time_variables_memory[variable_name]

    def add_inequality_to_memory(self, inequality: str):
        self.__inequalities_memory.append(inequality)

    def add_bounded_variable_to_memory(self, bounded_variable: BoundedVariable):
        self.__bounded_variables_memory.append(bounded_variable)

    def add_ordering_variable_mapping_to_memory(self, from_variable: str, to_variable: str):
        self.__ordering_variable_mappings_memory[from_variable] = to_variable

    def go_forward_in_time(self, of: int, on_time_window_of: str):
        self.__time_windows[on_time_window_of] += of

    def go_backward_in_time(self, of: int, on_time_window_of: str):
        self.__time_windows[on_time_window_of] -= of

    def get_current_time_position(self, on_time_window_of: str):
        if on_time_window_of not in self.__time_windows.keys():
            self.__time_windows[on_time_window_of] = 0
        return self.__time_windows[on_time_window_of]

    def get_ordering_variable_mapping(self, of: str):
        if of not in self.__ordering_variable_mappings_memory.keys():
            return of
        return self.__ordering_variable_mappings_memory[of]

    def add_atom_to_memory(self, atom: Atom):
        self.__atoms_memory.append(atom)

    def flush_atoms_memory(self, on: list[Atom | str]):
        for atom in self.__atoms_memory:
            on.insert(0, atom)

    def flush_inequalities_memory(self, on: list[Atom | str]):
        for inequality in self.__inequalities_memory:
            on.append(inequality)

    def flush_bounded_variables_memory(self, on: list[Atom | str | BoundedVariable]):
        for bounded_variable in self.__bounded_variables_memory:
            on.append(bounded_variable)

    def flush_all(self, on: list[Atom]):
        self.flush_atoms_memory(on=on)
        self.flush_inequalities_memory(on=on)
        self.flush_bounded_variables_memory(on=on)


class TemporalConcept:
    TEMPORAL_DATE = 0
    TEMPORAL_TIME = 1
    TEMPORAL_STEP = 2

    def __init__(self, name, type, lhs_range, rhs_range, step=1):
        self.name = name
        self.type = type
        self.step = step
        self.temporal_element_list = self.set_element_list(lhs_range, rhs_range)

    def set_element_list(self, lhs_range, rhs_range):
        elements = dict()
        counter = 1
        if self.type == self.TEMPORAL_TIME:
            start = datetime.strptime(lhs_range, '%I:%M %p')
            end = datetime.strptime(rhs_range, '%I:%M %p')
            elements[0] = start.strftime('%H:%M')
            start = start + timedelta(minutes=self.step)
            while datetime.strptime(elements[counter-1], '%H:%M') < end:
                if start > end: start = end
                elements[counter] = start.strftime('%H:%M')
                counter += 1
                start = start + timedelta(minutes=self.step)
        elif self.type == self.TEMPORAL_DATE:
            start = datetime.strptime(lhs_range, '%d/%m/%Y')
            end = datetime.strptime(rhs_range, '%d/%m/%Y')
            elements[0] = start.strftime('%d/%m/%Y')
            start = start + timedelta(days=self.step)
            while datetime.strptime(elements[counter-1], '%d/%m/%Y') < end:
                if start > end: start = end
                elements[counter] = start.strftime('%d/%m/%Y')
                counter += 1
                start = start + timedelta(days=self.step)
        elif self.type == self.TEMPORAL_STEP:
            start = lhs_range
            end = rhs_range
            elements[0] = start
            for i in range(int(start)+1, int(end) + 1):
                elements[counter] = i
                counter += 1
        return elements

    def __str__(self):
        facts = ''
        if self.type == self.TEMPORAL_DATE or self.type == self.TEMPORAL_TIME:
            for idx, value in self.temporal_element_list.items():
                facts += f'{self.name}({idx + 1},"{value}").  '
        elif self.type == self.TEMPORAL_STEP:
            for idx, value in self.temporal_element_list.items():
                facts += f'{self.name}({value}).  '
        return facts + '\n'


class CNLCompiler:

    def __init__(self):
        self.__compilation_result: str = ""
        self.decl_signatures: list[Signature] = []
        self.time_temporal_concepts: list[TemporalConcept] = []
        self.date_temporal_concepts: list[TemporalConcept] = []
        self.step_temporal_concepts: list[TemporalConcept] = []

    # For each definition call the corresponding compile method
    def compile(self, file: CNLFile):
        dependent_definitions = []
        for definition_clause in file.definitions:
            try:
                if type(definition_clause.clause) == CompoundedClause:
                    if type(definition_clause.clause.definition) == CompoundedClauseRange:
                        self.__compilation_result += self.__compile_compounded_clause_range(definition_clause.clause)
                    else:
                        self.__compilation_result += self.__compile_compounded_clause_match(definition_clause.clause)
                elif type(definition_clause.clause) == EnumerativeDefinitionClause:
                    self.__compilation_result += self.__compile_enumerative_definition_clause(definition_clause.clause)
                elif type(definition_clause.clause) == ConstantDefinitionClause:
                    self.__compile_constant_definition_clause(definition_clause.clause)
                elif type(definition_clause.clause) == DomainDefinition:
                    self.__compile_domain_definition(definition_clause.clause)
                elif type(definition_clause.clause) == FactDefinition:
                    self.__compilation_result += self.__compile_fact_definition(definition_clause.clause)
                elif type(definition_clause.clause) == WheneverThenClause:
                    self.__compilation_result += self.__compile_wheneverThen_clause(definition_clause.clause)
                elif type(definition_clause.clause) == TemporalConceptClause:
                    self.__compilation_result += self.__compile_temporal_concept_clause(definition_clause.clause)
            except (IndexError):
                dependent_definitions.append(definition_clause)
        for quantifier_clause in file.quantifiers:
            self.__compilation_result += self.__compile_quantified_choice_clause(quantifier_clause)
        for constraint in file.strongConstraints:
            self.__compilation_result += self.__compile_strong_constraint_clause(constraint)
        for constraint in file.weakConstraints:
            self.__compilation_result += self.__compile_weak_constraint_clause(constraint)
        for definition_clause in dependent_definitions:
            if type(definition_clause.clause) == CompoundedClause:
                if type(definition_clause.clause.definition) == CompoundedClauseRange:
                    self.__compilation_result += self.__compile_compounded_clause_range(definition_clause.clause)
                else:
                    self.__compilation_result += self.__compile_compounded_clause_match(definition_clause.clause)
            elif type(definition_clause.clause) == EnumerativeDefinitionClause:
                self.__compilation_result += self.__compile_enumerative_definition_clause(definition_clause.clause)
            elif type(definition_clause.clause) == ConstantDefinitionClause:
                self.__compile_constant_definition_clause(definition_clause.clause)
        return self

    def into(self, out_file: TextIO):
        out_file.write(self.__compilation_result)
        return self

    def newVar(self):
        return f'X_{str(uuid4()).replace("-", "_")}'


    def __compile_temporal_concept_clause(self, clause: TemporalConcept):
        if clause.type == 'minutes':
            datetime.strptime(clause.lhs_range, '%I:%M %p')
            temporal_concept = TemporalConcept(clause.name, TemporalConcept.TEMPORAL_TIME, clause.lhs_range,
                                               clause.rhs_range,
                                               clause.step)
            self.time_temporal_concepts.append(temporal_concept)
            self.decl_signatures.append(Signature(clause.name, [clause.name, 'value'], primary_key=[clause.name]))
            return str(temporal_concept)
        elif clause.type == 'days':
            temporal_concept = TemporalConcept(clause.name, TemporalConcept.TEMPORAL_DATE, clause.lhs_range,
                                               clause.rhs_range,
                                               clause.step)
            self.date_temporal_concepts.append(temporal_concept)
            self.decl_signatures.append(Signature(clause.name, [clause.name, 'value'], primary_key=[clause.name]))
            return str(temporal_concept)
        elif clause.type == 'steps':
            temporal_concept = TemporalConcept(clause.name, TemporalConcept.TEMPORAL_STEP, clause.lhs_range,
                                               clause.rhs_range,
                                               clause.step)
            self.step_temporal_concepts.append(temporal_concept)
            self.decl_signatures.append(Signature(clause.name, [clause.name], primary_key=[clause.name]))
            return str(temporal_concept)

    def init_atom_from_subject_clause(self, subject_clause: SubjectClause, body: list[Atom]):
        """
        Create and return the atom generated from a subject_clause
        @param subject_clause:
        @param body: the list of atoms present in the current rule
        @return: the atom and the list of comparisons
        """
        atom = self.__get_atom_from_signature_subject(subject_clause.subject_name)
        comparisons = []
        if subject_clause.subject_variable:
            atom.label = subject_clause.subject_variable
        if subject_clause.subject_ordering:
            for atom_in_body in body:
                if subject_clause.subject_ordering[1] in list(atom_in_body.atom_parameters.keys()):
                    value = atom_in_body.atom_parameters[subject_clause.subject_ordering[1]][0] if type(
                        atom_in_body.atom_parameters[subject_clause.subject_ordering[1]][0]) == str else \
                        list(atom_in_body.atom_parameters[subject_clause.subject_ordering[1]][
                                 0].atom_parameters.values())[
                            0][0]
                    if subject_clause.subject_ordering[0] == 'previous':
                        atom.set_parameter_variable(subject_clause.subject_ordering[1], value + '-1')
                    else:
                        atom.set_parameter_variable(subject_clause.subject_ordering[1], value + '+1')
        if subject_clause.parameters:
            comparisons = self.set_parameter_list(atom, subject_clause.parameters)
        else:
            atom.initializeVariables(self.__get_signature(atom.atom_name), self.is_temporal_concept(atom.atom_name))
        return atom, comparisons

    def init_atom_from_object_clause(self, object_clause: ObjectClause):
        """
        Create and return the atom generated from an ObjectClause
        @param object_clause:
        @return: the atom and the list of comparisons
        """
        atom = self.__get_atom_from_signature_subject(object_clause.object_name)
        comparisons = []
        if object_clause.object_variable and type(object_clause.object_variable) == list:
            comparisons += self.set_parameter_list(atom, object_clause.object_variable)
        else:
            parameter_name = [atom.atom_name]
            if self.__get_signature(atom.atom_name).primary_key:
                parameter_name = self.__get_signature(atom.atom_name).primary_key
            if object_clause.object_variable:
                atom.label = object_clause.object_variable
                atom.set_parameter_variable(parameter_name[0], object_clause.object_variable)
            else:
                for name in parameter_name:
                    atom.set_parameter_variable(name, self.newVar(), self.is_temporal_concept(atom.atom_name))
        return atom, comparisons

    def temporal_constraint(self, atom: Atom, temporal_constraint: TemporalConstraint):
        """
        Define a new comparison for the temporal constraint
        @param atom: the atom to which the temporal constraint is applied
        @param wheneverClause:
        @return: Comparison
        """
        comparisons = []
        for parameter in list(atom.atom_parameters.keys()):
            if self.isTime(temporal_constraint.temporal_value):
                for tc in self.time_temporal_concepts:
                    if parameter == tc.name:
                        variable = self.newVar()
                        atom.set_parameter_variable(parameter, variable)
                        time = datetime.strptime(temporal_constraint.temporal_value, '%I:%M %p').strftime(
                            '%H:%M')
                        value = list(tc.temporal_element_list.values()).index(time) + 1
                        comparisons.append(
                            Comparison(temporal_to_comparison_relations[clause.temporal_constraint.temporal_operator],
                                       variable, '', value, ''))
            elif self.isDate(temporal_constraint.temporal_value):
                for tc in self.date_temporal_concepts:
                    if parameter == tc.name:
                        variable = self.newVar()
                        atom.set_parameter_variable(parameter, variable)
                        time = datetime.strptime(temporal_constraint.temporal_value, '%d/%m/%Y').strftime(
                            '%d/%m/%Y')
                        value = list(tc.temporal_element_list.values()).index(time) + 1
                        comparisons.append(
                            Comparison(temporal_to_comparison_relations[temporal_constraint.temporal_operator],
                                       variable, '', value, ''))
            else:
                # single field atom that is before a constant
                variable = temporal_constraint.subject_clause.subject_variable
                comparisons.append(
                    Comparison(temporal_to_comparison_relations[temporal_constraint.temporal_operator], variable, '',
                               temporal_constraint.temporal_value, ''))
            return comparisons

    def __compile_quantified_maximum_quantity(self, quantified_maximum_quantity):
            return 0, quantified_maximum_quantity.value

    def __compile_quantified_minimum_quantity(self, quantified_maximum_quantity):
            return quantified_maximum_quantity.value, None

    def __compile_quantified_exact_quantity(self, quantified_exact_quantity):
        return quantified_exact_quantity.quantity, quantified_exact_quantity.quantity

    def __compile_quantified_range_clause(self, quantified_range_quantity):
        return quantified_range_quantity.quantified_range_lhs, quantified_range_quantity.quantified_range_rhs

    def __compile_cardinality(self, cardinality):
        """
        Coordinator method to compile cardinality
        @param cardinality:
        @return:
        """
        if type(cardinality.clause) == QuantifiedMaximumQuantity:
            return self.__compile_quantified_maximum_quantity(cardinality.clause)
        elif type(cardinality.clause) == QuantifiedExactQuantity:
            return self.__compile_quantified_exact_quantity(cardinality.clause)
        elif type(cardinality.clause) == QuantifiedRangeClause:
            return self.__compile_quantified_range_clause(cardinality.clause)
        elif type(cardinality.clause) == QuantifiedMinimumQuantity:
            return self.__compile_quantified_minimum_quantity(cardinality.clause)

    def initialize_atom_from_signature(self, name):
        atom = Atom(name, dict())
        for elem in self.__get_signature(name).primary_key:
            if type(elem) == Signature:
                atom.atom_parameters[elem.subject] = [self.initialize_atom_from_signature(elem.subject)]
            else:
                atom.atom_parameters[elem] = ['_']
        return atom

    def __compile_wheneverThen_clause(self, wheneverThen_clause):
        body: list[Atom] = [] # list of atoms in the rule body
        comparisons = [] # list of comparisons in the rule body
        for clause in wheneverThen_clause.wheneverClause:
            atom, comparison = self.init_atom_from_subject_clause(clause.subject, body)
            comparisons += comparison
            if clause.temporal_constraint:
                comparisons += self.temporal_constraint(atom, clause.temporal_constraint)
            body.append(atom)
        then_clause = wheneverThen_clause.thenClause
        head_atoms = []
        for then_body_clause in then_clause.then_body:
            condition: list[Atom] = []  # condition atoms in the head of the choice rule
            condition_comparisons = []
            for object_clause in then_body_clause.objects:
                atom, comparison = self.init_atom_from_object_clause(object_clause)
                comparisons += comparison
                condition.append(atom)
            verb_name = f'{then_body_clause.verb.name} {then_body_clause.verb.preposition}'.strip()
            if not self.__get_atom_from_signature_subject(verb_name):
                head_atom = Atom(verb_name, dict())
                for parameter in then_body_clause.verb.parameters:
                    if parameter.variable:
                        label_found = False
                        for atom in body:
                            if atom.label == parameter.variable and atom.atom_name == parameter.name:
                                label_found = True
                                for parameterkey, parametervalue in atom.atom_parameters.items():
                                    if parametervalue[0] != '_':
                                        if type(parametervalue[0]) == Atom:
                                            for parameterkey1, parametervalue1 in parametervalue[0].atom_parameters.items():
                                                atom_to_parameter = self.initialize_atom_from_signature(parameter.name)
                                                head_atom.atom_parameters[parameter.name] = [atom_to_parameter]
                                                head_atom.atom_parameters[parameter.name][0].atom_parameters[parameterkey][
                                                    0].set_parameter_variable(parameterkey1,
                                                                              parametervalue1[0])
                                        else:
                                            if(self.__get_atom_from_signature_subject(parameter.name)):
                                                head_atom.atom_parameters[parameter.name] = [self.__get_atom_from_signature_subject(parameter.name)] if not parameter.name in list(head_atom.atom_parameters.keys()) else head_atom.atom_parameters[parameter.name]
                                                head_atom.atom_parameters[parameter.name][0].set_parameter_variable(parameterkey,
                                                                                                                    parametervalue[0])
                                            else:
                                                head_atom.set_parameter_variable(parameterkey, parametervalue[0], newDefinition=True)
                        if not label_found:
                            if (self.__get_atom_from_signature_subject(parameter.name)):
                                atom_to_parameter = self.initialize_atom_from_signature(parameter.name)
                                head_atom.atom_parameters[parameter.name] = [atom_to_parameter]
                                head_atom.set_parameter_variable(parameter.name, parameter.variable)
                            else:
                                head_atom.set_parameter_variable(parameter.name, parameter.variable, newDefinition=True)
                for atom in condition:
                    self.link_two_atoms(head_atom, atom, newDefinition=True)
                    # for parameterkey, parametervalue in atom.atom_parameters.items():
                    #     if parametervalue[0] != '_' and parameterkey in list(
                    #             head_atom.atom_parameters.keys()) and head_atom.get_parameter_value(parameterkey) == '_':
                    #         head_atom.set_parameter_variable(parameterkey, parametervalue[0], newDefinition=True)
                if then_body_clause.verb.ordering:
                    ordering = then_body_clause.verb.ordering
                    if ordering.parameter == 'step':
                        temporal_concept_name = self.step_temporal_concepts[0].name
                        for atom in body:
                            if temporal_concept_name in list(atom.atom_parameters.keys()):
                                value = atom.get_parameter_value(temporal_concept_name)
                                if ordering.shift_operator == "the next":
                                    head_atom.set_parameter_variable(temporal_concept_name, f'{value}+1', newDefinition=True)
                                else:
                                    head_atom.set_parameter_variable(temporal_concept_name, value, newDefinition=True)
                if then_clause.subject.subject_name.isupper():
                    for atom in body:
                        if atom.label == then_clause.subject.subject_name:
                            # if (atom.atom_name in list(head_atom.atom_parameters.keys()) and type(head_atom.atom_parameters[atom.atom_name][0]) == Atom):
                            #     self.link_two_atoms(head_atom.atom_parameters[atom.atom_name][0], atom, newDefinition=True)
                            # else:
                            head_atom.atom_parameters[atom.atom_name] = [self.initialize_atom_from_signature(atom.atom_name)]
                            self.link_two_atoms(head_atom.atom_parameters[atom.atom_name][0], atom, newDefinition=True)
                self.decl_signatures.append(head_atom.compute_signature())
                head_atoms.append([head_atom, Conjunction(condition + condition_comparisons)])
            else:
                head_atom = self.__get_atom_from_signature_subject(f'{then_body_clause.verb.name} {then_body_clause.verb.preposition}'.strip())
                for parameter in then_body_clause.verb.parameters:
                    if parameter.variable:
                        label_found = False
                        for atom in body:
                            if atom.label == parameter.variable and atom.atom_name == parameter.name:
                                label_found = True
                                for parameterkey, parametervalue in atom.atom_parameters.items():
                                    if parametervalue[0] != '_':
                                        if type(parametervalue[0]) == Atom:
                                            for parameterkey1, parametervalue1 in parametervalue[0].atom_parameters.items():
                                                head_atom.atom_parameters[parameter.name][0].atom_parameters[parameterkey][
                                                    0].set_parameter_variable(parameterkey1,
                                                                              parametervalue1[0])
                                        else:
                                            if (type(head_atom.atom_parameters[parameter.name][0]) == Atom):
                                                head_atom.atom_parameters[parameter.name][0].set_parameter_variable(
                                                    parameterkey,
                                                    parametervalue[0])
                                            else:
                                                head_atom.set_parameter_variable(parameterkey, parametervalue[0])
                        if not label_found:
                            head_atom.set_parameter_variable(parameter.name, parameter.variable)
                for atom in condition:
                    for parameterkey, parametervalue in atom.atom_parameters.items():
                        if parametervalue[0] != '_' and parameterkey in list(
                                head_atom.atom_parameters.keys()) and head_atom.get_parameter_value(parameterkey) == '_':
                            head_atom.set_parameter_variable(parameterkey, parametervalue[0])
                if then_body_clause.verb.ordering:
                    ordering = then_body_clause.verb.ordering
                    if ordering.parameter == 'step':
                        temporal_concept_name = self.step_temporal_concepts[0].name
                        for atom in body:
                            if temporal_concept_name in list(atom.atom_parameters.keys()):
                                value = atom.get_parameter_value(temporal_concept_name)
                                if ordering.shift_operator == "the next":
                                    head_atom.set_parameter_variable(temporal_concept_name, f'{value}+1')
                                else:
                                    head_atom.set_parameter_variable(temporal_concept_name, value)
                if then_clause.subject.subject_name.isupper():
                    for atom in body:
                        if atom.label == then_clause.subject.subject_name:
                            if (atom.atom_name in list(head_atom.atom_parameters.keys()) and type(
                                    head_atom.atom_parameters[atom.atom_name][0]) == Atom):
                                self.link_two_atoms(head_atom.atom_parameters[atom.atom_name][0], atom)
                            else:
                                self.link_two_atoms(head_atom, atom)
                head_atoms.append([head_atom, Conjunction(condition + condition_comparisons)])
            duration_rules = ''
            if then_body_clause.duration:
                subject = None
                for atom in body:
                    if [value for key, value in atom.atom_parameters.items() if value[0] == then_body_clause.duration.value]:
                        subject = atom
                if subject:
                    duration_rules += self.__compile_duration_clause(body, [head_atom], then_body_clause.duration,
                                                                     then_body_clause.objects)
                else:
                    raise Exception(f'{then_body_clause.duration.value} {then_body_clause.duration.parameter.name} not defined.')

        rule_body: Conjunction = Conjunction(body + comparisons)
        rule_head = None
        if len(head_atoms) > 1:
            if [x for x in head_atoms if len(x[1].body) > 0]:
                objects = dict()
                for head_atom in head_atoms:
                    if len(head_atom[1].body):
                        objects[head_atom[0].atom_name] = head_atom[1]
                rule_head: ComplexDisjunction = ComplexDisjunction(head_atoms, objects)
            else:
                disjunction = [x[0] for x in head_atoms]
                rule_head: SimpleDisjunction = SimpleDisjunction(disjunction)
        else:
            if (then_clause.assignment_verb.value == "can"):
                quantified_range_lhs, quantified_range_rhs = self.__compile_cardinality(then_clause.cardinality)
                rule_head = ShortDisjunction(quantified_range_lhs, quantified_range_rhs, {'lower': False, 'upper': False},
                                            head_atoms[0][0], head_atoms[0][1])
            else:
                rule_head = Conjunction([head_atoms[0][0]])
        rule: Rule = Rule(head=rule_head, body=rule_body)
        return str(rule) + duration_rules

    # define the structure of an atom
    def __compile_domain_definition(self, clause: DomainDefinition):
        subject_in_clause: Subject = Subject(clause.subject)
        parameters = []
        primary_key = []
        for parameter in clause.parameters:
            try:
                signature = self.__get_signature(parameter.name)
                signature = Signature(signature.subject, signature.object_list, primary_key=signature.primary_key)
                if (signature.primary_key):
                    signature.object_list = signature.primary_key
                parameters.append(signature)
            except:
                parameters.append(parameter.name)
        for parameter in clause.primary_key_parameters:
            try:
                signature = self.__get_signature(parameter.name)
                signature = Signature(signature.subject, signature.object_list, primary_key=signature.primary_key)
                if (signature.primary_key):
                    signature.object_list = signature.primary_key
                primary_key.append(signature)
            except:
                primary_key.append(parameter.name)
        self.decl_signatures.append(
            Signature(subject_in_clause.name, primary_key + parameters, primary_key=primary_key))

    # The object is the atom defined in the domain definition
    # The subject is a new instance of the object
    def __compile_fact_definition(self, clause: FactDefinition):
        subject = clause.subject.subject_name
        parameters = clause.subject.parameters
        atom: Atom = self.__get_atom_from_signature_subject(subject)
        for parameter in parameters:
            if type(parameter.variable) == str and parameter.variable.isalpha() and parameter.variable.islower() and not (parameter.variable in list(constant_definitions_dict.keys())):
                # set the value of the atom fields
                atom.set_parameter_variable(parameter.name, f'"{parameter.variable}"')
            else:
                atom.set_parameter_variable(parameter.name, parameter.variable)
        return str(Rule(head=atom, body=None))

    # CompoundedClause: ("A " | "An ") subject_clause (compounded_clause_range compounded_clause_granularity?)
    # Definition of an atom with a range compound as a definition
    def __compile_compounded_clause_range(self, clause: CompoundedClause):
        compiled_string: str = ''
        # "CompoundedClauseRange: goes from" range_lhs "to" range_rhs
        compounded_range: CompoundedClauseRange = clause.definition
        subject_in_clause: Subject = Subject(clause.subject)
        lhs = None
        try:
            lhs = int(compounded_range.compounded_range_lhs)
        except ValueError:
            lhs = constant_definitions_dict[compounded_range.compounded_range_lhs.lower()]
        rhs = None
        try:
            rhs = int(compounded_range.compounded_range_rhs)
        except ValueError:
            rhs = constant_definitions_dict[compounded_range.compounded_range_rhs.lower()]
        # define the atom with parameters
        atom: Atom = Atom(subject_in_clause.name,
                          {f'{subject_in_clause.name}': [f'{lhs}'
                                                         f'..{rhs}']})
        # compounded_clause_granularity:  "and is made of" object_clause ("that are made of" object_clause)*
        granularity_hierarchy: list[str] = []
        if clause.tail:
            for elem in clause.tail.pop().granularity_hierarchy:
                granularity_hierarchy.append(Object(elem).name)
        # append the signature of the new atom
        self.decl_signatures.append(Signature(subject_in_clause.name, [subject_in_clause.name], granularity_hierarchy,
                                              {'lower': int(lhs),
                                               'upper': int(rhs)}))
        compiled_string += str(Rule(head=atom, body=None))
        return compiled_string

    # CompoundedClause: ("A " | "An ") subject_clause (compounded_clause_match compounded_clause_granularity? compounded_clause_match_tail?)
    # Definition of an atom with a match compound as a definition
    def __compile_compounded_clause_match(self, clause: CompoundedClause):
        compiled_string: str = ''
        subject_in_clause: Subject = Subject(clause.subject)
        # CompoundedClauseMatch: "is one of" compounded_list
        compounded_match: CompoundedClauseMatch = clause.definition
        (lower, upper) = get_list_bounds(compounded_match.compounded_match_list)
        # CompoundedClauseMatchTail: "and has" object_clause ("that are equal to respectively" | "that is equal to respectively") compounded_list ("and also" object_clause ("that are equal to respectively" | "that is equal to respectively") compounded_list)*
        compounded_match_tail: list[CompoundedClauseMatchTail] = []
        # compounded_clause_granularity: "and is made of" object_clause ("that are made of" object_clause)*
        granularity_hierarchy: list[str] = []
        if clause.tail:
            compounded_match_tail: list[CompoundedClauseMatchTail] = [tail_elem for tail_elem in clause.tail
                                                                      if type(tail_elem) != CompoundedClauseGranularity]
            granularity_hierarchy_list: list[CompoundedClauseGranularity] = [tail_elem for tail_elem in clause.tail
                                                                             if type(tail_elem) ==
                                                                             CompoundedClauseGranularity]
            if granularity_hierarchy_list:
                for elem in clause.tail.pop(0).granularity_hierarchy:
                    granularity_hierarchy.append(Object(elem).name)
        # for each element in the match list define a new atom
        for (i, elem) in enumerate(clause.definition.compounded_match_list):
            def_value: str = f'"{clause.definition.compounded_match_list[i]}"' if not \
                clause.definition.compounded_match_list[i].isdigit() else clause.definition.compounded_match_list[i]
            # if the match list element is not a digit, define a new atom and add the match list in the global constants with the order value 
            if not clause.definition.compounded_match_list[i].isdigit():
                atom: Atom = Atom(f'{subject_in_clause.name}',
                                  {f'{subject_in_clause.name}': [f'{def_value}']}, i)
                alphabetic_constants_set.add(clause.definition.compounded_match_list[i])
                ordered_constant_dict[clause.definition.compounded_match_list[i]] = i + 1
            else:
                atom: Atom = Atom(f'{subject_in_clause.name}',
                                  {f'{subject_in_clause.name}': [f'{def_value}']})
            # if has a tail add the elements to the atom parameters
            if compounded_match_tail:
                for tail_elem in compounded_match_tail:
                    tail_value: str = f'"{tail_elem.definition_list[i]}"' if not \
                        tail_elem.definition_list[i].isdigit() else tail_elem.definition_list[i]
                    atom.set_parameter_variable(f'{Object(tail_elem.subject).name}',
                                                f'{tail_value}', newDefinition=True)
                    if not tail_elem.definition_list[i].isdigit():
                        alphabetic_constants_set.add(tail_elem.definition_list[i])
                        ordered_constant_dict[tail_elem.definition_list[i]] = i + 1
            compiled_string += str(Rule(head=atom, body=None))
        # append the signature of the new atom
        self.decl_signatures.append(
            Signature(subject_in_clause.name, [subject_in_clause.name] +
                      [Object(tail_elem.subject).name for tail_elem in compounded_match_tail],
                      granularity_hierarchy,
                      {'lower': lower,
                       'upper': upper},
                      True))
        return compiled_string

    # EnumerativeDefinitionClause: subject_clause CNL_COPULA? (verb_name | verb_name_with_preposition) (subject_clause ("and" subject_clause)*)? ("when" when_part)? (where_clause)?
    def __compile_enumerative_definition_clause(self, clause: EnumerativeDefinitionClause):
        compiled_string: str = ''
        subject_in_clause: Subject = Subject(clause.subject)
        verb_name: str = " ".join([substr.strip().removesuffix("s") for substr in clause.verb_name.split(' ')]).lower()

        objects_list: list[str] = [subject_in_clause.name if not subject_in_clause.variable.startswith('X_')
                                   else verb_name]
        objects_values: list[str] = [self.__make_substitution_value(subject_in_clause.variable)
                                     if not subject_in_clause.variable.startswith('X_') else
                                     self.__make_substitution_value(subject_in_clause.name)]
        for def_object in clause.object_list:
            objects_list.append(self.__make_substitution_value(Subject(def_object).name))
            objects_values.append(self.__make_substitution_value(Subject(def_object).variable))

        atom: Atom = Atom(verb_name, dict())
        for i, object_name in enumerate(objects_list):
            object_value = f'"{objects_values[i]}"' if objects_values[i].isalpha() and objects_values[i].islower() else objects_values[i]
            atom.set_parameter_variable(object_name, object_value, newDefinition=True)
        self.decl_signatures.append(Signature(verb_name, objects_list))

        # WhereClause: "," " "* "where" (condition_clause | condition_match_group) ("and" condition_clause)*
        where_in_clause: WhereClause = clause.where_clause
        when_in_clause: list = clause.when_part
        head_result = []
        body_result = []
        conjunction: Conjunction | None = None
        if when_in_clause:
            compiled_clauses = []
            block_memory: ClauseBlockMemory = ClauseBlockMemory()
            for clause in when_in_clause:
                compiled_clause = self.__compile_simple_clause(clause, block_memory)
                compiled_clauses.append(compiled_clause)
                block_memory.flush_all(on=compiled_clauses)

            # conjunction = Conjunction(compiled_clauses)
            conjunction = Conjunction(compiled_clauses)
            maybe_unsafe_atoms: list[Atom] = conjunction.extract_maybe_unsafe_atoms()
            safe_variables: set[str] = conjunction.extract_safe_variables()
            safety_atoms_to_add: list[Atom] = []

            for atom in maybe_unsafe_atoms:
                for parameter in atom.atom_parameters.keys():
                    for variable in atom.atom_parameters[parameter]:
                        if (match := re.search(r'(X(_[a-z0-9]+){5}|[A-Z]([A-Z0-9a-z_])*)', variable)) \
                                is not None and match.group(1) not in safe_variables:
                            safety_atom: Atom | None = None
                            for old_atom in safety_atoms_to_add:
                                if old_atom.atom_name == parameter:
                                    safety_atom = old_atom
                            if safety_atom is None:
                                safety_atom = self.__get_atom_from_signature_subject(parameter)
                                safety_atoms_to_add.append(safety_atom)
                            safety_atom.set_parameter_variable(parameter, variable, force=True)

            conjunction.body += safety_atoms_to_add

        if where_in_clause:
            for elem in where_in_clause.conditions:
                if type(elem) is not ConditionMatchGroup:
                    # ConditionBoundClause: "between" object_name "and" object_name
                    if type(elem.condition_clause) is ConditionBoundClause:
                        bounded_variable = BoundedVariable(elem.condition_variable,
                                                           {'lower': elem.condition_clause.bound_lower,
                                                            'upper': elem.condition_clause.bound_upper})
                        conjunction.body.append(bounded_variable)
                    # ConditionComparisonClause: condition_negation? condition_operator condition_expression
                    elif type(elem.condition_clause) is ConditionComparisonClause:
                        comparison = None
                        if type(elem.condition_clause.condition_expression[0]) is not ConditionOperation:
                            comparison = Comparison(elem.condition_clause.condition_operator,
                                                    elem.condition_variable, '',
                                                    elem.condition_clause.condition_expression[0], '')
                        else:
                            comparison = Comparison('equal to',
                                                    elem.condition_variable,
                                                    '',
                                                    Operation(
                                                        elem.condition_clause.condition_expression[0].expression_lhs,
                                                        elem.condition_clause.condition_expression[0]
                                                        .expression_operator.operator,
                                                        elem.condition_clause.condition_expression[0].expression_rhs,
                                                        None,
                                                        elem.condition_clause.condition_expression[0]
                                                        .expression_operator.absolute_value,
                                                    ), '')
                        conjunction.body.append(comparison)
            for elem in where_in_clause.conditions:
                # ConditionMatchGroup: condition_match_clause ("and" condition_match_clause)*
                # condition_match_clause: variable CNL_COPULA "one of" "respectively"* compounded_list
                if type(elem) is ConditionMatchGroup:
                    if not when_in_clause:
                        for i in range(elem.group_list[0].list_len):
                            atom_copy: Atom = atom.copy()
                            for x in elem.group_list:
                                value: str = self.__make_substitution_value(x.condition_list[i])
                                atom_copy.set_variable_value(x.condition_variable, value)
                            head_result.append(atom_copy)
                    else:
                        for i in range(elem.group_list[0].list_len):
                            conjunction_copy: Conjunction = conjunction.copy()
                            for x in elem.group_list:
                                value: str = self.__make_substitution_value(x.condition_list[i])
                                conjunction_copy.set_variable_value(x.condition_variable, value)
                            body_result.append(conjunction_copy)
        if not head_result:
            head_result.append(atom)
        if not body_result:
            body_result.append(conjunction)

        for head_elem in head_result:
            for body_elem in body_result:
                compiled_string += str(Rule(head=head_elem, body=body_elem))

        return compiled_string

    def __compile_constant_definition_clause(self, clause: ConstantDefinitionClause):
        # self.decl_signatures.append(Signature(clause.subject, [clause.subject]))
        constant_definitions_dict[clause.subject.lower()] = clause.constant.lower()

    def __compile_quantified_choice_disjunction_clause(self, clause: QuantifiedChoiceClause):
        subject_in_clause: Subject = Subject(clause.subject_clause)
        verb_names = [f'{clause.verb_name.name} {clause.verb_name.preposition}'.strip()] #first verb
        verb_names += \
            [f'{x.name} {x.preposition}'.strip() for x in clause.object_clause.objects if type(x) == VerbName]
        for i,verb in enumerate(verb_names):
            verb_names[i] = " ".join(
                [substr.strip().removesuffix("s") for substr in verb.split(' ')]).lower()
        subject_in_clause_atom: Atom = self.__get_atom_from_signature_subject(subject_in_clause.name)
        # set a variable for each parameter defined in input
        # for parameter in clause.parameters:
        #     variable = f'X_{str(uuid4()).replace("-", "_")}' if parameter.variable == '' else parameter.variable
        #     subject_in_clause_atom.set_parameter_variable(parameter.name, variable)
        self.set_parameter_list(subject_in_clause_atom, clause.subject_clause.parameters)
        objects_in_foreach: list[Object] = []
        # foreach_clause: "for each" object_clause ("and" object_clause)*
        if clause.foreach_clause:
            for foreach_object in clause.foreach_clause.objects:
                objects_in_foreach.append(Object(foreach_object))
        clause_foreach_atoms: list[Atom] = [self.__get_atom_from_signature_subject(foreach_object.name)
                                            .set_parameter_variable(foreach_object.name,
                                                                    foreach_object.variable) for
                                            foreach_object in objects_in_foreach]
        head_atoms = []
        for verb in verb_names:
            if self.__get_atom_from_signature_subject(verb):
                head_atoms.append([self.__get_atom_from_signature_subject(verb), False])
            else:
                head_atoms.append([Atom(verb, dict()), True])
        if clause.verb_name.parameters:
            self.set_parameter_list(head_atoms[0][0], clause.verb_name.parameters, newDefinition=head_atoms[0][1])
        for i, head_atom in enumerate(head_atoms[1:]):
            if hasattr(clause.object_clause.objects[i], 'parameters'):
                self.set_parameter_list(head_atom[0], clause.object_clause.objects[i].parameters, newDefinition=head_atom[1])
        for x, y in [(elem.atom_name, elem.atom_parameters[elem.atom_name]) for elem in clause_foreach_atoms]:
            for z in y:
                for atom in head_atoms:
                    atom[0].set_parameter_variable(x, z, force=True, newDefinition=atom[1])
        objects = dict()
        if clause.object_clause.objects and [elem for elem in clause.object_clause.objects if
                                             type(elem) == ObjectClause]:
            for j, atom in enumerate(head_atoms):
                objects[atom[0].atom_name] = []
                atoms = []
                variable = f'X_{str(uuid4()).replace("-", "_")}'
                if j == 0:
                    parameter_name = list(self.__get_atom_from_signature_subject(
                        clause.object_clause.objects[0].object_name).atom_parameters.keys())[0]
                    atoms.append(self.__get_atom_from_signature_subject(clause.object_clause.objects[0].object_name) \
                                 .set_parameter_variable(parameter_name, variable, newDefinition=atom[1]))
                    atom[0].set_parameter_variable(parameter_name, variable, force=True, newDefinition=atom[1])
                else:
                    for i, object in enumerate(clause.object_clause.objects):
                        if type(object) == VerbName and (
                                atom[0].atom_name == f'{object.name}_{object.preposition}' or atom[0].atom_name == f'{object.name}'):
                            parameter_name = list(self.__get_atom_from_signature_subject(
                                clause.object_clause.objects[i + 1].object_name).atom_parameters.keys())[0]
                            atoms.append(
                                self.__get_atom_from_signature_subject(clause.object_clause.objects[i + 1].object_name) \
                                    .set_parameter_variable(parameter_name, variable, newDefinition=atom[1]))
                            atom[0].set_parameter_variable(parameter_name, variable,force=True, newDefinition=atom[1])
                objects[atom.atom_name] = atoms
        duration_rules = ''
        if clause.duration_clause:
            atom_list = []
            for atom in head_atoms:
                atom_list.append(atom[0])
            duration_rules += self.__compile_duration_clause([subject_in_clause_atom], atom_list,
                                                             clause.duration_clause)

        rule_body: Conjunction = Conjunction([subject_in_clause_atom] + clause_foreach_atoms)
        if not clause.verb_name.parameters:
            for head_atom in head_atoms:
                self.link_two_atoms(head_atom[0], subject_in_clause_atom, newDefinition=head_atom[1])
        for head_atom in head_atoms:
            if head_atom[1]:
                self.decl_signatures.append(Signature(head_atom[0].atom_name, head_atom[0].atom_parameters.keys()))
        if clause.object_clause.objects and [elem for elem in clause.object_clause.objects if
                                             type(elem) == ObjectClause]:
            atom_list = [x[0] for x in head_atoms]
            rule_head: ComplexDisjunction = ComplexDisjunction(atom_list, objects)
        else:
            atom_list = [x[0] for x in head_atoms]
            rule_head: SimpleDisjunction = SimpleDisjunction(atom_list)
        rule: Rule = Rule(head=rule_head, body=rule_body)
        return str(rule) + duration_rules

    # define the temporal duration of a task
    def __compile_duration_clause(self, body: list[Atom], head_atoms: list[Atom], duration_clause: DurationClause,
                                  object_clause: ObjectClause = []):
        rules = ''
        value = duration_clause.value
        flag = True
        if flag:
            for atom in head_atoms:
                head = atom.copy()
                support_atom = Atom('support', head.atom_parameters)
                for key in list(atom.atom_parameters.keys()):
                    # TODO not key in object_clause not working
                    if self.is_temporal_concept(key) and not [x for x in object_clause if key == x.object_name]:
                        del atom.atom_parameters[key]
                rule: Rule = Rule(head=head, body=Conjunction([support_atom, atom]))
                rules += str(rule)
                # Define support atom
                head_param = head.atom_parameters.get(duration_clause.parameter.name.removesuffix("s"))[0]
                if type(head_param) == Atom:
                    support_param = f'{head_param.set_parameter_variable(head_param.atom_name, head_param.atom_parameters[head_param.atom_name][0] + ".." + head_param.atom_parameters[head_param.atom_name][0] + "+" + value + "-1", force=True)}'
                else:
                    support_param = f'{head_param}..{head_param}+{value}'
                support_atom.set_parameter_variable(duration_clause.parameter.name.removesuffix("s"), support_param,
                                                    force=True)
                rule_body: Conjunction = Conjunction([atom] + body)
                rule: Rule = Rule(head=support_atom, body=rule_body)
                rules += str(rule)
            return rules
        else:
            for atom in head_atoms:
                head = atom.copy()
                head_param = head.atom_parameters.get(duration_clause.parameter.name.removesuffix("s"))[0]
                if type(head_param) == Atom:
                    head_param = f'{head_param.set_parameter_variable(head_param.atom_name, head_param.atom_parameters[head_param.atom_name][0] + ".." + head_param.atom_parameters[head_param.atom_name][0] + "+" + value + "-1", force=True)}'
                else:
                    head_param = f'{head_param}..{head_param}+{value}'
                head.set_parameter_variable(duration_clause.parameter.name.removesuffix("s"), head_param, force=True)
                rule_body: Conjunction = Conjunction([atom] + body)
                rule: Rule = Rule(head=head, body=rule_body)
                rules += str(rule)
            return rules

    # QuantifiedChoiceClause: quantifier subject_clause "can" CNL_COPULA? (verb_name | verb_name_with_preposition) (quantified_exact_quantity_clause | quantified_range_clause)? quantified_object_clause? foreach_clause?
    def __compile_quantified_choice_clause(self, clause: QuantifiedChoiceClause):
        if (type(clause.object_clause) == DisjunctionClause):
            return self.__compile_quantified_choice_disjunction_clause(clause)
        old_subject_variable: str | None = None
        subject_in_clause: Subject = Subject(clause.subject_clause)
        verb_name: str = f'{clause.verb_name.name} {clause.verb_name.preposition}'.strip()
        objects_in_foreach: list[Object] = []
        # foreach_clause: "for each" object_clause ("and" object_clause)*
        if clause.foreach_clause:
            for foreach_object in clause.foreach_clause.objects:
                objects_in_foreach.append(Object(foreach_object))
        objects_in_body: list[Object] = []
        verb_atom_in_body: list[Atom] = []
        clause_verb_atom: Atom = Atom(verb_name, dict())
        if clause.object_clause:
            tmp = ""
            for body_object in clause.object_clause.objects:
                if type(body_object) is not SimpleClause:
                    objects_in_body.append(Object(body_object))
                else:
                    subject: Subject = Subject(body_object.subject)
                    verb: Verb = Verb(body_object.verb_clause)
                    verb_object: VerbObject = VerbObject(body_object.verb_clause.object_clause)
                    new_atom: Atom = self.__get_atom_from_signature_subject(verb.name)
                    new_atom.set_parameter_variable(verb_object.name, verb_object.variable)
                    new_atom.set_parameter_variable(subject.name, subject.variable)
                    verb_atom_in_body.append(new_atom)
                    clause_verb_atom.set_parameter_variable(verb_object.name, verb_object.variable, force=True, newDefinition=True)
                    old_subject_variable = subject_in_clause.variable
                    subject_in_clause.variable = subject.variable
                    tmp = verb_object.variable
        clause_subject_atom: Atom = self.__get_atom_from_signature_subject(subject_in_clause.name)
        # if no clause parameters just take the atom name as parameter and set the variable
        if not clause.parameters:
            clause_subject_atom.set_parameter_variable(subject_in_clause.name, subject_in_clause.variable)
        else:
            for parameter in clause.parameters:
                variable = f'X_{str(uuid4()).replace("-", "_")}' if parameter.variable == '' else parameter.variable
                clause_subject_atom.set_parameter_variable(parameter.name, variable)
            for parameter_definition in clause.parameters_definitions:
                clause_subject_atom.set_parameter_variable(parameter_definition.parameter_name,
                                                           parameter_definition.parameter_value)
        clause_foreach_atoms: list[Atom] = [self.__get_atom_from_signature_subject(foreach_object.name)
                                            .set_parameter_variable(foreach_object.name,
                                                                    foreach_object.variable) for
                                            foreach_object in objects_in_foreach]
        clause_object_variables: list[Atom] = [self.__get_atom_from_signature_subject(object_clause_elem.name)
        .set_parameter_variable(object_clause_elem.name, object_clause_elem.variable)
            for object_clause_elem in objects_in_body if type(object_clause_elem) is Object]
        clause_object_variables_conj: Conjunction = Conjunction(clause_object_variables)
        if not clause.parameters:
            # if no clause parameters just take the atom name as parameter and set the variable
            for x, y in [(clause_subject_atom.atom_name,
                          clause_subject_atom.atom_parameters[clause_subject_atom.atom_name])]:
                for z in y:
                    clause_verb_atom.set_parameter_variable(x, z, newDefinition=True)
        else:
            # Copy the parameters subject into the verb
            for parameters in [clause_subject_atom.atom_parameters]:
                for parameter_name in parameters:
                    if [x for x in clause.parameters if x.name == parameter_name]:
                        clause_verb_atom.set_parameter_variable(parameter_name, parameters.get(parameter_name)[0], newDefinition=True)
                    else:
                        for paramDef in clause.parameters_definitions:
                            if (parameter_name == paramDef.parameter_name):
                                clause_verb_atom.set_parameter_variable(parameter_name,
                                                                        parameters.get(parameter_name)[0], newDefinition=True)
        if old_subject_variable is not None:
            clause_subject_atom.set_parameter_variable(subject_in_clause.name, tmp, force=True)
            clause_verb_atom.set_parameter_variable(subject_in_clause.name, old_subject_variable, force=True)
        for x, y in [(elem.atom_name, elem.atom_parameters[elem.atom_name]) for elem in clause_foreach_atoms]:
            for z in y:
                clause_verb_atom.set_parameter_variable(x, z, newDefinition=True)
        for x, y in [(elem.atom_name, elem.atom_parameters[elem.atom_name]) for elem in
                     clause_object_variables]:
            for z in y:
                clause_verb_atom.set_parameter_variable(x, z, newDefinition=True)
        clause_object_variables += verb_atom_in_body

        duration_rules = ''
        if clause.duration_clause:
            duration_rules += self.__compile_duration_clause([clause_subject_atom], [clause_verb_atom],
                                                             clause.duration_clause)
        self.decl_signatures.append(Signature(verb_name,
                                              clause_verb_atom.atom_parameters.keys()))
        conjunction = [clause_subject_atom]
        rule_body: Conjunction = Conjunction(conjunction + clause_foreach_atoms)
        rule_head: ShortDisjunction = ShortDisjunction(clause.range.quantified_range_lhs,
                                                       clause.range.quantified_range_rhs,
                                                       {'lower': False, 'upper': False},
                                                       clause_verb_atom,
                                                       clause_object_variables_conj) if clause.range else \
            ShortDisjunction(None,
                             None,
                             {'lower': False, 'upper': False},
                             clause_verb_atom,
                             clause_object_variables_conj)
        rule: Rule = Rule(head=rule_head, body=rule_body)
        return str(rule) + duration_rules

    # link two atoms setting the same values to the keys with same name
    def link_two_atoms(self, atom1: Atom, atom2: Atom, newDefinition=False):
        atom_keys = self.__get_signature(' '.join(atom2.atom_name.split('_'))).primary_key
        for key in atom_keys:
            parameter_name = key if type(key) == str else key.subject
            if newDefinition:
                if self.__get_atom_from_signature_subject(parameter_name):
                    atom1.atom_parameters[parameter_name] = [self.initialize_atom_from_signature(parameter_name)]
            var = self.newVar()
            if type(atom2.atom_parameters[parameter_name][0]) == str and atom2.atom_parameters[parameter_name][
                0] != '_':
                var = atom2.atom_parameters[parameter_name][0]
                atom1.set_parameter_variable(parameter_name, var)
            elif type(atom2.atom_parameters[parameter_name][0]) == Atom and parameter_name in list(
                    atom1.atom_parameters.keys()) and type(atom1.atom_parameters[parameter_name][0]) == Atom:
                self.link_two_atoms(atom1.atom_parameters[parameter_name][0], atom2.atom_parameters[parameter_name][0])
            elif parameter_name in list(atom1.atom_parameters.keys()):
                atom1.set_parameter_variable(parameter_name, var)
                atom2.set_parameter_variable(parameter_name, var)

    def isTime(self, string):
        try:
            datetime.strptime(string, '%I:%M %p')
            return True
        except:
            return False

    def isDate(self, string):
        try:
            datetime.strptime(string, '%d/%m/%Y')
            return True
        except:
            return False

    def set_parameter_list(self, atom, parameters, newDefinition=False):
        """
        set a list of parameters to an atom
        @param atom: atom to set the parameters
        @param parameters: list of parameters
        @return comparisons:
        """
        comparisons = []
        for parameter in parameters:
            if type(parameter) == Parameter or type(parameter) == ParameterDefinition:
                atom.set_parameter_variable(parameter.name, parameter.variable, newDefinition=newDefinition)
            else:
                operator = parameter.expression_operator
                lhs = parameter.expression_lhs.variable
                rhs = parameter.expression_rhs
                comparisons.append(Comparison(operator, lhs, '', rhs, ''))
                atom.set_parameter_variable(parameter.expression_lhs.name, lhs)
        return comparisons

    # get the compatible atom with the ordering operator and set the appropriate value to the parameter
    def set_ordering_operator(self, item, body):
        ordering_operator = item[1]
        ordering_operator_parameter = self.step_temporal_concepts[0].name if ordering_operator[1] == 'step' else \
            ordering_operator[1]
        for atom_in_body in body:
            if atom_in_body.atom_name == item[0].atom_name and atom_in_body.label == item[0].label: continue
            if ordering_operator_parameter in list(atom_in_body.atom_parameters.keys()):
                value = atom_in_body.atom_parameters[ordering_operator_parameter][0] if type(
                    atom_in_body.atom_parameters[ordering_operator_parameter][0]) == str else \
                    list(atom_in_body.atom_parameters[ordering_operator_parameter][0].atom_parameters.values())[0][0]
                if ordering_operator[0] == 'previous':
                    item[0].set_parameter_variable(ordering_operator_parameter, value + '-1')
                    break
                else:
                    item[0].set_parameter_variable(ordering_operator_parameter, value + '+1')
                    break

    def is_temporal_concept(self, concept):
        for time in self.time_temporal_concepts:
            if time.name == concept: return True
        for date in self.date_temporal_concepts:
            if date.name == concept: return True
        for step in self.step_temporal_concepts:
            if step.name == concept: return True
        return False

    def __compile_temporal_ordering(self, atom, temporal_ordering, initialized_atom_list):
        """
        @param atom:
        @param temporal_ordering:
        @param initialized_atom_list: atoms initialized in the preposition
        @return:
        """
        incremental_value = '+1' if temporal_ordering.shift_operator == "the next" else '-1'
        if temporal_ordering.temporal_type == 'step':
            for parameter in list(atom.atom_parameters.keys()):
                for step in self.step_temporal_concepts:
                    if parameter == step.name:
                        atom.set_parameter_variable(parameter, f'{temporal_ordering.parameter}{incremental_value}')
        elif temporal_ordering.temporal_type == 'day':
            for parameter in list(atom.atom_parameters.keys()):
                for date in self.date_temporal_concepts:
                    if parameter == date.name:
                        atom.set_parameter_variable(parameter, f'{temporal_ordering.parameter}{incremental_value}')
        elif temporal_ordering.temporal_type == 'minutes':
            for parameter in list(atom.atom_parameters.keys()):
                for time in self.time_temporal_concepts:
                    if parameter == time.name:
                        atom.set_parameter_variable(parameter, f'{temporal_ordering.parameter}{incremental_value}')


    def __compile_strong_constraint_clause(self, constraint: StrongConstraintClause):
        if constraint.whenever_clause or (type(constraint.clauses) == list and [x for x in constraint.clauses if type(x) == SuchThat]):
            body: list[Atom] = []
            clauses = []
            to_set_ordering_operator = []
            if constraint.whenever_clause:
                for clause in constraint.whenever_clause:
                    atom = self.__get_atom_from_signature_subject(clause.subject.subject_name)
                    if clause.verb_negation:
                        atom.negated = True
                    if clause.subject.subject_variable:
                        atom.label = clause.subject.subject_variable
                    if clause.subject.parameters:
                        for parameter in clause.subject.parameters:
                            if type(parameter) == ConditionOperation:
                                variable = self.newVar() if not parameter.expression_lhs.variable else parameter.expression_lhs.variable
                                atom.set_parameter_variable(parameter.expression_lhs.name, variable)
                                rhs_name = ''
                                if type(parameter.expression_rhs) == str:
                                    for atom in body + [atom]:
                                        for name, var in atom.atom_parameters.items():
                                            if var[0] == parameter.expression_rhs:
                                                rhs_name = name
                                    clauses.append(Comparison(parameter.expression_operator, variable, parameter.expression_lhs.name,
                                                              parameter.expression_rhs, rhs_name))
                                else:
                                    clauses.append(Comparison(parameter.expression_operator, variable, parameter.expression_lhs.name,
                                                              parameter.expression_rhs.variable, rhs_name))
                            elif type(parameter) == TemporalOrdering:
                                self.__compile_temporal_ordering(atom, parameter, body)
                            else:
                                parameter_is_an_atom = False
                                for atom_body in body:
                                    if type(atom_body) == Atom and atom_body.atom_name == parameter.name and atom_body.label == parameter.variable:
                                        self.link_two_atoms(atom.atom_parameters[parameter.name][0], atom_body)
                                        parameter_is_an_atom = True
                                if not parameter_is_an_atom and parameter.name in list(atom.atom_parameters.keys()):
                                    atom.set_parameter_variable(parameter.name, parameter.variable)
                    else:
                        atom.initializeVariables(self.__get_signature(atom.atom_name),
                                                 self.is_temporal_concept(atom.atom_name))
                    if clause.temporal_constraint:
                        comparison = self.temporal_constraint(atom, clause.temporal_constraint)
                        clauses += comparison
                    if clause.subject.subject_ordering:
                        to_set_ordering_operator.append([atom, clause.subject.subject_ordering])
                    body.append(atom)
            factors = []
            if constraint.condition_clause:
                comparison = None
                condition_clause = constraint.condition_clause[0]
                if type(condition_clause.condition_variable) == ConditionOperation:
                    if type(condition_clause.condition_variable.expression_lhs[0]) == str:
                        factors.append({'name': condition_clause.condition_variable.expression_lhs[0],
                                        'variable': condition_clause.condition_variable.expression_lhs})
                    else:
                        variable = self.newVar()
                        name = ''
                        for atom in body:
                            if atom.atom_name == condition_clause.condition_variable.expression_lhs[1].subject_name:
                                if atom.label and condition_clause.condition_variable.expression_lhs[
                                    1].subject_variable and atom.label == \
                                        condition_clause.condition_variable.expression_lhs[1].subject_variable:
                                    if atom.atom_parameters[condition_clause.condition_variable.expression_lhs[0].name][
                                        0] == '_':
                                        atom.set_parameter_variable(
                                            condition_clause.condition_variable.expression_lhs[0].name, variable)
                                        name = condition_clause.condition_variable.expression_lhs[0].name
                                    else:
                                        variable = atom.get_parameter_value(
                                            condition_clause.condition_variable.expression_lhs[0].name)
                                        name = condition_clause.condition_variable.expression_lhs[0].name
                                        # variable = atom.atom_parameters[
                                        # condition_clause.condition_variable.expression_lhs[0].name][0]
                        factors.append({'name': name, 'variable': variable})

                    if type(condition_clause.condition_variable.expression_rhs[0]) == str:
                        if not condition_clause.condition_variable.expression_rhs[0] in list(constant_definitions_dict.keys()):
                            raise Exception(f'Constant "{condition_clause.condition_variable.expression_rhs[0]}" not declared.')
                        factors.append({'name': condition_clause.condition_variable.expression_rhs[0], 'variable': condition_clause.condition_variable.expression_rhs[0]})
                    else:
                        variable = self.newVar()
                        name = ''
                        for atom in body:
                            if atom.atom_name == condition_clause.condition_variable.expression_rhs[
                                1].subject_name:
                                if atom.label and condition_clause.condition_variable.expression_rhs[
                                    1].subject_variable and atom.label == \
                                        condition_clause.condition_variable.expression_rhs[
                                            1].subject_variable:
                                    atom.set_parameter_variable(
                                        condition_clause.condition_variable.expression_rhs[0].name, variable)
                                    name = condition_clause.condition_variable.expression_rhs[0].name
                        factors.append(
                            {'name': condition_clause.condition_variable.expression_rhs[0].name, 'variable': variable})

                    if condition_clause.condition_variable.more_expression_factors:
                        for factor in condition_clause.condition_variable.more_expression_factors:
                            variable = self.newVar()
                            name = ''
                            for atom in body:
                                if atom.atom_name == factor[1].subject_name:
                                    if atom.label and factor[1].subject_variable and atom.label == factor[
                                        1].subject_variable:
                                        atom.set_parameter_variable(factor[0].name, variable)
                                        name = factor[0].name
                            factors.append({'name': name, 'variable': variable})

                    variable = self.newVar()
                    name = ''
                    if type(condition_clause.condition_clause.condition_expression[0]) == str:
                        name = condition_clause.condition_clause.condition_expression[0]
                        variable = condition_clause.condition_clause.condition_expression[0]
                    else:
                        for atom in body:
                            if atom.atom_name == condition_clause.condition_clause.condition_expression[0][
                                1].subject_name:
                                if atom.label and condition_clause.condition_clause.condition_expression[0][
                                    1].subject_variable and atom.label == \
                                        condition_clause.condition_clause.condition_expression[0][
                                            1].subject_variable:
                                    if atom.atom_parameters[
                                        condition_clause.condition_clause.condition_expression[0][0].name][
                                        0] == '_':
                                        atom.set_parameter_variable(
                                            condition_clause.condition_clause.condition_expression[0][0].name,
                                            variable)
                                        name = condition_clause.condition_clause.condition_expression[0][0].name
                                    else:
                                        variable = atom.atom_parameters[
                                            condition_clause.condition_clause.condition_expression[0][0].name][0]
                                        name = condition_clause.condition_clause.condition_expression[0][0].name
                                        if type(variable) == Atom:
                                            name = list(variable.atom_parameters.keys())[0]
                                            variable = variable.atom_parameters[list(variable.atom_parameters.keys())[0]][0]
                    # factors.append(variable)
                    if condition_clause.condition_clause.condition_operator in comparison_relations:
                        lhs_operator = factors[0]['variable']
                        lhs_operator_name = factors[0]['name']
                        rhs_operator = factors[1]['variable']
                        rhs_operator_name = factors[1]['name']
                        condition_lhs_modulo = 0
                        if condition_clause.condition_variable.expression_operator.modulo:
                            condition_lhs_modulo = condition_clause.condition_variable.expression_operator.modulo
                        condition_rhs_modulo = 0
                        if len(condition_clause.condition_clause.condition_expression[0]) == 3:
                            condition_rhs_modulo = condition_clause.condition_clause.condition_expression[0][2]
                        factors.pop(0)
                        factors.pop(0)
                        #remaining factors names
                        factors_names = [x['name'] for x in factors]
                        factors_variables = [x['variable'] for x in factors]
                        comparison = Comparison(condition_clause.condition_clause.condition_operator,
                                                variable, name,
                                                Operation(lhs_operator,
                                                          constraint.condition_clause[
                                                              0].condition_variable.expression_operator.operator,
                                                          rhs_operator,
                                                          None,
                                                          constraint.condition_clause[
                                                              0].condition_variable.expression_operator.absolute_value,
                                                          factors_variables
                                                          ), lhs_operator_name + rhs_operator_name + ' '.join(factors_names), condition_lhs_modulo, condition_rhs_modulo, constraint.positive)
                    else:
                        lhs_operator = factors[0]['variable']
                        lhs_operator_name = factors[0]['name']
                        rhs_operator = factors[1]['variable']
                        rhs_operator_name = factors[1]['name']
                        factors.pop(0)
                        factors.pop(0)
                        # remaining factors names
                        factors_names = [x['name'] for x in factors]
                        factors_variables = [x['variable'] for x in factors]
                        comparison = Comparison('equal to',
                                                variable, '',
                                                Operation(lhs_operator,
                                                          constraint.condition_clause[
                                                              0].condition_variable.expression_operator.operator,
                                                          rhs_operator,
                                                          None,
                                                          constraint.condition_clause[
                                                              0].condition_variable.expression_operator.absolute_value,
                                                          factors_variables
                                                          ), lhs_operator_name + ' ' + rhs_operator_name + ' '.join(factors_names), condition_lhs_modulo, condition_rhs_modulo, constraint.positive)
                elif type(condition_clause.condition_variable) == str:
                    comparison = Comparison(condition_clause.condition_clause.condition_operator,
                                            condition_clause.condition_variable, '',
                                            condition_clause.condition_clause.condition_expression[0], '', '', '', constraint.positive)
                # type == ConditionClause
                else:
                    lhs_operator = ''
                    lhs_parameter_name = ''
                    rhs_operator = ''
                    rhs_parameter_name = ''
                    for atom in body:
                        if atom.label == condition_clause.condition_variable[1].subject_variable and atom.atom_name == \
                                condition_clause.condition_variable[1].subject_name:
                            if atom.get_parameter_value(condition_clause.condition_variable[0].name) != '_':
                                lhs_operator = atom.get_parameter_value(condition_clause.condition_variable[0].name)
                                lhs_parameter_name = condition_clause.condition_variable[0].name
                            else:
                                lhs_operator = condition_clause.condition_variable[0].variable
                                lhs_parameter_name = condition_clause.condition_variable[0].name
                                atom.set_parameter_variable(condition_clause.condition_variable[0].name,
                                                            condition_clause.condition_variable[0].variable)
                        if type(condition_clause.condition_clause.condition_expression[0]) == str:
                            rhs_operator = condition_clause.condition_clause.condition_expression[0]
                            rhs_parameter_name = ''
                            for elem in re.split('[^a-zA-Z]', rhs_operator):
                                for atom in body:
                                    if (atom.has_parameter_value(elem)):
                                        rhs_parameter_name += atom.get_parameter_name_from_parameter_value(elem)
                        elif atom.label == condition_clause.condition_clause.condition_expression[
                            0][1].subject_variable and atom.atom_name == \
                                condition_clause.condition_clause.condition_expression[
                                    0][1].subject_name:
                            if atom.get_parameter_value(
                                    condition_clause.condition_clause.condition_expression[0][0].name) != '_':
                                rhs_operator = atom.get_parameter_value(
                                    condition_clause.condition_clause.condition_expression[0][0].name)
                                rhs_parameter_name = condition_clause.condition_clause.condition_expression[0][0].name
                            else:
                                rhs_operator = condition_clause.condition_clause.condition_expression[0][0].variable
                                rhs_parameter_name = condition_clause.condition_clause.condition_expression[0][0].name
                                atom.set_parameter_variable(
                                    condition_clause.condition_clause.condition_expression[0][0].name,
                                    condition_clause.condition_clause.condition_expression[0][0].variable)
                    operator = condition_clause.condition_clause.condition_operator
                    comparison = Comparison(operator, lhs_operator, lhs_parameter_name, rhs_operator,
                                            rhs_parameter_name, '', '', constraint.positive)
                for item in to_set_ordering_operator:
                    self.set_ordering_operator(item, body)
                return str(Rule(head=None, body=Conjunction(body + clauses + [comparison])))
            conjunction = None
            if constraint.clauses:
                for clause in constraint.clauses:
                    if type(clause) == AggregateClause:
                        if type(clause.aggregate_body) == SubjectClause:
                            aggregate_body_atom = self.__get_atom_from_signature_subject(
                                clause.aggregate_body.subject_name)
                            self.set_parameter_list(aggregate_body_atom, clause.aggregate_body.parameters)
                            parameter_name = clause.parameter[0].name
                            parameter_value = clause.parameter[0].variable if clause.parameter[0].variable else self.newVar()
                            aggregate_body_atom.set_parameter_variable(parameter_name, parameter_value)
                            aggregate_variable_list = [parameter_value]
                        else:
                            aggregate_body_atom = self.__get_atom_from_signature_subject(
                                clause.aggregate_body.aggregate_verb_clause.verb_name)
                            self.set_parameter_list(aggregate_body_atom, clause.aggregate_body.aggregate_verb_clause.parameters)
                            for parameter in clause.aggregate_body.aggregate_for_clauses:
                                aggregate_body_atom.set_parameter_variable(parameter.verb_object_name,
                                                                           parameter.verb_object_variable)
                            aggregate_variable_list = [self.newVar()]
                            parameter_name = '_'.join([clause.aggregate_body.aggregate_subject_clause.subject_name, clause.aggregate_body.aggregate_subject_clause.subject_variable]) if clause.aggregate_body.aggregate_subject_clause.subject_variable else clause.aggregate_body.aggregate_subject_clause.subject_name
                            if (aggregate_body_atom.get_parameter_value(parameter_name) != '_'):
                                aggregate_variable_list = [aggregate_body_atom.get_parameter_value(parameter_name)]
                            else:
                                aggregate_body_atom.set_parameter_variable(
                                    clause.aggregate_body.aggregate_subject_clause.subject_name,
                                    aggregate_variable_list[0])
                        aggregate_operator = clause.aggregate_operator
                        aggregate_body = [aggregate_body_atom]
                        for such_that in constraint.clauses:
                            if type(such_that) == SuchThat:
                                atom, comparison = self.init_atom_from_subject_clause(such_that.elements[0],body)
                                aggregate_body.append(atom)
                        aggregate: Aggregate = Aggregate(aggregate_operator, aggregate_variable_list,
                                                         aggregate_body, body)
                        comparison_aggregate: Comparison = Comparison(
                            constraint.comparison_clause[0].condition_operator,
                            aggregate, '',
                            self.__make_substitution_value(
                                constraint.comparison_clause[0].comparison_value), '', '', '', constraint.positive)
                        conjunction = Conjunction([comparison_aggregate])
                        return str(Rule(head=None, body=conjunction))
                    elif type(clause) == TemporalConstraint:
                        isTime = self.isTime(clause.temporal_value)
                        for atom_in_body in body:
                            if atom_in_body.atom_name == clause.subject_clause.subject_name and atom_in_body.label == clause.subject_clause.subject_variable:
                                for parameter in list(atom_in_body.atom_parameters.keys()):
                                    if isTime:
                                        for tc in self.time_temporal_concepts:
                                            if parameter == tc.name:
                                                variable = self.newVar()
                                                atom_in_body.set_parameter_variable(parameter, variable)
                                                time = datetime.strptime(clause.temporal_value, '%I:%M %p').strftime(
                                                    '%H:%M')
                                                value = list(tc.temporal_element_list.values()).index(time) + 1
                                                operator = negated_temporal_to_comparison_relations[clause.temporal_operator] if constraint.positive else temporal_to_comparison_relations[clause.temporal_operator]
                                                clauses.append(Comparison(
                                                    operator, variable, '', value, ''))
                                    else:
                                        for tc in self.date_temporal_concepts:
                                            if parameter == tc.name:
                                                variable = self.newVar()
                                                atom_in_body.set_parameter_variable(parameter, variable)
                                                time = datetime.strptime(clause.temporal_value, '%d/%m/%Y').strftime(
                                                    '%d/%m/%Y')
                                                value = list(tc.temporal_element_list.values()).index(time) + 1
                                                clauses.append(Comparison(
                                                    negated_temporal_to_comparison_relations[clause.temporal_operator],
                                                    variable, '', value, ''))
                        conjunction = Conjunction(body + clauses)
                        return str(Rule(head=None, body=conjunction))
                    elif type(clause) == SimpleClause:
                        atom = self.__get_atom_from_signature_subject(clause.verb_clause.verb_name)
                        atom.negated = not clause.verb_clause.verb_negated
                        if (clause.verb_clause.object_clause):
                            object_atom, comparison = self.init_atom_from_object_clause(ObjectClause(object_name = clause.verb_clause.object_clause.verb_object_name, object_variable = clause.verb_clause.object_clause.verb_object_variable))
                            self.link_two_atoms(atom,object_atom)
                        subject_atom, comparison = self.init_atom_from_subject_clause(clause.subject, [])
                        self.link_two_atoms(atom, subject_atom)
                        body.append(atom)
                    for item in to_set_ordering_operator:
                        self.set_ordering_operator(item, body)
                    conjunction = Conjunction(body + clauses)
                    return str(Rule(head=None, body=conjunction))
        else:
            compiled_string: str = ''
            conjunction: Conjunction | None = None
            block_memory: ClauseBlockMemory = ClauseBlockMemory()
            if type(constraint.clauses) == list:
                compiled_clauses = []
                for clause in constraint.clauses:
                    compiled_clause = None
                    if type(clause) == SimpleClause:
                        compiled_clause = self.__compile_simple_clause(clause, block_memory)
                    if type(compiled_clause) == list:
                        for clauses in compiled_clause:
                            compiled_clauses.append(clauses)
                    else:
                        compiled_clauses.append(compiled_clause)
                # block_memory is used to pass data through the methods
                block_memory.flush_all(on=compiled_clauses)
                conjunction = Conjunction(compiled_clauses)
            elif type(constraint.clauses) == AggregateClause:
                comparison_in_clause: ComparisonClause = constraint.comparison_clause
                # Aggregate: "the" aggregate_operator "of" (aggregate_active_clause | aggregate_passive_clause) (ranging_clause)?
                aggregate: Aggregate = self.__compile_aggregate_clause(constraint.clauses)
                comparison: Comparison = Comparison(comparison_in_clause.condition_operator, aggregate, '',
                                                    self.__make_substitution_value(
                                                        comparison_in_clause.comparison_value), '')
                conjunction = Conjunction([comparison])

            maybe_unsafe_atoms: list[Atom] = conjunction.extract_maybe_unsafe_atoms()
            safe_variables: set[str] = conjunction.extract_safe_variables()
            safety_atoms_to_add: list[Atom] = []

            for atom in maybe_unsafe_atoms:
                for parameter in atom.atom_parameters.keys():
                    for variable in atom.atom_parameters[parameter]:
                        if (match := re.search(r'(X(_[a-z0-9]+){5}|[A-Z]([A-Z0-9a-z_])*)', variable)) \
                                is not None and match.group(1) not in safe_variables:
                            safety_atom: Atom | None = None
                            for old_atom in safety_atoms_to_add:
                                if old_atom.atom_name == parameter:
                                    safety_atom = old_atom
                            if safety_atom is None:
                                safety_atom = self.__get_atom_from_signature_subject(parameter)
                                safety_atoms_to_add.append(safety_atom)
                            safety_atom.set_parameter_variable(parameter, variable, force=True)

            conjunction.body += safety_atoms_to_add

            conjunction_list: list[Conjunction] = []
            if constraint.where_clause:
                conjunction_list += self.__make_where_clause_list(constraint, conjunction, block_memory)
            if not conjunction_list:
                conjunction_list.append(conjunction)

            for elem in conjunction_list:
                for const, const_val in constant_definitions_dict.items():
                    elem.set_variable_value(const, const_val)

            # Delete duplicates
            conjunction_list = list(dict.fromkeys(conjunction_list))

            for elem in conjunction_list:
                compiled_string += str(Rule(head=None, body=elem))

            return compiled_string

    def __compile_weak_constraint_clause(self, constraint: WeakConstraintClause):
        if constraint.whenever_clause:
            body: list[Atom] = []
            comparisons = []
            for elem in constraint.whenever_clause:
                atom = self.__get_atom_from_signature_subject(elem.subject.subject_name)
                atom.label = elem.subject.subject_variable
                if elem.subject.parameters:
                    for parameter in elem.subject.parameters:
                        if type(parameter) == Parameter:
                            atom.set_parameter_variable(parameter.name, parameter.variable)
                        else:
                            operator = parameter.expression_operator
                            lhs = parameter.expression_lhs.variable
                            rhs = parameter.expression_rhs
                            comparisons.append(Comparison(operator, lhs, '', rhs, ''))
                            atom.set_parameter_variable(parameter.expression_lhs.name, lhs)
                else:
                    atom.initializeVariables(self.__get_atom_from_signature_subject(elem.subject.subject_name))
                body.append(atom)
            if constraint.verb:
                verb_atom = self.__get_atom_from_signature_subject(constraint.verb.name)
                subject_atom = ''
                for elem in constraint.object:
                    verb_atom.set_parameter_variable(elem.object_name, elem.object_variable)
                    for atom in body:
                        if atom.label == elem.object_variable:
                            self.link_two_atoms(verb_atom, atom)
                            break
                discriminant = ''
                if constraint.subject[0].parameters:
                    subject_atom = self.__get_atom_from_signature_subject(constraint.subject[0].subject_name)
                    subject_atom.label = constraint.subject[0].subject_variable
                    for parameter in constraint.subject[0].parameters:
                        subject_atom.set_parameter_variable(parameter.name, parameter.variable)

                    self.link_two_atoms(subject_atom, verb_atom.atom_parameters[subject_atom.atom_name][0])
                discriminant = verb_atom.atom_parameters[constraint.subject[0].subject_name][0]
                if type(discriminant) == Atom:
                    discriminant = list(discriminant.atom_parameters.values())[0]
                cost = '-1' if constraint.optimization_operator == 'as much as possible' or constraint.optimization_operator == 'maximized' else '1'
                return str(Rule(head=None, body=Conjunction(body + comparisons + [subject_atom] + [verb_atom]),
                                cost=[cost, str(priority_levels_map[constraint.priority_level])],
                                discriminants=discriminant))
            elif constraint.variable_to_optimize:
                cost = constraint.variable_to_optimize if constraint.optimization_operator == 'as little as possible' or constraint.optimization_operator == 'minimized' else f'-{constraint.variable_to_optimize}'
                return str(Rule(head=None, body=Conjunction(body + comparisons),
                                cost=[cost, str(priority_levels_map[constraint.priority_level])]))
            elif type(constraint.constraint_body[0]) == ConditionClause:
                lhs = constraint.constraint_body[0].condition_variable
                if type(constraint.constraint_body[0].condition_variable) == AggregateClause:
                    subject_atom, comparison = self.init_atom_from_subject_clause(constraint.constraint_body[0].condition_variable.aggregate_body, body)
                    var = self.newVar()
                    subject_atom.set_parameter_variable(constraint.constraint_body[0].condition_variable.parameter[0].name, var, force=True)
                    lhs = Aggregate(constraint.constraint_body[0].condition_variable.aggregate_operator,
                                    [var],
                                    [subject_atom],
                                    [])
                rhs = constraint.constraint_body[0].condition_clause.condition_expression[0]
                if type(constraint.constraint_body[0].condition_clause.condition_expression[0]) == Aggregate:
                    rhs = Aggregate()
                rule = Comparison(constraint.constraint_body[0].condition_clause.condition_operator, lhs, '', rhs)

                cost = '-1' if constraint.optimization_operator == 'as much as possible' or constraint.optimization_operator == 'maximized' else '1'
                return str(Rule(head=None, body=Conjunction(body + comparisons + [rule]),
                                cost=[cost, str(priority_levels_map[constraint.priority_level])]))
        compilation_string: str = ''

        body_in_clause: ConditionOperation | AggregateClause = constraint.constraint_body
        variable: str = f'X_{str(uuid4()).replace("-", "_")}'
        conjunction: Conjunction | str = ''
        subject_variables_in_clause: list[str] = []
        if type(body_in_clause) is AggregateClause:
            subject_in_clause: Subject = Subject(body_in_clause
                                                 .aggregate_body.aggregate_subject_clause)
            aggregate: Aggregate = self.__compile_aggregate_clause(body_in_clause,
                                                                   in_subject=subject_in_clause)
            if not body_in_clause.aggregate_body.active_form:
                subject_variables_in_clause.append(subject_in_clause.variable)
            comparison: Comparison = Comparison('equal to', aggregate, '', variable, '')
            clause_list = []
            clause_list.append(comparison)
            if body_in_clause.ranging_clause:
                clause_list.append(BoundedVariable(variable, {'lower': self.__make_substitution_value(body_in_clause
                                                                                                      .ranging_clause.ranging_lhs),
                                                              'upper': self.__make_substitution_value(body_in_clause
                                                                                                      .ranging_clause.ranging_rhs)}))
            conjunction = Conjunction(clause_list)
        else:
            ag_variable: str = f'X_{str(uuid4()).replace("-", "_")}'
            clause_list = []
            if type(body_in_clause.expression_lhs) is AggregateClause:
                subject_in_clause: Subject = Subject(body_in_clause.expression_lhs
                                                     .aggregate_body.aggregate_subject_clause)
                aggregate: Aggregate = self.__compile_aggregate_clause(body_in_clause.expression_lhs,
                                                                       in_subject=subject_in_clause)
                if not body_in_clause.expression_lhs.aggregate_body.active_form:
                    subject_variables_in_clause.append(subject_in_clause.variable)
                comparison: Comparison = Comparison('equal to', aggregate, '', ag_variable, '')
                clause_list.append(comparison)
                if body_in_clause.expression_lhs.ranging_clause:
                    clause_list.append(BoundedVariable(ag_variable, {
                        'lower': self.__make_substitution_value(body_in_clause.expression_lhs
                                                                .ranging_clause.ranging_lhs),
                        'upper': self.__make_substitution_value(body_in_clause.expression_lhs
                                                                .ranging_clause.ranging_rhs)}))
                operation: Operation = Operation(ag_variable, body_in_clause.expression_operator.operator,
                                                 self.__make_substitution_value(body_in_clause.expression_rhs),
                                                 variable,
                                                 body_in_clause.expression_operator.absolute_value)
                clause_list.append(operation)
            if type(body_in_clause.expression_rhs) is list and type(body_in_clause.expression_rhs[0]) is AggregateClause:
                body_in_clause_rhs = body_in_clause.expression_rhs[0]
                subject_in_clause: Subject = Subject(body_in_clause_rhs
                                                     .aggregate_body.aggregate_subject_clause)
                aggregate: Aggregate = self.__compile_aggregate_clause(body_in_clause_rhs,
                                                                       in_subject=subject_in_clause)
                if not body_in_clause_rhs.aggregate_body.active_form:
                    subject_variables_in_clause.append(subject_in_clause.variable)
                comparison: Comparison = Comparison('equal to', aggregate, '', ag_variable, '')
                clause_list.append(comparison)
                if body_in_clause_rhs.ranging_clause:
                    clause_list.append(BoundedVariable(ag_variable, {
                        'lower': self.__make_substitution_value(body_in_clause_rhs
                                                                .ranging_clause.ranging_lhs),
                        'upper': self.__make_substitution_value(body_in_clause_rhs
                                                                .ranging_clause.ranging_rhs)}))
                operation: Operation = Operation(self.__make_substitution_value(body_in_clause.expression_lhs),
                                                 body_in_clause.expression_operator.operator,
                                                 ag_variable,
                                                 variable,
                                                 body_in_clause.expression_operator.absolute_value)
                clause_list.append(operation)
            conjunction = Conjunction(clause_list)

        conjunction_list: list[Conjunction] = []
        if constraint.where_clause:
            conjunction_list += self.__make_where_clause_list(constraint, conjunction, None)
        if not conjunction_list:
            conjunction_list.append(conjunction)

        for elem in conjunction_list:
            for const, const_val in constant_definitions_dict.items():
                elem.set_variable_value(const, const_val)

        variable = f"-{variable}" if constraint.optimization_operator == 'maximized' or constraint.optimization_operator == 'as much as possible' else variable

        for elem in conjunction_list:
            compilation_string += str(Rule(head=None, body=elem,
                                           cost=[variable, str(priority_levels_map[constraint.priority_level])],
                                           discriminants=subject_variables_in_clause))

        return compilation_string

    def __compile_aggregate_clause(self, aggregate_clause: AggregateClause, in_subject: Subject = None):
        compiled_string: str = ''
        aggregate_body_in_clause: AggregateBodyClause = aggregate_clause.aggregate_body
        aggregate_ranging_in_clause: RangingClause = aggregate_clause.ranging_clause
        aggregate_operator_in_clause: str = aggregate_clause.aggregate_operator
        subject_in_clause: Subject = Subject(aggregate_body_in_clause.aggregate_subject_clause) if in_subject is None \
            else in_subject
        verb_in_clause = list()
        if type(aggregate_body_in_clause.aggregate_verb_clause) == list:
            for aggregate_verb in aggregate_body_in_clause.aggregate_verb_clause:
                verb_in_clause.append(Verb(aggregate_verb))
        else:
            verb_in_clause = Verb(aggregate_body_in_clause.aggregate_verb_clause)
        aggregate_objects_in_clause: list[VerbObject] = []
        if type(aggregate_body_in_clause.aggregate_object_clause) == VerbObjectClause:
            aggregate_objects_in_clause.append(VerbObject(aggregate_body_in_clause.aggregate_object_clause))
        elif type(aggregate_body_in_clause.aggregate_object_clause) == CompositionClause:
            aggregate_objects_in_clause += \
                [VerbObject(aggregate_body_in_clause.aggregate_object_clause.composition_lhs),
                 VerbObject(aggregate_body_in_clause.aggregate_object_clause.composition_rhs)]
        elif type(aggregate_body_in_clause.aggregate_object_clause) == TupleClause:
            for elem in aggregate_body_in_clause.aggregate_object_clause.tuple_objects:
                aggregate_objects_in_clause += [VerbObject(elem)]

        for_objects_in_clause: list[AggregateForObject] = []
        for elem in aggregate_body_in_clause.aggregate_for_clauses:
            for_objects_in_clause.append(AggregateForObject(elem))

        aggregate_variable_list: list[str] = []
        aggregate_body: list[Atom] = []
        aggregate_head: list[Atom] = []

        # <head>, {<variable_list>: <body>}
        if aggregate_body_in_clause.active_form:
            aggregate_verb_atom = list()
            if type(verb_in_clause) == list:
                for verb in verb_in_clause:
                    atom = self.__get_atom_from_signature_subject(verb.name)
                    atom.negated = verb.is_negated
                    if aggregate_clause.parameter:
                        atom.set_parameter_variable(aggregate_clause.parameter[0].name, subject_in_clause.variable)
                    else:
                        atom.set_parameter_variable(subject_in_clause.name, subject_in_clause.variable)
                    aggregate_verb_atom.append(atom)
            else:
                atom = self.__get_atom_from_signature_subject(verb_in_clause.name)
                atom.negated = verb_in_clause.is_negated
                if aggregate_clause.parameter:
                    atom.set_parameter_variable(aggregate_clause.parameter[0].name, subject_in_clause.variable)
                else:
                    atom.set_parameter_variable(subject_in_clause.name, subject_in_clause.variable)
                aggregate_verb_atom.append(atom)
            aggregate_variable_list.append(subject_in_clause.variable)
            for atom in aggregate_verb_atom:
                aggregate_body.append(atom)
            if not aggregate_body_in_clause.aggregate_for_clauses:
                if aggregate_objects_in_clause:
                    atom: Atom = self.__get_atom_from_signature_subject(aggregate_objects_in_clause[0].name)
                    parameter_name = list(atom.atom_parameters.keys())[0]
                    for agg_atom in aggregate_verb_atom:
                        self.__double_substitution(agg_atom, parameter_name, atom,
                                                   aggregate_objects_in_clause[0].variable)
                    aggregate_objects_in_clause.pop(0)
                    aggregate_head.append(atom)
        else:
            newDefinition = True
            aggregate_verb_atom = Atom(verb_in_clause.name, dict())
            if self.__get_atom_from_signature_subject(verb_in_clause.name):
                newDefinition = False
                aggregate_verb_atom: Atom = self.__get_atom_from_signature_subject(verb_in_clause.name)
            aggregate_verb_atom.negated = verb_in_clause.is_negated
            aggregate_body.append(aggregate_verb_atom)
            aggregate_subject_atom: Atom = self.__get_atom_from_signature_subject(subject_in_clause.name)
            if aggregate_subject_atom:
                self.__double_substitution(aggregate_verb_atom, subject_in_clause.name, aggregate_subject_atom,
                                           subject_in_clause.variable, newDefinition)
                aggregate_head.append(aggregate_subject_atom)
            if newDefinition:
                self.decl_signatures.append(aggregate_verb_atom.compute_signature())
        variable: str = ''
        for ag_object in aggregate_objects_in_clause:
            if ag_object.range is not None:
                variable = ag_object.variable
                (head_part, body_part) = self.__make_windowed_range_for_aggregate(ag_object.range.range_window,
                                                                                  variable,
                                                                                  ag_object.name,
                                                                                  f'X_{str(uuid4()).replace("-", "_")}')
                aggregate_head += head_part
                aggregate_body.append(body_part)
                aggregate_variable_list.append(variable)
            else:
                if ag_object.variable not in alphabetic_constants_set and not ag_object.variable.isdigit():
                    variable = ag_object.variable
                    aggregate_variable_list.append(variable)
                else:
                    variable = f'"{ag_object.variable}"' if not ag_object.variable.isdigit() else ag_object.variable
            if (type(verb_in_clause) == list):
                for atom in verb_in_clause:
                    join_atom: Atom | None = self.__find_join_atom_from_signature_subject(atom.name,
                                                                                          ag_object.name)
            else:
                join_atom: Atom | None = self.__find_join_atom_from_signature_subject(verb_in_clause.name,
                                                                                      ag_object.name)

            if join_atom is not None:
                if (type(aggregate_verb_atom) == list):
                    for atom in aggregate_verb_atom:
                        self.__join_atoms(atom, ag_object.name, join_atom, variable)
                else:
                    self.__join_atoms(aggregate_verb_atom, ag_object.name, join_atom, variable)
                aggregate_body.append(join_atom)
            else:
                if (type(aggregate_verb_atom) == list):
                    for atom in aggregate_verb_atom:
                        atom.set_parameter_variable(ag_object.name, variable)
                else:
                    aggregate_verb_atom.set_parameter_variable(ag_object.name, variable)

        for for_object in for_objects_in_clause:
            atom: Atom = self.__get_atom_from_signature_subject(for_object.for_object.name)
            variable_name = list(atom.atom_parameters.keys())[0]
            if (type(aggregate_verb_atom) == list):
                atom.set_parameter_variable(variable_name, for_object.for_object.variable)
                for agg_atom in aggregate_verb_atom:
                    agg_atom.set_parameter_variable(variable_name, for_object.for_object.variable)
            else:
                self.__double_substitution(aggregate_verb_atom, variable_name, atom,
                                           for_object.for_object.variable)
            aggregate_head.append(atom)
        aggregate: Aggregate = Aggregate(aggregate_operator_in_clause, aggregate_variable_list,
                                         aggregate_body, aggregate_head)

        return aggregate

    # check if a string is in the global constants otherwise return itself
    def __make_substitution_value(self, string_to_check: str) -> str:
        if string_to_check.lower() in constant_definitions_dict.keys() and constant_definitions_dict[string_to_check.lower()]:
            return constant_definitions_dict[string_to_check.lower()]
        elif string_to_check in alphabetic_constants_set:
            return f'"{string_to_check}"'
        else:
            return string_to_check

    # simple_clause: subject_clause CNL_COPULA? verb_clause
    def __compile_simple_clause(self, clause: SimpleClause, block_memory: ClauseBlockMemory):
        result: Atom | Comparison | None = None
        subject_in_clause: Subject = Subject(clause.subject)
        # set the current subject into the memory if the memory is empty
        if block_memory.subject_in_block is None:
            block_memory.set_subject_of_block(subject_in_clause)
        # verb_clause: verb_negation? (verb_name | verb_name_with_preposition) (verb_object_clause | composition_clause | tuple_clause | same_clause)? | verb_negation? verb_name
        verb_in_clause: Verb = Verb(clause.verb_clause)
        newDefinition = True
        simple_verb_atom = Atom(verb_in_clause.name, dict())
        if self.__get_atom_from_signature_subject(verb_in_clause.name):
            newDefinition = False
            simple_verb_atom: Atom = self.__get_atom_from_signature_subject(verb_in_clause.name)
        # the subject in block memory is the true subject
        # substitute the simple verb atom parameter (initialized to '_') with the corresponding subject variable 
        if subject_in_clause.name != block_memory.subject_in_block.name:
            simple_verb_atom.set_parameter_variable(block_memory.subject_in_block.name,
                                                    self.__make_substitution_value(
                                                        block_memory.subject_in_block.variable), newDefinition=newDefinition)
        else:
            simple_verb_atom.set_parameter_variable(subject_in_clause.name,
                                                    self.__make_substitution_value(
                                                        subject_in_clause.variable), newDefinition=newDefinition)
        simple_verb_atom.negated = verb_in_clause.is_negated
        result = simple_verb_atom
        # todo: i soggetti (dopo il primo) possono anche non essere all'interno dei parametri dell'atomo del verbo
        if subject_in_clause.name != block_memory.subject_in_block.name:
            value_for_subject: str = subject_in_clause.variable
            if subject_in_clause.ordering is not None:
                value_for_subject = block_memory.get_time_variable_value(subject_in_clause.name)
                consecution_count: int = 1
                if subject_in_clause.ordering.consecutive:
                    simple_verb_atom.negated = False
                    ag_variable: str = f'X_{str(uuid4()).replace("-", "_")}'
                    consecution_count = subject_in_clause.ordering.ordering_count
                    starting_position: str = str(abs(block_memory.get_current_time_position(
                        on_time_window_of=subject_in_clause.name) + 1)) \
                        if subject_in_clause.ordering.ordering_direction == 'the next' else str(
                        abs(block_memory.get_current_time_position(on_time_window_of=subject_in_clause.name) - 1))
                    head_part, body_part = self.__make_consecution_string(subject_in_clause.name, ag_variable,
                                                                          starting_position,
                                                                          consecution_count,
                                                                          object_variable=value_for_subject,
                                                                          consecution_operator=subject_in_clause.ordering
                                                                          .ordering_direction)
                    aggregate = Aggregate('number', [ag_variable], [simple_verb_atom, body_part], [head_part])
                    result = Comparison('different from', aggregate, '', consecution_count,
                                        '') if verb_in_clause.is_negated \
                        else Comparison('equal to', aggregate, '', consecution_count, '')
                    value_for_subject = ag_variable
                else:
                    if subject_in_clause.ordering.ordering_direction == 'the next':
                        value_for_subject = f'{value_for_subject}+' \
                                            f'{abs(block_memory.get_current_time_position(on_time_window_of=subject_in_clause.name) + 1)}'
                    else:
                        value_for_subject = f'{value_for_subject}-' \
                                            f'{abs(block_memory.get_current_time_position(on_time_window_of=subject_in_clause.name) - 1)}'
                if subject_in_clause.ordering.ordering_direction == 'the next':
                    block_memory.go_forward_in_time(of=consecution_count, on_time_window_of=subject_in_clause.name)
                else:
                    block_memory.go_backward_in_time(of=consecution_count, on_time_window_of=subject_in_clause.name)

            simple_verb_atom.set_parameter_variable(subject_in_clause.name,
                                                    self.__make_substitution_value(value_for_subject), newDefinition=newDefinition)
        # list of object_clauses
        # object_clause: "a "? object_name variable?
        objects_in_clause: list[VerbObject] = []
        if type(clause.verb_clause.object_clause) == VerbObjectClause:
            objects_in_clause.append(VerbObject(clause.verb_clause.object_clause))
        elif type(clause.verb_clause.object_clause) == list and all(
                type(obj) == VerbObjectClause for obj in clause.verb_clause.object_clause):
            for object in clause.verb_clause.object_clause:
                objects_in_clause.append(VerbObject(object))
        elif type(clause.verb_clause.object_clause) == CompositionClause:
            objects_in_clause += [VerbObject(clause.verb_clause.object_clause.composition_lhs),
                                  VerbObject(clause.verb_clause.object_clause.composition_rhs)]
        elif type(clause.verb_clause.object_clause) == TupleClause:
            for elem in clause.verb_clause.object_clause.tuple_objects:
                objects_in_clause += [VerbObject(elem)]

        # todo: gli oggetti possono anche non essere all'interno dei parametri dell'atomo del verbo
        for cls_object in objects_in_clause:
            value_for_object: str = cls_object.variable
            block_memory.add_time_variable_to_memory(cls_object.name, cls_object.variable)
            if cls_object.ordering is not None:
                cls_object_signature: Signature = self.__get_signature(cls_object.name)
                first_ordering_variable: str = cls_object.ordering.ordering_variable
                second_ordering_variable: str = f'X_{str(uuid4()).replace("-", "_")}'
                if cls_object_signature.indexed_by_parameter:
                    first_ordering_variable = f'X_{str(uuid4()).replace("-", "_")}'
                    new_variable: str = f'X_{str(uuid4()).replace("-", "_")}'
                    block_memory.add_ordering_variable_mapping_to_memory(cls_object.ordering.ordering_variable,
                                                                         first_ordering_variable)
                    block_memory.add_bounded_variable_to_memory(BoundedVariable(first_ordering_variable,
                                                                                cls_object_signature.ordering_bounds))
                    block_memory.add_bounded_variable_to_memory(BoundedVariable(second_ordering_variable,
                                                                                cls_object_signature.ordering_bounds))
                    first_atom: Atom = self.__get_atom_from_signature_subject(cls_object.name)
                    second_atom: Atom = self.__get_atom_from_signature_subject(cls_object.name)
                    first_atom.set_parameter_variable(f'{cls_object.name}_ord', first_ordering_variable)
                    second_atom.set_parameter_variable(f'{cls_object.name}_ord', second_ordering_variable)
                    first_atom.set_parameter_variable(cls_object.name, cls_object.ordering.ordering_variable)
                    second_atom.set_parameter_variable(cls_object.name, new_variable)
                    block_memory.add_atom_to_memory(first_atom)
                    block_memory.add_atom_to_memory(second_atom)
                    value_for_object = new_variable
                if cls_object.ordering.ordering_operator == 'after':
                    block_memory.add_inequality_to_memory(f'{second_ordering_variable} > {first_ordering_variable}')
                else:
                    block_memory.add_inequality_to_memory(f'{second_ordering_variable} < {first_ordering_variable}')
            if cls_object.consecution:
                ag_variable: str = f'X_{str(uuid4()).replace("-", "_")}'
                mem_variable: str = f'X_{str(uuid4()).replace("-", "_")}'
                block_memory.add_time_variable_to_memory(cls_object.consecution.consecution_object_name,
                                                         mem_variable)
                consecution_count: int = cls_object.consecution.consecution_count
                starting_position: str = str(abs(block_memory.get_current_time_position(
                    on_time_window_of=cls_object.consecution.consecution_object_name)))
                head_part, body_part = self.__make_consecution_string(cls_object.consecution.consecution_object_name,
                                                                      ag_variable,
                                                                      starting_position,
                                                                      consecution_count - 1,
                                                                      object_variable=mem_variable,
                                                                      consecution_operator='the next')
                simple_verb_atom.set_parameter_variable(cls_object.consecution.consecution_object_name,
                                                        ag_variable)
                aggregate = Aggregate('number', [ag_variable], [simple_verb_atom, body_part], [head_part])
                result = Comparison('different from', aggregate, '', consecution_count, '') if verb_in_clause.is_negated \
                    else Comparison('equal to', aggregate, '', consecution_count, '')
                value_for_object = cls_object.variable
                block_memory.go_forward_in_time(of=consecution_count - 1,
                                                on_time_window_of=cls_object.consecution.consecution_object_name)

            simple_verb_atom.set_parameter_variable(cls_object.name,
                                                    self.__make_substitution_value(value_for_object))
            subject_atom = None
            if clause.parameter_list:
                subject_atom = self.__get_atom_from_signature_subject(subject_in_clause.name)
                for parameter in clause.parameter_list:
                    subject_atom.set_parameter_variable(parameter.name.lower(), parameter.name)
            if subject_atom:
                return [result, subject_atom]
        return result

    def __make_where_clause_list(self, constraint: StrongConstraintClause | WeakConstraintClause,
                                 until_now: Conjunction,
                                 memory: ClauseBlockMemory):
        where_in_clause: WhereClause = constraint.where_clause

        result = []
        for elem in where_in_clause.conditions:
            if type(elem) is ConditionClause:
                variable: str = memory.get_ordering_variable_mapping(elem.condition_variable)
                if type(elem.condition_clause) is ConditionBoundClause:
                    until_now.set_bounded_variable_bounds(variable,
                                                          {'lower': get_ordering_number(
                                                              of=elem.condition_clause.bound_lower),
                                                              'upper': get_ordering_number(
                                                                  of=elem.condition_clause.bound_upper)})
                elif type(elem.condition_clause) is ConditionComparisonClause:
                    comparison = None
                    if type(elem.condition_clause.condition_expression[0]) is not ConditionOperation:
                        comparison = Comparison(elem.condition_clause.condition_operator,
                                                variable, '',
                                                elem.condition_clause.condition_expression[0], '')
                    else:
                        more_factors = None
                        if elem.condition_clause.condition_expression[0].more_expression_factors:
                            more_factors = elem.condition_clause.condition_expression[0].more_expression_factors
                        if elem.condition_clause.condition_operator in comparison_relations:
                            comparison = Comparison(elem.condition_clause.condition_operator,
                                                    variable, '',
                                                    Operation(
                                                        elem.condition_clause.condition_expression[0].expression_lhs,
                                                        elem.condition_clause.condition_expression[0]
                                                        .expression_operator.operator,
                                                        elem.condition_clause.condition_expression[0].expression_rhs,
                                                        None,
                                                        elem.condition_clause.condition_expression[0]
                                                        .expression_operator.absolute_value,
                                                        more_factors
                                                    ), '')
                        else:
                            comparison = Comparison('equal to',
                                                    variable, '',
                                                    Operation(
                                                        elem.condition_clause.condition_expression[0].expression_lhs,
                                                        elem.condition_clause.condition_expression[0]
                                                        .expression_operator.operator,
                                                        elem.condition_clause.condition_expression[0].expression_rhs,
                                                        None,
                                                        elem.condition_clause.condition_expression[0]
                                                        .expression_operator.absolute_value,
                                                        more_factors
                                                    ), '')
                    until_now.body.append(comparison)
                    result.append(until_now)
        for elem in where_in_clause.conditions:
            if type(elem) is ConditionMatchGroup:
                for i in range(elem.group_list[0].list_len):
                    until_now_copy: Conjunction = until_now.copy()
                    for x in elem.group_list:
                        value: str = self.__make_substitution_value(x.condition_list[i])
                        until_now_copy.set_variable_value(x.condition_variable, value)
                    result.append(until_now_copy)

        return result

    def __join_atoms(self, first_atom: Atom, parameter: str, second_atom: Atom, with_variable_name: str = None):
        variable_value: str = parameter.upper() if with_variable_name is None else with_variable_name
        join_variable: str = f'X_{str(uuid4()).replace("-", "_")}'
        if first_atom is not None:
            first_atom.set_parameter_variable(second_atom.atom_name, join_variable)
        if second_atom is not None:
            second_atom.set_parameter_variable(second_atom.atom_name, join_variable)
            second_atom.set_parameter_variable(parameter, variable_value)

    def __double_substitution(self, first_atom: Atom, parameter: str, second_atom: Atom,
                              with_variable_name: str = None, newDefinition=False):
        join_variable: str = parameter.capitalize() if with_variable_name is None else with_variable_name
        if first_atom is not None:
            first_atom.set_parameter_variable(parameter, join_variable, newDefinition=newDefinition)
        if second_atom is not None:
            second_atom.set_parameter_variable(parameter, join_variable)

    def __find_join_atom_from_signature_subject(self, from_signature_subject: str, attribute: str) -> Atom | None:
        if self.__get_signature(from_signature_subject):
            for signature_attribute in self.__get_signature(from_signature_subject).object_list:
                if signature_attribute == attribute:
                    return None
                else:
                    if self.__get_signature(signature_attribute):
                        for attribute_signature_object in self.__get_signature(signature_attribute).object_list:
                            if attribute_signature_object == attribute:
                                return self.__get_atom_from_signature_subject(signature_attribute)
        else:
            return

    def __make_consecution_string(self, object_name: str, consecution_variable: str, consecution_start: str,
                                  consecution_count: int, object_variable: str = None,
                                  consecution_operator: str = 'between'):
        atom: Atom = self.__get_atom_from_signature_subject(object_name)
        subst_variable: str = f'X_{str(uuid4()).replace("-", "_")}' if object_variable is None else object_variable
        atom_str: str = f"{atom.set_parameter_variable(object_name, subst_variable)}"
        if consecution_operator == 'the next':
            upper_bound: int = self.__get_signature(object_name).ordering_bounds['upper']
            first_inequality: str = f"{subst_variable}+{str(int(consecution_count))} <= {str(upper_bound)}"
            second_inequality: str = f"{consecution_variable} >= " \
                                     f"{subst_variable}+{consecution_start}, {consecution_variable} <= " \
                                     f"{subst_variable}+{str(int(consecution_count))}" \
                if int(consecution_start) > 0 else f"{consecution_variable} >= " \
                                                   f"{subst_variable}, {consecution_variable} <= " \
                                                   f"{subst_variable}+{str(int(consecution_count))}"
            return atom, second_inequality
        elif consecution_operator == 'the previous':
            lower_bound: int = self.__get_signature(object_name).ordering_bounds['lower']
            first_inequality: str = f"{subst_variable}-{str(int(consecution_count))} >= {str(lower_bound)}"
            second_inequality: str = f"{consecution_variable} >= " \
                                     f"{subst_variable}-{str(int(consecution_count))}, " \
                                     f"{consecution_variable} <= " \
                                     f"{subst_variable}-{consecution_start}" \
                if int(consecution_start) > 0 else f"{consecution_variable} >= " \
                                                   f"{subst_variable}-{str(int(consecution_count))}, " \
                                                   f"{consecution_variable} <= " \
                                                   f"{subst_variable}"
            return atom, second_inequality

        else:
            upper_bound: int = self.__get_signature(object_name).ordering_bounds['upper']
            first_inequality: str = f"{subst_variable} <= " \
                                    f"{str(upper_bound - (int(consecution_count) - 1))}"
            second_inequality: str = f"{consecution_variable} >= {subst_variable}, {consecution_variable} <= " \
                                     f"{subst_variable}+{str(int(consecution_count) - 1)}"
            return atom, second_inequality

    def __make_windowed_range_for_aggregate(self, window_value: int, window_variable: str, object_name: str,
                                            object_variable: str):
        upper_bound: int = self.__get_signature(object_name).ordering_bounds['upper']
        atom: Atom = self.__get_atom_from_signature_subject(object_name)
        atom_str: str = f"{atom.set_parameter_variable(object_name, object_variable)}"
        first_inequality: str = f"{object_variable} <= {str(upper_bound - (int(window_value) - 1))}"
        second_inequality: str = f"{window_variable} >= {object_variable}, {window_variable} <= " \
                                 f"{object_variable}+{str(int(window_value) - 1)}"
        return (atom, first_inequality), second_inequality

    # todo: controllare che i riferimenti sono stati effettivamente introdotti nelle definizioni, lanciare un errore altrimenti
    # return a new atom with all its corresponding parameters initialized to '_'
    def __get_atom_from_signature_subject(self, subject_in_signature: str, signature=None):
        subject_in_signature = subject_in_signature.lower()
        try:
            if not signature:
                signature: Signature = self.__get_signature(subject_in_signature)
        except:
            signature = None
        if signature:
            atom: Atom = Atom(signature.subject, dict())
            for elem in signature.object_list:
                if (type(elem) == Signature):
                    object_list = dict()
                    for parameter in elem.object_list:
                        if (type(parameter) == Signature):
                            object_list[parameter.subject] = [
                                self.__get_atom_from_signature_subject(parameter.subject, parameter)]
                        else:
                            object_list[parameter] = ['_']
                    atom_parameter = Atom(elem.subject, object_list)
                    atom.set_parameter_variable(elem.subject, atom_parameter, newDefinition=True)
                else:
                    atom.set_parameter_variable(elem, '_', newDefinition=True)
            return atom
        else:
            return

    def __signature_To_Atom(self, signature):
        atom: Atom = Atom(signature.subject, dict())
        for elem in signature.object_list:
            if (type(elem) == Signature):
                object_list = dict()
                for parameter in elem.object_list:
                    object_list[parameter] = ['_']
                atom_parameter = Atom(elem.subject, object_list)
                atom.set_parameter_variable(elem.subject, atom_parameter, newDefinition=True)
            else:
                atom.set_parameter_variable(elem, '_', newDefinition=True)
        return atom

    def __get_signature_from_atom(self, atom: Atom) -> Signature:
        return self.__get_signature(atom.atom_name)

    def __get_signature(self, signature_name: str) -> Signature:
        for elem in self.decl_signatures:
            if elem.subject == signature_name:
                return elem
        raise Exception(f'Signature "{signature_name}" not found.')
