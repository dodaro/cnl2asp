from __future__ import annotations

import collections
import os
import traceback
from typing import TextIO

from lark import Lark, UnexpectedCharacters
from lark.exceptions import VisitError

from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.converter.cnl2json_converter import Cnl2jsonConverter
from cnl2asp.exception.cnl2asp_exceptions import ParserError, EntityNotFound
from cnl2asp.specification.attribute_component import AttributeComponent
from cnl2asp.specification.entity_component import EntityComponent
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.parser.parser import CNLTransformer
from cnl2asp.specification.problem import Problem
from cnl2asp.specification.signaturemanager import SignatureManager
from cnl2asp.specification.specification import SpecificationComponent


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
    def __init__(self, cnl_input: TextIO | str):
        if isinstance(cnl_input, str):
            self.cnl_input = cnl_input
        else:
            self.cnl_input = cnl_input.read()

    def __parse_input(self):
        cnl_parser = Lark(open(os.path.join(os.path.dirname(__file__), "grammar.lark"), "r").read(),
                          propagate_positions=True)
        specification: SpecificationComponent = CNLTransformer().transform(cnl_parser.parse(self.cnl_input))
        return specification

    def __is_predicate(self, name: str):
        try:
            SignatureManager.get_signature(name)
            return True
        except:
            return False

    def __get_predicate(self, entity_name: str, attribute: AttributeComponent):
        split_name = attribute.name.split('_')
        if len(split_name) > 1:
            for name in split_name:
                if self.__is_predicate(name):
                    return SignatureManager.get_signature(name)
        signature_name = attribute.name
        if attribute.origin != entity_name:
            signature_name = attribute.origin.name
        if self.__is_predicate(signature_name):
            return SignatureManager.get_signature(signature_name)
        return None


    def cnl_to_json(self):
        problem = self.__parse_input()
        converter = Cnl2jsonConverter()
        json = problem.convert(converter)
        return json

    def check_syntax(self) -> bool:
        if self.__parse_input():
            return True
        return False

    def compile(self) -> str:
        try:
            specification: SpecificationComponent = self.__parse_input()
        except UnexpectedCharacters as e:
            print(ParserError(e.char, e.line, e.column, e.get_context(self.cnl_input), list(e.allowed)))
            return ''
        except VisitError as e:
            print(e.args[0])
            return ''
        try:
            asp_converter: ASPConverter = ASPConverter()
            program: ASPProgram = specification.convert(asp_converter)
            SignatureManager().signatures = []
            return str(program)
        except Exception as e:
            print("Error in asp conversion:", str(e))
            traceback.print_exception(e)
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
