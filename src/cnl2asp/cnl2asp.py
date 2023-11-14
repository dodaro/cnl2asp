from __future__ import annotations
import os
import traceback
from typing import TextIO
from lark import Lark, UnexpectedCharacters
from lark.exceptions import VisitError

from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.exception.cnl2asp_exceptions import ParserError
from cnl2asp.proposition.attribute_component import AttributeComponent
from cnl2asp.proposition.entity_component import EntityComponent
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.parser.parser import CNLTransformer
from cnl2asp.proposition.problem import Problem
from cnl2asp.proposition.signaturemanager import SignatureManager


class Symbol:
    def __init__(self, predicate: str, keys: list[str | Symbol], attributes: list[str | Symbol]):
        """
        Class for representing the concepts (ASP atoms) structure.

        :param predicate:
        :param keys: the list of attributes that are keys.
        :param attributes: the FULL list (including the keys) of attributes of the atom.
        """
        self.predicate = predicate
        self.keys = keys
        self.attributes = attributes

    def __repr__(self):
        return f'{self.predicate}({self.attributes})'


class Cnl2asp:

    def __init__(self, input_file: TextIO):
        self.input_file = input_file

    def __parse_input(self):
        cnl_parser = Lark(open(os.path.join(os.path.dirname(__file__), "grammar.lark"), "r").read(),
                          propagate_positions=True)
        problem: Problem = CNLTransformer().transform(cnl_parser.parse(self.input_file.read()))
        return problem

    def check_syntax(self) -> bool:
        if self.__parse_input():
            return True
        return False

    def compile(self) -> str:
        try:
            problem: Problem = self.__parse_input()
        except UnexpectedCharacters as e:
            self.input_file.seek(0)
            print(ParserError(e.char, e.line, e.column, e.get_context(self.input_file.read()), list(e.allowed)))
            return ''
        except VisitError as e:
            print(e.orig_exc)
            return ''
        try:
            asp_converter: ASPConverter = ASPConverter()
            program: ASPProgram = problem.convert(asp_converter)
            SignatureManager().signatures = []
            return program.to_string()
        except Exception as e:
            print("Error in asp conversion:", str(e))
            return ''

    def __convert_attribute(self, entity_name: str, attribute: AttributeComponent) -> str | Symbol:
        if attribute.origin and entity_name != attribute.origin.name:
            return Symbol(attribute.origin.name,
                          [self.__convert_attribute(entity_name, AttributeComponent(attribute.name,
                                                                                    attribute.value,
                                                                                    attribute.origin.origin))],
                          [self.__convert_attribute(entity_name, AttributeComponent(attribute.name,
                                                                                    attribute.value,
                                                                                    attribute.origin.origin))])
        return attribute.name

    def __convert_signature(self, entity: EntityComponent) -> Symbol:
        keys = []
        attributes = []
        for attribute in entity.get_attributes():
            attributes.append(self.__convert_attribute(entity.name, attribute))
        if entity.get_attributes() != entity.get_keys():
            for key in entity.get_keys():
                keys.append(self.__convert_attribute(entity.name, key))
        return Symbol(entity.name, keys, keys + attributes)

    def get_symbols(self) -> list[Symbol]:
        self.compile()
        signatures: list[Symbol] = []
        for signature in SignatureManager().signatures:
            signatures.append(self.__convert_signature(signature))
        SignatureManager().signatures = []
        return signatures
