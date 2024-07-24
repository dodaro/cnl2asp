from dataclasses import dataclass

import clingo
from clingo.solving import _SymbolSequence

from cnl2asp.specification.attribute_component import ValueComponent, AttributeComponent
from cnl2asp.specification.entity_component import EntityComponent
from cnl2asp.specification.specification import SpecificationComponent


@dataclass(frozen=True)
class NewKnowledge:
    new_entity: EntityComponent
    subject: list[EntityComponent]
    verb: str
    objects: list[EntityComponent]


class ClingoResultParser:

    def __init__(self, specification: SpecificationComponent):
        self.specification = specification
        self.target_predicates = []
        self._signatures: list[NewKnowledge] = []

    def _get_new_knowledge(self):
        for programs in self.specification.get_problems():
            for proposition in programs.get_propositions():
                for new_knowledge in proposition.new_knowledge:
                    name = new_knowledge.new_entity.get_name()
                    if name not in self.target_predicates:
                        self.target_predicates.append(new_knowledge.new_entity.get_name())
                        subject = [new_knowledge.subject] if new_knowledge.subject else []
                        self._signatures.append(NewKnowledge(new_knowledge.new_entity.copy(),
                                                             subject, new_knowledge.auxiliary_verb,
                                                             new_knowledge.objects))
                    else:
                        for signature in self._signatures:
                            if signature.new_entity and name == signature.new_entity.get_name():
                                if new_knowledge.subject and new_knowledge.subject.get_name() \
                                        not in [x.get_name() for x in signature.subject]:
                                    signature.subject.append(new_knowledge.subject)

    def _get_signature(self, name: str):
        for signature in self._signatures:
            if name == signature.new_entity.get_name():
                new_entity = signature.new_entity.copy()
                subject = [x.copy() for x in signature.subject.copy()] if signature.subject else signature.subject
                objects = [x.copy() for x in signature.objects] if signature.objects else signature.objects
                return NewKnowledge(new_entity, subject, signature.verb, objects)

    def _entity_printer(self, symbol_name: str, attributes: list[AttributeComponent]):
        attributes_string = ''
        if len(attributes) == 1:
            attributes_string += f'{attributes[0].value}'
        else:
            for attribute in attributes:
                attributes_string += f'with {str(attribute).removeprefix(symbol_name).strip()} equal to {attribute.value}, '
        attributes_string = attributes_string.removesuffix(', ')
        name = ' '.join(symbol_name.split('_'))
        return f"{name} {attributes_string}".strip()

    def _convert_attribute_to_entity(self, subject: EntityComponent, atom: EntityComponent):
        res = ''
        if subject:
            attributes_to_print = []
            for attribute in atom.get_keys_and_attributes():
                try:
                    subject_attribute = subject.get_attributes_by_name_and_origin(attribute.get_name(), attribute.origin)[0]
                    subject.get_keys().remove(subject_attribute)
                    attributes_to_print.append(attribute)
                except:
                    pass
            for attribute in attributes_to_print:
                try:
                    atom.attributes.remove(attribute)
                except ValueError:
                    pass
                try:
                    atom.keys.remove(attribute)
                except ValueError:
                    pass
            res = self._entity_printer(subject.get_name(), attributes_to_print)
        return res if res and res != subject.get_name() else "There"

    def _convert_verb(self, verb):
        if verb in ["be ", "be a ", "be an ", "are ", "are a ", "are an ", "is ", "is a ", "is an "]:
            return "is "
        elif verb in ["have ", "have a ", "have an ", "has ", "has a ", "has an "]:
            return "has "
        return ""

    def _parse_clingo_symbol(self, symbol: clingo.Symbol, entity: EntityComponent):
        for idx, attribute in enumerate(entity.get_keys_and_attributes()):
            try:
                attribute.value = ValueComponent(str(symbol.arguments[idx]).removeprefix('\"').removesuffix('\"'))
            except AttributeError:
                attribute.value = ValueComponent(symbol.arguments[idx])

    def _attributes_intersection(self, entity_1: EntityComponent, entity_2: EntityComponent):
        matched_attributes = []
        for attribute in entity_1.get_keys():
            try:
                match = entity_2.get_attributes_by_name_and_origin(attribute.get_name(), attribute.origin)
                matched_attributes += match
            except:
                pass
        return matched_attributes

    def _has_same_value_attribute(self, attribute: AttributeComponent, entity: EntityComponent) -> bool:
        try:
            match = entity.get_attributes_by_name_and_origin(attribute.get_name(), attribute.origin)
            for value in match:
                if attribute.value == value.value:
                    return True
        except:
            return False

    def _check_attributes_list(self, attributes: list[AttributeComponent], entity: EntityComponent) -> bool:
        for attribute in attributes:
            if not self._has_same_value_attribute(attribute, entity):
                return False
        return True

    def _search_entity(self, entity_name: str, attributes: list[AttributeComponent]):
        for programs in self.specification.get_problems():
            for proposition in programs.get_propositions():
                for new_knowledge in proposition.new_knowledge:
                    if new_knowledge.new_entity.get_name() == entity_name:
                        if self._check_attributes_list(attributes, new_knowledge.new_entity):
                            return new_knowledge.new_entity.copy()

    def _convert_subject(self, subject: list[EntityComponent], atom: EntityComponent):
        if len(subject) == 1:
            return self._convert_attribute_to_entity(subject[0], atom)
        elif not subject:
            return self._convert_attribute_to_entity(None, atom)
        elif len(subject) > 1:
            for entity in subject:
                attributes = self._attributes_intersection(entity, atom)
                if self._search_entity(entity.get_name(), attributes):
                    return self._convert_attribute_to_entity(entity, atom)

    def _clingo_symbol_to_sentence(self, symbol: clingo.Symbol):
        signature = self._get_signature(symbol.name)
        self._parse_clingo_symbol(symbol, signature.new_entity)
        string = ''
        subject = self._convert_subject(signature.subject, signature.new_entity)
        if subject != "There":
            verb = self._convert_verb(signature.verb)
        else:
            verb = "is "
        if signature.objects:
            for object_complement in signature.objects:
                string += self._convert_attribute_to_entity(object_complement, signature.new_entity)
        return f"{subject} {verb}" \
               f"{self._entity_printer(signature.new_entity.get_name(), signature.new_entity.get_keys_and_attributes())} " \
               f"{string}".capitalize().strip() + "."

    def parse_model(self, model: list[str]):
        self._get_new_knowledge()
        res = ''
        for elem in model:
            elem = clingo.parse_term(elem.strip())
            if elem.name in self.target_predicates:
                res += self._clingo_symbol_to_sentence(elem) + '\n'
        return res
