from __future__ import annotations
from typing import TextIO

from cnl2asp.cnl.compile import DefinitionError, CNLCompiler
from cnl2asp.cnl.compile import CNLFile
from cnl2asp.cnl.compile import Signature

import lark



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
        cnl_file = None
        try:
            self.input_file.seek(0)
            cnl_file = CNLFile(self.input_file)
        except lark.exceptions.UnexpectedInput as err:
            print("Syntax error in input file:", err)
        return cnl_file

    def check_syntax(self) -> bool:
        """
        Check if the provided input fits the grammar.

        :return: True if the input fits the grammar; False otherwise.
        """
        if self.__parse_input():
            return True
        return False

    def compile(self) -> str:
        """
        Compile the input file into the ASP encoding.

        :return: the compiled string (ASP encoding).
        """
        cnl_file = self.__parse_input()
        if cnl_file:
            cnl_compiler: CNLCompiler = CNLCompiler()
            try:
                cnl_compiler.compile(cnl_file)
                return cnl_compiler.get_compiled_result()
            except DefinitionError as err:
                print(str(err), 'Compilation failed.')
                return ''

    def __convert_signature(self, signature: Signature) -> Symbol:
        symbol = Symbol(signature.subject, [], [])
        for attribute in signature.object_list:
            if isinstance(attribute, Signature):
                symbol.attributes.append(self.__convert_signature(attribute))
            else:
                symbol.attributes.append(attribute)
        for key in signature.primary_key:
            if isinstance(key, Signature):
                symbol.keys.append(self.__convert_signature(key))
            else:
                symbol.keys.append(key)
        return symbol


    def get_symbols(self) -> list[Symbol]:
        """
        Get all the concepts defined in the problem and their initialized structure.

        :return: list of symbols.
        """
        cnl_file = self.__parse_input()
        if cnl_file:
            cnl_compiler: CNLCompiler = CNLCompiler()
            try:
                cnl_compiler.compile(cnl_file)
                definitions: list[Symbol] = []
                for signature in cnl_compiler.decl_signatures:
                    definitions.append(self.__convert_signature(signature))
                return definitions
            except:
                return []
