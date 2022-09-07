import copy
import re
from uuid import uuid4
import os.path
import logging

from typing import TextIO

from lark import Lark
from cnl.parse import *
from dataclasses import *

debug: bool = False

comparison_relations = {'more than': ">", 'less than': '<', 'different from': '!=', 'equal to': '=', 'at least': '>=',
                        'at most': '<='}
ordering_operators = {'before': '<', 'after': '>'}
aggregate_operators = {'number': 'count', 'total': 'sum', "highest": "max", "biggest": "max", "lowest": 'min',
                       "smallest": 'min'}
priority_levels_map = {'low': 1, 'medium': 2, 'high': 3}
condition_operation = {'the sum': '+', 'the difference': '-', 'the product': '*', 'the division': '/'}
alphabetic_constants_set: set[str] = set()
ordered_constant_dict: dict[str, int] = {}
constant_definitions_dict: dict[str, str] = {}


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
                 ordering_bounds: dict[str, int] = None, indexed_by_parameter: bool = False):
        self.subject = subject
        self.object_list = object_list
        self.granularity_hierarchy = granularity_hierarchy
        self.ordering_bounds = ordering_bounds if ordering_bounds is not None else {'lower': None, 'upper': None}
        if indexed_by_parameter:
            self.object_list = [self.subject + '_ord'] + self.object_list
        self.indexed_by_parameter = indexed_by_parameter

    def __repr__(self):
        return f"Signature(subject={str(self.subject)}, object_list={str(self.object_list)}, " \
               f"granularity_hierarchy={str(self.granularity_hierarchy)}, " \
               f"ordering_bounds=[lower={self.ordering_bounds['lower']}, " \
               f"upper={self.ordering_bounds['upper']}])"


class Atom:

    def __init__(self, atom_name: str, atom_parameters: dict[str, list[str]], ordering_index: int = None,
                 negated: bool = False):
        self.atom_name = atom_name.replace(' ', '_')
        self.atom_parameters = atom_parameters
        self.ordering_index = ordering_index
        self.negated = negated

    def copy(self):
        return Atom(copy.deepcopy(self.atom_name),
                    copy.deepcopy(self.atom_parameters),
                    copy.deepcopy(self.ordering_index),
                    copy.deepcopy(self.negated))

    def set_parameter_variable(self, parameter_name: str, new_variable: str, force: bool = False, index: int = None):
        if parameter_name not in self.atom_parameters.keys():
            self.atom_parameters[parameter_name] = [new_variable]
        else:
            if index is not None:
                self.atom_parameters[parameter_name][index] = new_variable
                return self
            for i, elem in enumerate(self.atom_parameters[parameter_name]):
                if (elem == '_' and new_variable != '_') or force:
                    self.atom_parameters[parameter_name][i] = new_variable
                    return self
            self.atom_parameters[parameter_name].append(new_variable)
        return self

    def set_variable_value(self, variable: str, value: str):
        for parameter, dict_variable_list in self.atom_parameters.items():
            for i, dict_variable in enumerate(dict_variable_list):
                if dict_variable == variable:
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
                string += elem
                if j < len(self.atom_parameters[parameter]) - 1:
                    string += ","
            if i < len(self.atom_parameters.keys()) - 1:
                string += ","

        return string + ")"


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
    comparison_value: str

    def set_variable_value(self, variable: str, value: str):
        if type(self.comparison_target) == Aggregate:
            self.comparison_target.set_variable_value(variable, value)
        if self.comparison_value == variable:
            self.comparison_value = value

    def __str__(self):
        return f"{str(self.comparison_target)} {comparison_relations[self.comparison_operator]}" \
               f" {self.comparison_value}"


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


@dataclass(frozen=True)
class Rule:
    head: ShortDisjunction | SimpleDisjunction
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

    def set_variable_value(self, parameter: str, value: str):
        if self.operation_lhs == parameter:
            self.operation_lhs = value
        if self.operation_rhs == parameter:
            self.operation_rhs = value

    def __str__(self):
        string: str = f'{self.operation_eq_variable} = ' if self.operation_eq_variable is not None else ''
        if not self.absolute_value:
            string += f"{self.operation_lhs} {condition_operation[self.operator]} {self.operation_rhs}"
        else:
            string += f"|{self.operation_lhs} {condition_operation[self.operator]} {self.operation_rhs}|"
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
        self.name = " ".join([substr.removesuffix("s") for substr in verb_in_clause.verb_name.split(' ')])
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


class CNLCompiler:

    def __init__(self):
        self.__compilation_result: str = ""
        self.decl_signatures: [Signature] = []

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
                    # self.__compilation_result +=
                    self.__compile_constant_definition_clause(definition_clause.clause)
            except IndexError:
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
                # self.__compilation_result +=
                self.__compile_constant_definition_clause(definition_clause.clause)
        # print(self.decl_signatures)
        return self

    def into(self, out_file: TextIO):
        out_file.write(self.__compilation_result)
        return self

    def __compile_compounded_clause_range(self, clause: CompoundedClause):
        compiled_string: str = ''
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
        atom: Atom = Atom(subject_in_clause.name,
                          {f'{subject_in_clause.name}': [f'{lhs}'
                                                         f'..{rhs}']})
        granularity_hierarchy: list[str] = []
        if clause.tail:
            for elem in clause.tail.pop().granularity_hierarchy:
                granularity_hierarchy.append(Object(elem).name)

        self.decl_signatures.append(Signature(subject_in_clause.name, [subject_in_clause.name], granularity_hierarchy,
                                              {'lower': int(lhs),
                                               'upper': int(rhs)}))
        compiled_string += str(Rule(head=atom, body=None))
        return compiled_string

    def __compile_compounded_clause_match(self, clause: CompoundedClause):
        compiled_string: str = ''
        subject_in_clause: Subject = Subject(clause.subject)
        compounded_match: CompoundedClauseMatch = clause.definition
        (lower, upper) = get_list_bounds(compounded_match.compounded_match_list)
        compounded_match_tail: list[CompoundedClauseMatchTail] = []
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
        for (i, elem) in enumerate(clause.definition.compounded_match_list):
            def_value: str = f'"{clause.definition.compounded_match_list[i]}"' if not \
                clause.definition.compounded_match_list[i].isdigit() else clause.definition.compounded_match_list[i]
            if not clause.definition.compounded_match_list[i].isdigit():
                atom: Atom = Atom(f'{subject_in_clause.name}',
                                  {f'{subject_in_clause.name}': [f'{def_value}']}, i)
                alphabetic_constants_set.add(clause.definition.compounded_match_list[i])
                ordered_constant_dict[clause.definition.compounded_match_list[i]] = i + 1
            else:
                atom: Atom = Atom(f'{subject_in_clause.name}',
                                  {f'{subject_in_clause.name}': [f'{def_value}']})
            if compounded_match_tail:
                for tail_elem in compounded_match_tail:
                    tail_value: str = f'"{tail_elem.definition_list[i]}"' if not \
                        tail_elem.definition_list[i].isdigit() else tail_elem.definition_list[i]
                    atom.set_parameter_variable(f'{Object(tail_elem.subject).name}',
                                                f'{tail_value}')
                    if not tail_elem.definition_list[i].isdigit():
                        alphabetic_constants_set.add(tail_elem.definition_list[i])
                        ordered_constant_dict[tail_elem.definition_list[i]] = i + 1
            compiled_string += str(Rule(head=atom, body=None))
        self.decl_signatures.append(
            Signature(subject_in_clause.name, [subject_in_clause.name] +
                      [Object(tail_elem.subject).name for tail_elem in compounded_match_tail],
                      granularity_hierarchy,
                      {'lower': lower,
                       'upper': upper},
                      True))
        return compiled_string

    def __compile_enumerative_definition_clause(self, clause: EnumerativeDefinitionClause):
        # print(clause)
        compiled_string: str = ''

        subject_in_clause: Subject = Subject(clause.subject)
        verb_name: str = " ".join([substr.removesuffix("s") for substr in clause.verb_name.split(' ')]).lower()

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
            atom.set_parameter_variable(object_name, objects_values[i])

        self.decl_signatures.append(Signature(verb_name, objects_list))

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
                    if type(elem.condition_clause) is ConditionBoundClause:
                        bounded_variable = BoundedVariable(elem.condition_variable, {'lower': elem.condition_clause.bound_lower,
                            'upper': elem.condition_clause.bound_upper})
                        conjunction.body.append(bounded_variable)
                    elif type(elem.condition_clause) is ConditionComparisonClause:
                        comparison = None
                        if type(elem.condition_clause.condition_expression[0]) is not ConditionOperation:
                            comparison = Comparison(elem.condition_clause.condition_operator,
                                                    elem.condition_variable,
                                                    elem.condition_clause.condition_expression[0])
                        else:
                            comparison = Comparison('equal to',
                                                    elem.condition_variable,
                                                    Operation(elem.condition_clause.condition_expression[0].expression_lhs,
                                                              elem.condition_clause.condition_expression[0]
                                                              .expression_operator.operator,
                                                              elem.condition_clause.condition_expression[0].expression_rhs,
                                                              None,
                                                              elem.condition_clause.condition_expression[0]
                                                              .expression_operator.absolute_value
                                                              ))
                        conjunction.body.append(comparison)
            for elem in where_in_clause.conditions:
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
        constant_definitions_dict[clause.subject.lower()] = clause.constant

    def __compile_quantified_choice_clause(self, clause: QuantifiedChoiceClause):
        old_subject_variable: str | None = None
        subject_in_clause: Subject = Subject(clause.subject_clause)
        verb_name: str = " ".join([substr.removesuffix("s") for substr in clause.verb_name.split(' ')]).lower()
        objects_in_foreach: list[Object] = []
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
                    clause_verb_atom.set_parameter_variable(verb_object.name, verb_object.variable)
                    old_subject_variable = subject_in_clause.variable
                    subject_in_clause.variable = subject.variable
                    tmp = verb_object.variable
        clause_subject_atom: Atom = self.__get_atom_from_signature_subject(subject_in_clause.name) \
            .set_parameter_variable(subject_in_clause.name, subject_in_clause.variable)
        clause_foreach_atoms: [Atom] = [self.__get_atom_from_signature_subject(foreach_object.name)
                                            .set_parameter_variable(foreach_object.name,
                                                                    foreach_object.variable) for
                                        foreach_object in objects_in_foreach]
        clause_object_variables: [Atom] = [self.__get_atom_from_signature_subject(object_clause_elem.name)
                                               .set_parameter_variable(object_clause_elem.name,
                                                                       object_clause_elem.variable) for
                                           object_clause_elem in objects_in_body if type(object_clause_elem) is Object]
        clause_object_variables_conj: Conjunction = Conjunction(clause_object_variables)
        for x, y in [(clause_subject_atom.atom_name,
                      clause_subject_atom.atom_parameters[clause_subject_atom.atom_name])]:
            for z in y:
                clause_verb_atom.set_parameter_variable(x, z)
        if old_subject_variable is not None:
            clause_subject_atom.set_parameter_variable(subject_in_clause.name, tmp, force=True)
            clause_verb_atom.set_parameter_variable(subject_in_clause.name, old_subject_variable, force=True)
        for x, y in [(elem.atom_name, elem.atom_parameters[elem.atom_name]) for elem in clause_foreach_atoms]:
            for z in y:
                clause_verb_atom.set_parameter_variable(x, z)
        for x, y in [(elem.atom_name, elem.atom_parameters[elem.atom_name]) for elem in clause_object_variables]:
            for z in y:
                clause_verb_atom.set_parameter_variable(x, z)
        clause_object_variables += verb_atom_in_body
        self.decl_signatures.append(Signature(verb_name,
                                              clause_verb_atom.atom_parameters.keys()))
        rule_body: Conjunction = Conjunction([clause_subject_atom] + clause_foreach_atoms)
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
        return str(rule)

    def __compile_strong_constraint_clause(self, constraint: StrongConstraintClause):
        # print(constraint)
        compiled_string: str = ''
        conjunction: Conjunction | None = None
        block_memory: ClauseBlockMemory = ClauseBlockMemory()
        if type(constraint.clauses) == list:
            compiled_clauses = []
            for clause in constraint.clauses:
                compiled_clause = None
                if type(clause) == SimpleClause:
                    compiled_clause = self.__compile_simple_clause(clause, block_memory)
                compiled_clauses.append(compiled_clause)
            block_memory.flush_all(on=compiled_clauses)
            conjunction = Conjunction(compiled_clauses)
        elif type(constraint.clauses) == AggregateClause:
            comparison_in_clause: ComparisonClause = constraint.comparison_clause
            aggregate: Aggregate = self.__compile_aggregate_clause(constraint.clauses)
            comparison: Comparison = Comparison(comparison_in_clause.condition_operator, aggregate,
                                                self.__make_substitution_value(comparison_in_clause.comparison_value))
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

        for elem in conjunction_list:
            compiled_string += str(Rule(head=None, body=elem))

        # print(compiled_string)
        return compiled_string

    def __compile_weak_constraint_clause(self, constraint: WeakConstraintClause):
        # print(constraint)
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
            comparison: Comparison = Comparison('equal to', aggregate, variable)
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
                comparison: Comparison = Comparison('equal to', aggregate, ag_variable)
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
            if type(body_in_clause.expression_rhs) is AggregateClause:
                subject_in_clause: Subject = Subject(body_in_clause.expression_rhs
                                                     .aggregate_body.aggregate_subject_clause)
                aggregate: Aggregate = self.__compile_aggregate_clause(body_in_clause.expression_rhs,
                                                                       in_subject=subject_in_clause)
                if not body_in_clause.expression_rhs.aggregate_body.active_form:
                    subject_variables_in_clause.append(subject_in_clause.variable)
                comparison: Comparison = Comparison('equal to', aggregate, ag_variable)
                clause_list.append(comparison)
                if body_in_clause.expression_rhs.ranging_clause:
                    clause_list.append(BoundedVariable(ag_variable, {
                        'lower': self.__make_substitution_value(body_in_clause.expression_rhs
                                                                .ranging_clause.ranging_lhs),
                        'upper': self.__make_substitution_value(body_in_clause.expression_rhs
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

        variable = f"-{variable}" if constraint.optimization_operator == 'maximized' else variable

        for elem in conjunction_list:
            compilation_string += str(Rule(head=None, body=elem,
                                           cost=[variable, str(priority_levels_map[constraint.priority_level])],
                                           discriminants=subject_variables_in_clause))

        return compilation_string

    def __compile_aggregate_clause(self, aggregate_clause: AggregateClause, in_subject: Subject = None):
        compiled_string: str = ''
        # print(aggregate_clause)

        aggregate_body_in_clause: AggregateBodyClause = aggregate_clause.aggregate_body
        aggregate_ranging_in_clause: RangingClause = aggregate_clause.ranging_clause
        aggregate_operator_in_clause: str = aggregate_clause.aggregate_operator
        subject_in_clause: Subject = Subject(aggregate_body_in_clause.aggregate_subject_clause) if in_subject is None \
            else in_subject
        verb_in_clause: Verb = Verb(aggregate_body_in_clause.aggregate_verb_clause)

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
            aggregate_verb_atom: Atom = self.__get_atom_from_signature_subject(verb_in_clause.name)
            aggregate_verb_atom.negated = verb_in_clause.is_negated
            aggregate_verb_atom.set_parameter_variable(subject_in_clause.name, subject_in_clause.variable)
            aggregate_variable_list.append(subject_in_clause.variable)
            aggregate_body.append(aggregate_verb_atom)
            if not aggregate_body_in_clause.aggregate_for_clauses:
                if aggregate_objects_in_clause:
                    atom: Atom = self.__get_atom_from_signature_subject(aggregate_objects_in_clause[0].name)
                    self.__double_substitution(aggregate_verb_atom, aggregate_objects_in_clause[0].name, atom,
                                               aggregate_objects_in_clause[0].variable)
                    aggregate_objects_in_clause.pop(0)
                    aggregate_head.append(atom)
        else:
            aggregate_verb_atom: Atom = self.__get_atom_from_signature_subject(verb_in_clause.name)
            aggregate_verb_atom.negated = verb_in_clause.is_negated
            aggregate_body.append(aggregate_verb_atom)
            aggregate_subject_atom: Atom = self.__get_atom_from_signature_subject(subject_in_clause.name)
            self.__double_substitution(aggregate_verb_atom, subject_in_clause.name, aggregate_subject_atom,
                                       subject_in_clause.variable)
            aggregate_head.append(aggregate_subject_atom)

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

            join_atom: Atom | None = self.__find_join_atom_from_signature_subject(verb_in_clause.name,
                                                                                  ag_object.name)
            if join_atom is not None:
                self.__join_atoms(aggregate_verb_atom, ag_object.name, join_atom, variable)
                aggregate_body.append(join_atom)
            else:
                aggregate_verb_atom.set_parameter_variable(ag_object.name, variable)

        for for_object in for_objects_in_clause:
            atom: Atom = self.__get_atom_from_signature_subject(for_object.for_object.name)
            self.__double_substitution(aggregate_verb_atom, for_object.for_object.name, atom,
                                       for_object.for_object.variable)
            aggregate_head.append(atom)
        aggregate: Aggregate = Aggregate(aggregate_operator_in_clause, aggregate_variable_list,
                                         aggregate_body, aggregate_head)

        return aggregate

    def __make_substitution_value(self, string_to_check: str) -> str:
        if string_to_check.lower() in constant_definitions_dict.keys():
            return constant_definitions_dict[string_to_check.lower()]
        elif string_to_check in alphabetic_constants_set:
            return f'"{string_to_check}"'
        else:
            return string_to_check

    def __compile_simple_clause(self, clause: SimpleClause, block_memory: ClauseBlockMemory):
        # print(clause)
        result: Atom | Comparison | None = None
        subject_in_clause: Subject = Subject(clause.subject)
        if block_memory.subject_in_block is None:
            block_memory.set_subject_of_block(subject_in_clause)

        verb_in_clause: Verb = Verb(clause.verb_clause)
        simple_verb_atom: Atom = self.__get_atom_from_signature_subject(verb_in_clause.name)
        if subject_in_clause.name != block_memory.subject_in_block.name:
            simple_verb_atom.set_parameter_variable(block_memory.subject_in_block.name,
                                                    self.__make_substitution_value(
                                                        block_memory.subject_in_block.variable))
        else:
            simple_verb_atom.set_parameter_variable(subject_in_clause.name,
                                                    self.__make_substitution_value(
                                                        subject_in_clause.variable))
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
                    result = Comparison('different from', aggregate, consecution_count) if verb_in_clause.is_negated \
                        else Comparison('equal to', aggregate, consecution_count)
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
                                                    self.__make_substitution_value(value_for_subject))

        objects_in_clause: list[VerbObject] = []
        if type(clause.verb_clause.object_clause) == VerbObjectClause:
            objects_in_clause.append(VerbObject(clause.verb_clause.object_clause))
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
                result = Comparison('different from', aggregate, consecution_count) if verb_in_clause.is_negated \
                    else Comparison('equal to', aggregate, consecution_count)
                value_for_object = cls_object.variable
                block_memory.go_forward_in_time(of=consecution_count - 1,
                                                on_time_window_of=cls_object.consecution.consecution_object_name)

            simple_verb_atom.set_parameter_variable(cls_object.name,
                                                    self.__make_substitution_value(value_for_object))
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
                                                variable,
                                                elem.condition_clause.condition_expression[0])
                    else:
                        comparison = Comparison('equal to',
                                                variable,
                                                Operation(elem.condition_clause.condition_expression[0].expression_lhs,
                                                          elem.condition_clause.condition_expression[0]
                                                          .expression_operator.operator,
                                                          elem.condition_clause.condition_expression[0].expression_rhs,
                                                          None,
                                                          elem.condition_clause.condition_expression[0]
                                                          .expression_operator.absolute_value
                                                          ))
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
                              with_variable_name: str = None):
        join_variable: str = parameter.capitalize() if with_variable_name is None else with_variable_name
        if first_atom is not None:
            first_atom.set_parameter_variable(parameter, join_variable)
        if second_atom is not None:
            second_atom.set_parameter_variable(parameter, join_variable)

    def __find_join_atom_from_signature_subject(self, from_signature_subject: str, attribute: str) -> Atom | None:
        for signature_attribute in self.__get_signature(from_signature_subject).object_list:
            if signature_attribute == attribute:
                return None
            else:
                for attribute_signature_object in self.__get_signature(signature_attribute).object_list:
                    if attribute_signature_object == attribute:
                        return self.__get_atom_from_signature_subject(signature_attribute)

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
    def __get_atom_from_signature_subject(self, subject_in_signature: str):
        signature: Signature = self.__get_signature(subject_in_signature)
        atom: Atom = Atom(signature.subject, dict())
        for elem in signature.object_list:
            atom.set_parameter_variable(elem, '_')
        return atom

    def __get_signature_from_atom(self, atom: Atom) -> Signature:
        return self.__get_signature(atom.atom_name)

    def __get_signature(self, signature_name: str) -> Signature:
        return [elem for elem in self.decl_signatures if elem.subject == signature_name][0]
