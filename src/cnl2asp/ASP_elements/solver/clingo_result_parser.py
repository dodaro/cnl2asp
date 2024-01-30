from dataclasses import dataclass

import clingo
from cnl2asp.proposition.attribute_component import ValueComponent, AttributeComponent

from cnl2asp.proposition.entity_component import EntityComponent
from cnl2asp.proposition.problem import Problem


@dataclass(frozen=True)
class NewKnowledge:
    new_entity: EntityComponent
    subject: EntityComponent
    verb: str
    objects: list[EntityComponent]

# simple
# quantified
# whenever then
#

class ClingoResultParser:

    def __init__(self, specification: Problem, model: clingo.Model):
        self.specification = specification
        self.model = model
        self.target_predicates = []
        self._signatures: list[NewKnowledge] = []

    def _get_new_knowledge(self):
        for proposition in self.specification.get_propositions():
            for new_knowledge in proposition.new_knowledge:
                name = new_knowledge.new_entity.get_name()
                if name not in self.target_predicates:
                    self.target_predicates.append(new_knowledge.new_entity.get_name())
                    self._signatures.append(NewKnowledge(new_knowledge.new_entity.copy(),
                                            new_knowledge.subject, new_knowledge.auxiliary_verb, new_knowledge.objects))

    def _get_signature(self, name: str):
        for signature in self._signatures:
            if name == signature.new_entity.get_name():
                new_entity = signature.new_entity.copy()
                subject = signature.subject.copy() if signature.subject else signature.subject
                objects = [x.copy() for x in signature.objects] if signature.objects else signature.objects
                return NewKnowledge(new_entity, subject, signature.verb, objects)

    def _symbol_printer(self, symbol_name: str, attributes: list[AttributeComponent]):
        attributes_string = ''
        if len(attributes) == 1:
            attributes_string += f'{attributes[0].value}'
        else:
            for attribute in attributes:
                attributes_string += f'with {str(attribute).removeprefix(symbol_name).strip()} equal to {attribute.value}, '
        attributes_string = attributes_string.removesuffix(', ')
        name = ' '.join(symbol_name.split('_'))
        return f"{name} {attributes_string}".strip()

    def parameter_as_entity(self, subject: EntityComponent, atom: EntityComponent):
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
                atom.attributes.remove(attribute)
            res = self._symbol_printer(subject.get_name(), attributes_to_print)
        return res if res and res != subject.get_name() else "There"

    def verb(self, verb):
        if verb in ["be ", "be a ", "be an ", "are ", "are a ", "are an ", "is ", "is a ", "is an "]:
            return "is"
        elif verb in ["have ", "have a ", "have an ", "has ", "has a ", "has an "]:
            return "has"
        else:
            return "is"

    def clingosymbol_to_ASPAtom(self, symbol: clingo.Symbol, atom: EntityComponent):
        for idx, attribute in enumerate(atom.get_keys_and_attributes()):
            attribute.value = ValueComponent(symbol.arguments[idx])

    def atom_to_sentence(self, symbol: clingo.Symbol):
        signature = self._get_signature(symbol.name)
        self.clingosymbol_to_ASPAtom(symbol, signature.new_entity)
        string = ''
        if signature.objects:
            for object_complement in signature.objects:
                string += self.parameter_as_entity(object_complement, signature.new_entity)
        subject = self.parameter_as_entity(signature.subject, signature.new_entity)
        if subject != "There":
            verb = self.verb(signature.verb)
        else:
            verb = "is"
        return f"{subject} {verb} " \
               f"{self._symbol_printer(signature.new_entity.get_name(), signature.new_entity.get_keys_and_attributes())} " \
               f"{string}".capitalize().strip() + "."

    def parse_model(self):
        self._get_new_knowledge()
        model = ''
        for elem in self.model.symbols(atoms=True):
            if elem.name in self.target_predicates:
                model += self.atom_to_sentence(elem) + '\n'
        return model