from collections import defaultdict
from token import LESSEQUAL

from cnl2asp.ASP_elements.asp_attribute import ASPValue
from cnl2asp.ASP_elements.asp_rule import ASPRule
from cnl2asp.specification.component import Component

from cnl2asp.specification.operation_component import Operators

from cnl2asp.ASP_elements.asp_operation import ASPOperation

from cnl2asp.ASP_elements.asp_atom import ASPAtom
from cnl2asp.ASP_elements.asp_theory_atom import TheoryAtom

from cnl2asp.specification.entity_component import EntityComponent

from cnl2asp.converter.asp_converter import ASPConverter, EntityToAtom
from cnl2asp.specification.proposition import Proposition, NewKnowledgeComponent


class DLConverter(ASPConverter):
    def __init__(self):
        super().__init__()
        self.dl_entities = set()
        self.visited_entities = set()
        self.asp_grounding_atoms = set()

    def clear_support_variables(self):
        super().clear_support_variables()
        self.dl_entities = set()
        self.visited_entities = set()
        self.asp_grounding_atoms = set()

    def _extract_dl_info(self, entity: EntityComponent):
        entity_name = entity.get_name()
        if entity_name in self.visited_entities:
            return
        self.visited_entities.add(entity_name)
        for attribute in entity.get_keys_and_attributes():
            if attribute.has_integer_domain:
                self.dl_entities.add(entity_name)
                return

    def _create_dl_atom(self, entity) -> ASPOperation:
        theory_atom_body = []
        atom_attributes = []
        for attribute in entity.get_keys_and_attributes():
            if attribute.has_integer_domain:
                theory_atom_body.append(attribute.convert(self))
            else:
                atom_attributes.append(attribute.convert(self))

        atom = ASPAtom(entity.get_name(), atom_attributes, entity.negated, entity.is_before,
                       entity.is_after, entity.is_initial, entity.is_final)
        theory_atom_body.append(atom)
        self._atoms_in_current_rule.append(EntityToAtom(entity, atom))
        return ASPOperation(Operators.LESS_THAN_OR_EQUAL_TO, TheoryAtom('diff', [ASPOperation(Operators.DIFFERENCE, *theory_atom_body)]), ASPValue(0))

    def convert_proposition(self, proposition: Proposition) -> ASPRule | None:
        if proposition.user_info.is_optional_rule:
            return None
        for atom in proposition.user_info.optional_atoms:
            self.asp_grounding_atoms.add(atom)
        return super().convert_proposition(proposition)

    def convert_entity(self, entity: EntityComponent) -> ASPOperation | ASPAtom:
        if entity.get_name() in self.asp_grounding_atoms:
            return ASPAtom('', [], entity.negated, entity.is_initial, entity.is_final)
        self._extract_dl_info(entity)
        if entity.get_name() in self.dl_entities:
            return self._create_dl_atom(entity)
        atom = ASPAtom(entity.get_name(), [attribute.convert(self) for attribute in entity.get_keys_and_attributes()],
                       entity.negated, entity.is_before, entity.is_after, entity.is_initial, entity.is_final)
        self._atoms_in_current_rule.append(EntityToAtom(entity, atom))
        return atom

    def entity_to_atoms_and_link(self, entity_1: EntityComponent, entity_2: EntityComponent,
                                 new_knowledge: NewKnowledgeComponent = None):
        if entity_1.get_name() in self.asp_grounding_atoms or entity_2.get_name() in self.asp_grounding_atoms:
            return
        else:
            super().entity_to_atoms_and_link(entity_1, entity_2, new_knowledge)
