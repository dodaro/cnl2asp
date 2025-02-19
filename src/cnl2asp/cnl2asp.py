from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import tempfile
import traceback
from enum import Enum
from textwrap import indent
from typing import TextIO

from cnl2asp.utility.utility import Utility
from lark import Lark, UnexpectedCharacters, Token, Tree
from lark.exceptions import VisitError

from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.converter.cnl2json_converter import Cnl2jsonConverter
from cnl2asp.exception.cnl2asp_exceptions import ParserError
from cnl2asp.specification.attribute_component import AttributeComponent
from cnl2asp.specification.entity_component import EntityComponent
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.parser.parser import CNLTransformer
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


class Cnl2asp:
    def __init__(self, cnl_input: TextIO | str, debug: bool = False):
        self._debug = debug
        if isinstance(cnl_input, str):
            self.cnl_input = cnl_input
            if os.path.isfile(cnl_input):
                self.cnl_input = open(cnl_input).read()
        else:
            self.cnl_input = cnl_input.read()

    def parse_input(self) -> Tree[Token]:
        with open(os.path.join(os.path.dirname(__file__), "grammar.lark"), "r") as grammar:
            cnl_parser = Lark(grammar.read(), propagate_positions=True)
            return cnl_parser.parse(self.cnl_input)


    def __is_predicate(self, name: str):
        try:
            SignatureManager.clone_signature(name)
            return True
        except:
            return False

    def __get_predicate(self, entity_name: str, attribute: AttributeComponent):
        split_name = attribute.get_name().split('_')
        if len(split_name) > 1:
            for name in split_name:
                if self.__is_predicate(name):
                    return SignatureManager.clone_signature(name)
        signature_name = attribute.get_name()
        if attribute.origin != entity_name:
            signature_name = attribute.origin.name
        if self.__is_predicate(signature_name):
            return SignatureManager.clone_signature(signature_name)
        return None

    def cnl_to_json(self):
        problem = CNLTransformer().transform(self.parse_input())
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
        specification: SpecificationComponent = CNLTransformer().transform(self.parse_input())
        asp_converter: ASPConverter = ASPConverter()
        program: ASPProgram = specification.convert(asp_converter)
        return str(program)

    def optimize(self, asp_encoding: str, input_symbols: list[Symbol] = None, output_symbols: list[Symbol] = None,
                 print_with_functions=False):
        from clingo.ast import parse_files
        from ngo import optimize, auto_detect_input, auto_detect_output, Predicate
        prg = []
        with tempfile.NamedTemporaryFile(mode="w") as file:
            file.write(asp_encoding)
            file.seek(0)
            parse_files([file.name], prg.append)
            input_predicates = auto_detect_input(prg)
            if input_symbols is not None:
                input_predicates = []
                for symbol in input_symbols:
                    input_predicates.append(Predicate(symbol.predicate, symbol.get_arity(print_with_functions)))
            output_predicates = auto_detect_output(prg)
            if output_symbols is not None:
                output_predicates = []
                for symbol in output_symbols:
                    output_predicates.append(Predicate(symbol.predicate, symbol.get_arity(print_with_functions)))
            prg = optimize(prg, input_predicates, output_predicates)
            optimized_encoding = ''
            for stm in prg:
                optimized_encoding += str(stm) + '\n'
        return optimized_encoding

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
    parser.add_argument('--solve', type=str, choices=["clingo", "telingo"],
                        help='Call the corresponding solver and print a cnl-translated output')
    parser.add_argument('-o', '--optimize', action='store_true', help='Optimize the output using ngo')
    parser.add_argument('--explain', action='store_true', help='Returns a cnl version of the best model')
    parser.add_argument('input_file')
    parser.add_argument('output_file', type=str, nargs='?', default='')
    args = parser.parse_args()

    Utility.PRINT_WITH_FUNCTIONS = args.print_with_functions

    input_file = args.input_file

    in_file = open(input_file, 'r')
    cnl2asp = Cnl2asp(in_file, args.debug)
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
        except UnexpectedCharacters as e:
            in_file.seek(0)
            cnl_input = in_file.read()
            print(ParserError(e.char, e.line, e.column, e.get_context(cnl_input), cnl_input.splitlines()[e.line - 1],
                              list(e.allowed)))
            return ''
        except VisitError as e:
            print(e.args[0])
            if args.debug:
                traceback.print_exception(e)
            return ''
        except Exception as e:
            print("Error in asp conversion:", str(e))
            if args.debug:
                traceback.print_exception(e)
            return ''

        if args.optimize:
            asp_encoding = cnl2asp.optimize(asp_encoding)
        try:
            out = sys.stdout
            if args.output_file:
                if str(asp_encoding):
                    print("Compilation completed.")
                out = open(args.output_file, "w")
            out.write(asp_encoding)
            if args.solve:
                if args.solve == "clingo":
                    from cnl2asp.ASP_elements.solver.clingo_wrapper import Clingo
                    from cnl2asp.ASP_elements.solver.clingo_result_parser import ClingoResultParser
                    solver = Clingo()
                    res_parser = ClingoResultParser(CNLTransformer().transform(cnl2asp.parse_input()))
                elif args.solve == "telingo":
                    from cnl2asp.ASP_elements.solver.telingo_result_parser import TelingoResultParser
                    from cnl2asp.ASP_elements.solver.telingo_wrapper import Telingo
                    solver = Telingo()
                    res_parser = TelingoResultParser(CNLTransformer().transform(cnl2asp.parse_input()))
                else:
                    raise Exception(f"{args.solve} not recognised")
                print("\n*********")
                print(f"Running {args.solve}...\n")
                solver.load(str(asp_encoding))
                res = solver.solve()
                if args.explain:
                    model = res_parser.parse_model(res)
                    print("\n\n" + model)
        except Exception as e:
            print("Error in writing output", str(e))
