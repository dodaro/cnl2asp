from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import traceback
from enum import Enum
from textwrap import indent
from typing import TextIO

from cnl2asp.parser.dl_compiler import DlTransformer
from cnl2asp.parser.telingo_compiler import TelingoTransformer
from cnl2asp.utility.utility import Utility
from lark import Lark, UnexpectedCharacters, Token, Tree
from lark.exceptions import VisitError

from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.converter.cnl2json_converter import Cnl2jsonConverter
from cnl2asp.exception.cnl2asp_exceptions import ParserError
from cnl2asp.specification.attribute_component import AttributeComponent
from cnl2asp.specification.entity_component import EntityComponent
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.parser.asp_compiler import ASPTransformer
from cnl2asp.specification.signaturemanager import SignatureManager
from cnl2asp.specification.specification import SpecificationComponent


class SymbolType(Enum):
    DEFAULT = 0
    TEMPORAL = 1


class Symbol:
    def __init__(self, predicate: str, keys: list[str | Symbol], attributes: list[str | Symbol],
                 symbol_type: SymbolType):
        """
        Class for representing the concepts (ASP atoms) structure.

        :param predicate:
        :param keys: the list of attributes that are keys.
        :param attributes: the FULL list (including the keys) of attributes of the atom.
        """
        self.predicate = predicate
        self.keys = keys
        self.attributes = attributes
        self.symbol_type = symbol_type

    def get_arity(self, print_with_functions=False):
        if print_with_functions:
            keys = set()
            for attribute in self.attributes:
                if isinstance(attribute, str):
                    keys.add(attribute)
                else:
                    keys.add(attribute.predicate)
            return len(keys)
        return len(self.attributes)

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return self.predicate == other.predicate and self.symbol_type == other.symbol_type \
                and collections.Counter(self.attributes) == collections.Counter(other.attributes) \
                and collections.Counter(self.keys) == collections.Counter(other.keys)
        return False

    def __repr__(self):
        attributes = f'\n{indent(str(self.attributes), "    ")}'
        return f'\n{self.predicate} [{self.symbol_type.name}]: {indent(attributes, "    ")}'

    def __hash__(self):
        return hash((self.predicate, tuple(self.attributes), tuple(self.keys), self.symbol_type))


class MODE(Enum):
    ASP = 0,
    TELINGO = 1
    DIFF_LOGIC = 2

class Cnl2asp:
    def __init__(self, cnl_input: TextIO | str, mode=MODE.ASP):
        if isinstance(cnl_input, str):
            self.cnl_input = cnl_input
            if os.path.isfile(cnl_input):
                self.cnl_input = open(cnl_input).read()
        else:
            self.cnl_input = cnl_input.read()
        self.mode = mode

    def get_grammar(self):
        res = ''
        with open(os.path.join(os.path.dirname(__file__), "grammars", "asp_grammar.lark"), "r") as grammar:
            res += grammar.read()
        if self.mode == MODE.TELINGO:
            with open(os.path.join(os.path.dirname(__file__), "grammars", "telingo_grammar.lark"), "r") as grammar:
                res += '\n'
                res += grammar.read()
        elif self.mode == MODE.DIFF_LOGIC:
            with open(os.path.join(os.path.dirname(__file__), "grammars", "dl_grammar.lark"), "r") as grammar:
                res += '\n'
                res += grammar.read()
        return res

    def get_transformer(self):
        if self.mode == MODE.ASP:
            return ASPTransformer()
        elif self.mode == MODE.TELINGO:
            return TelingoTransformer()
        elif self.mode == MODE.DIFF_LOGIC:
            return DlTransformer()

    def parse_input(self) -> Tree[Token]:
        try:
            cnl_parser = Lark(self.get_grammar(), propagate_positions=True)
            return cnl_parser.parse(self.cnl_input)
        except UnexpectedCharacters as e:
            raise ParserError(e.char, e.line, e.column, e.get_context(self.cnl_input),
                              self.cnl_input.splitlines()[e.line - 1],
                              list(e.allowed))

    def cnl_to_json(self):
        problem = ASPTransformer().transform(self.parse_input())
        converter = Cnl2jsonConverter()
        json = problem.convert(converter)
        return json

    def check_syntax(self) -> bool:
        if self.parse_input():
            return True
        return False

    def compile(self, auto_link_entities: bool = True) -> str:
        SignatureManager.signatures = []
        Utility.AUTO_ENTITY_LINK = auto_link_entities
        specification: SpecificationComponent = self.get_transformer().transform(self.parse_input())
        asp_converter: ASPConverter = ASPConverter()
        program: ASPProgram = specification.convert(asp_converter)
        return str(program)

    def optimize(self, asp_encoding: str, input_symbols: list[Symbol] = None, output_symbols: list[Symbol] = None,
                 print_with_functions=False):
        def symbol_to_clingo_predicate(symbols: list[Symbol]):
            res = []
            for symbol in symbols:
                res.append(Predicate(symbol.predicate, symbol.get_arity(print_with_functions)))
            return res

        from clingo.ast import parse_string
        from ngo import optimize, auto_detect_input, auto_detect_output, Predicate
        prg = []
        parse_string(asp_encoding, prg.append)
        input_predicates = auto_detect_input(prg)
        if input_symbols is not None:
            input_predicates = symbol_to_clingo_predicate(input_symbols)
        output_predicates = auto_detect_output(prg)
        if output_symbols is not None:
            output_predicates = symbol_to_clingo_predicate(output_symbols)
        return '\n'.join(map(str, optimize(prg, input_predicates, output_predicates)))

    def __get_type(self, name: str):
        if SignatureManager.is_temporal_entity(name):
            return SymbolType.TEMPORAL
        return SymbolType.DEFAULT

    def __convert_attribute(self, entity_name: str, attribute: AttributeComponent) -> str | Symbol:
        if attribute.origin and entity_name != attribute.origin.name:
            return Symbol(str(attribute.origin.name),
                          [self.__convert_attribute(entity_name, AttributeComponent(attribute.get_name(),
                                                                                    attribute.value,
                                                                                    attribute.origin.origin))],
                          [self.__convert_attribute(entity_name, AttributeComponent(attribute.get_name(),
                                                                                    attribute.value,
                                                                                    attribute.origin.origin))],
                          self.__get_type(attribute.origin.name)
                          )
        return attribute.get_name()

    def __convert_signature(self, entity: EntityComponent) -> Symbol:
        keys = []
        attributes = []
        for attribute in entity.get_attributes():
            attributes.append(self.__convert_attribute(entity.get_name(), attribute))
        entity_type = SymbolType.DEFAULT
        if SignatureManager.is_temporal_entity(entity.get_name()):
            entity_type = SymbolType.TEMPORAL
        if entity.get_attributes() != entity.get_keys():
            for key in entity.get_keys():
                keys.append(self.__convert_attribute(entity.get_name(), key))
        return Symbol(entity.get_name(), keys, keys + attributes, entity_type)

    def get_symbols(self) -> list[Symbol]:
        self.compile()
        signatures: list[Symbol] = []
        for signature in SignatureManager.signatures:
            signatures.append(self.__convert_signature(signature))
        SignatureManager.signatures = []
        return signatures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--check-syntax', action='store_true', help='Checks that the input fits the grammar')
    parser.add_argument('--cnl2json', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--symbols', action='store_true',
                        help='Return the list of symbols generated for the compilation')
    parser.add_argument('-p', '--print-with-functions', action='store_true',
                        help='Print atoms with functions. ')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--solve', action='store_true',
                        help='Call the corresponding solver and print a cnl-translated output')
    parser.add_argument('--telingo', action='store_true',
                        help='Generate a telingo encoding')
    parser.add_argument('--dl', action='store_true',
                        help='Generate a clingo dl encoding')
    parser.add_argument('-o', '--optimize', action='store_true', help='Optimize the output using ngo')
    parser.add_argument('--explain', action='store_true', help='Returns a cnl version of the best model')
    parser.add_argument('input_file')
    parser.add_argument('output_file', type=str, nargs='?', default='')
    args = parser.parse_args()

    Utility.PRINT_WITH_FUNCTIONS = args.print_with_functions
    mode = MODE.ASP
    if args.telingo:
        mode = MODE.TELINGO
    elif args.dl:
        mode = MODE.DIFF_LOGIC
    cnl2asp = Cnl2asp(args.input_file, mode)

    if args.check_syntax:
        if cnl2asp.check_syntax():
            print("Input file fits the grammar.")
    elif args.cnl2json:
        print(json.dumps(cnl2asp.cnl_to_json()))
    elif args.symbols:
        print(cnl2asp.get_symbols())
    else:
        try:
            asp_encoding = cnl2asp.compile()
        except VisitError as e:
            print(e.args[0])
            if args.debug:
                traceback.print_exception(e)
            return
        except Exception as e:
            print("Error in asp conversion:\n", str(e))
            if args.debug:
                traceback.print_exception(e)
            return

        if args.optimize:
            asp_encoding = cnl2asp.optimize(asp_encoding)
        try:
            out = sys.stdout
            if args.output_file:
                if str(asp_encoding):
                    print("Compilation completed.")
                out = open(args.output_file, "w")
            out.write(asp_encoding)
        except Exception as e:
            print("Error in writing output", str(e))

        if args.solve:
            if args.telingo:
                from cnl2asp.ASP_elements.solver.telingo_result_parser import TelingoResultParser
                from cnl2asp.ASP_elements.solver.telingo_wrapper import Telingo
                solver = Telingo()
                res_parser = TelingoResultParser(cnl2asp.get_transformer().transform(cnl2asp.parse_input()))
            else:
                from cnl2asp.ASP_elements.solver.clingo_wrapper import Clingo
                from cnl2asp.ASP_elements.solver.clingo_result_parser import ClingoResultParser
                solver = Clingo()
                res_parser = ClingoResultParser(cnl2asp.get_transformer().transform(cnl2asp.parse_input()))
            print("\n*********")
            print(f"Running {args.solve}...\n")
            solver.load(str(asp_encoding))
            res = solver.solve()
            if args.explain:
                model = res_parser.parse_model(res)
                print("\n\n" + model)
