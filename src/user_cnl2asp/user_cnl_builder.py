import dataclasses

from lark import Tree
from lark.visitors import Interpreter
import random
import string

@dataclasses.dataclass()
class ProductionRule:
    head: str
    body: str

    def __str__(self):
        return f'{self.head}: {self.body}'


class Importer:
    def __init__(self, grammar_path: str):
        grammar = open(grammar_path, 'r')
        self.grammar = grammar.read()
        grammar.close()
        self.common_libraries = ["", "WS", "LETTER", "INT", "UCASE_LETTER", "LCASE_LETTER", "_EXP", "CPP_COMMENT",
                                 "C_COMMENT"]
        self.imported_rules: list[str] = ['STRING', 'PARAMETER_NAME']

    def find_rule(self, rule_name: str) -> str:
        rule = ''
        lines = self.grammar.splitlines()
        for idx, line in enumerate(lines):
            if line.removeprefix('?').removeprefix('!').startswith(rule_name):
                rule += line
                while lines[idx + 1].strip().startswith('|'):
                    rule += lines[idx + 1]
                    idx += 1
                return rule
        return ''

    def remove_string_tokens(self, rule: str) -> str:
        indexes = [i for i in range(len(rule)) if rule.startswith('\"', i)]
        indexes = indexes[-1::-1]
        for end, start in zip(indexes[0::2], indexes[1::2]):
            rule = rule[0:start - 1] + rule[end + 1::]
        return rule

    def clear_token(self, token: str):
        elements = ['(', ')', '[', ']', '?', '\n', '*', '+', '\"']
        for element in elements:
            token = token.replace(element, '').strip()
        return token

    def find_rule_dependencies(self, rule: str) -> list[str]:
        if rule.startswith('EXPRESSION'):
            print()
        dependencies: list[str] = []
        rules = ''.join(rule.split(':')[1::]).split('|')
        for rule in rules:
            rule = rule.split('->')[0]  # remove labels
            rule = self.remove_string_tokens(rule)
            dependencies += rule.split(' ')
        return [self.clear_token(x) for x in dependencies if self.clear_token(x) not in self.common_libraries]

    def import_rule(self, rule_name: str):
        rule = self.find_rule(rule_name) + '\n'
        if not rule:
            raise Exception('Rule not found')
        self.imported_rules.append(rule_name)
        dependencies = self.find_rule_dependencies(rule)
        for dependence in dependencies:
            if dependence not in self.imported_rules:
                if dependence == '"':
                    print()
                self.imported_rules.append(dependence)
                rule += self.import_rule(dependence) + '\n'
        return rule


class Grammar:
    def __init__(self):
        self.production_rules: list[ProductionRule] = []
        # support_rules are elements that can be used inside production rules
        self.support_rules: list[ProductionRule] = []
        self.rule_functions: dict[str, [str]] = dict()
        self.importer: Importer = Importer('cnl2asp/grammar.lark')

    def import_rule(self, rule_name: str):
        self.importer.import_rule(rule_name)

    def add_rule(self, production_rule: ProductionRule):
        if production_rule.head and production_rule.body:
            self.production_rules.append(production_rule)

    def add_function(self, production_rule_head: str, function: str):
        if self.rule_functions.get(production_rule_head):
            self.rule_functions[production_rule_head] += function
        else:
            self.rule_functions[production_rule_head] = function

    def has_production_rule(self, head: str):
        for rule in self.production_rules:
            if rule.head == head:
                return True
        return False

    def has_support_rule(self, head: str):
        for rule in self.support_rules:
            if rule.head == head:
                return True
        return False

    def is_support_rule(self, support_rule: ProductionRule):
        if support_rule in self.support_rules:
            return True
        return False

    def __str__(self):
        grammar = f''' 
%import common.WS
%import common.LETTER
%import common.INT
%import common.UCASE_LETTER
%import common.LCASE_LETTER
%import common._EXP
%import common.CPP_COMMENT
%import common.C_COMMENT

%ignore WS
%ignore CPP_COMMENT
%ignore C_COMMENT
'''
        rules_to_import = [x for x in self.importer.imported_rules if not self.has_production_rule(x)]
        if rules_to_import:
            grammar += f'%import .cnl2asp.grammar ({", ".join(rules_to_import)})\n'
        for rule in self.support_rules:
            grammar += str(rule) + '\n'
        grammar += '\n'
        for rule in self.production_rules[-1::-1]:
            grammar += str(rule) + '\n'
        return grammar


class TreeInterpreter(Interpreter):
    def __init__(self):
        super(TreeInterpreter, self).__init__()
        self.grammar: Grammar = Grammar()
        self.functions_map = {
            'assignment': 'assignment',
            'choice': 'choice',
            'preference': 'preference',
            'constraint': 'constraint',
            'aggregate': 'aggregate',
            'aggregate.operator.sum': 'aggregate_sum',
            'aggregate.operator.count': 'aggregate_count',
            'aggregate.operator.min': 'aggregate_min',
            'aggregate.operator.max': 'aggregate_max',
            'operation': 'operation',
            'operation.operand': 'operation_operand',
            'operation.operator': 'operation_operator',
            'operation.operator.sum': 'operation_sum',
            'operation.operator.difference': 'operation_difference',
            'operation.operator.multiplication': 'operation_multiplication',
            'operation.operator.division': 'operation_division',
            'operation.operator.equality': 'operation_equality',
            'operation.operator.inequality': 'operation_inequality',
            'operation.operator.greater_than': 'operation_greater_than',
            'operation.operator.less_than': 'operation_less_than',
            'operation.operator.greater_than_or_equal_to': 'operation_greater_than_or_equal_to',
            'operation.operator.less_than_or_equal_to': 'operation_less_than_or_equal_to',
            'operation.operator.conjunction': 'operation_conjunction',
            'operation.operator.disjunction': 'operation_disjunction',
            'operation.operator.left_implication': 'operation_left_implication',
            'operation.operator.right_implication': 'operation_right_implication',
            'operation.operator.equivalence': 'operation_equivalence',
            'operation.operator.negation': 'operation_negation',
            'operation.operator.previous': 'operation_previous',
            'operation.operator.weak_previous': 'operation_weak_previous',
            'operation.operator.trigger': 'operation_trigger',
            'operation.operator.always_before': 'operation_always_before',
            'operation.operator.since': 'operation_since',
            'operation.operator.eventually_before': 'operation_eventually_before',
            'operation.operator.precede': 'operation_precede',
            'operation.operator.weak_precede': 'operation_weak_precede',
            'operation.operator.next': 'operation_next',
            'operation.operator.weak_next': 'operation_weak_next',
            'operation.operator.release': 'operation_release',
            'operation.operator.always_after': 'operation_always_after',
            'operation.operator.until': 'operation_until',
            'operation.operator.eventually_after': 'operation_eventually_after',
            'operation.operator.follow': 'operation_follow',
            'operation.operator.weak_follow': 'operation_weak_follow',
            'body': 'add_requisite',
            'head': 'add_new_knowledge',
            'aggregate.operator': 'aggregate_operator',
            'aggregate.discriminant': 'aggregate_discriminant',
            'aggregate.body': 'aggregate_body',
            'condition': 'add_condition',
            'add_proposition': 'add_proposition'
        }

    def _generate_production_rule_id(self):
        return ''.join(random.choices(string.ascii_lowercase, k=10))

    def start(self, tree: Tree):
        start_production_rule: ProductionRule = ProductionRule('start', '((')
        for idx, child in enumerate(tree.children):
            production_rule = self.visit(child)
            if production_rule and not self.grammar.is_support_rule(production_rule):
                self.grammar.add_rule(production_rule)
                start_production_rule.body += production_rule.head
                if idx + 1 < len(tree.children):
                    start_production_rule.body += ' | '
        start_production_rule.body += ') /\./ )*'
        self.grammar.add_rule(start_production_rule)

    def import_rule(self, tree: Tree):
        rule_name = self.visit(tree.children[0])
        self.grammar.import_rule(rule_name)
        if rule_name != 'entity':
            return ProductionRule(rule_name, '')

    def rule_name(self, tree: Tree):
        return tree.children[0].value

    def rule(self, tree: Tree):
        context = self.visit(tree.children[0])
        production_rule: ProductionRule = self.visit(tree.children[1])
        self.grammar.add_function(production_rule.head, context)
        return production_rule

    def context(self, tree: Tree):
        return self.functions_map.get(tree.children[1].value)

    def support_proposition(self, tree: Tree) -> ProductionRule:
        production_rule: ProductionRule = ProductionRule(tree.children[0].value, self.visit(tree.children[1]))
        self.grammar.support_rules.append(production_rule)
        return production_rule

    def proposition(self, tree: Tree):
        return ProductionRule(self._generate_production_rule_id(), self.visit(tree.children[0]))

    def dummy(self, tree: Tree):
        return self.visit(tree.children[0])

    def structural_proposition(self, tree: Tree) -> str:
        body: str = ''
        for child in tree.children:
            if isinstance(child, Tree):
                body += self.visit(child) + ' '
            else:
                body += child.value
        return body

    def structural_token(self, tree: Tree) -> str:
        structural_token = ''
        for child in tree.children:
            if child.value == '\"':
                structural_token = structural_token.strip()
            structural_token += child.value
            if child.value != '\"':
                structural_token += ' '
        return structural_token

    def token(self, tree: Tree):
        value = tree.children[0].value.lower() + self._generate_production_rule_id()
        if not self.grammar.has_production_rule(value):
            if tree.children[0].value.lower() in self.grammar.importer.imported_rules:
                self.grammar.add_rule(ProductionRule(value, tree.children[0].value.lower()))
            elif self.grammar.has_support_rule(tree.children[0].value.lower()):
                self.grammar.add_rule(ProductionRule(value, tree.children[0].value.lower()))
            else:
                self.grammar.add_rule(ProductionRule(value, 'STRING'))
            for child in self.visit(tree.children[2]):
                self.grammar.add_function(value, child)
        return value

    def command_list(self, tree: Tree):
        functions = []
        for function in tree.children:
            functions.append(self.functions_map.get(function.value))
        return functions
