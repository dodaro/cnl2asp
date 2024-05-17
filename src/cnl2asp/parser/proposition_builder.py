from cnl2asp.exception.cnl2asp_exceptions import EntityNotFound, LabelNotFound
from cnl2asp.specification.relation_component import RelationComponent
from cnl2asp.specification.attribute_component import AttributeComponent, ValueComponent, RangeValueComponent
from cnl2asp.specification.component import Component
from cnl2asp.specification.entity_component import EntityComponent
from cnl2asp.specification.proposition import Proposition, NewKnowledgeComponent, CardinalityComponent, \
    PreferenceProposition, PREFERENCE_PROPOSITION_TYPE, ConditionComponent
from cnl2asp.utility.utility import Utility


class PropositionBuilder:

    def __init__(self, proposition: Proposition = None):
        self._original_rule: Proposition = proposition if proposition else Proposition()
        self._derived_rules: list[Proposition] = []

    def get_propositions(self) -> list[Proposition]:
        return [self._original_rule] + self._derived_rules

    def get_cardinality(self):
        return self._original_rule.cardinality

    def get_new_knowledge(self) -> list[NewKnowledgeComponent]:
        return [proposition.new_knowledge for proposition in self.get_propositions()]

    def get_relations(self) -> list[RelationComponent]:
        relations: list[RelationComponent] = []
        for proposition in self.get_propositions():
            for relation in proposition.relations:
                relations.append(relation)
        return relations

    def get_entities(self) -> list[EntityComponent]:
        return self._original_rule.get_entities()

    def get_entity_by_label(self, label: str) -> EntityComponent:
        for entity in self._original_rule.get_entities():
            if entity.label == label:
                return entity
        raise LabelNotFound(f"Label \"{label}\" not declared before.")

    def add_proposition(self, proposition: Proposition):
        self._derived_rules.append(proposition)

    def copy_proposition(self) -> Proposition:
        child = self._original_rule.copy()
        self._derived_rules.append(child)
        return child

    def add_cardinality(self, cardinality: CardinalityComponent):
        for proposition in self.get_propositions():
            proposition.cardinality = cardinality

    def add_requisite(self, component: Component):
        for proposition in self.get_propositions():
            proposition.requisite.components.append(component)

    def add_requisite_list(self, component: list[Component]):
        for proposition in self.get_propositions():
            proposition.requisite.components += component

    def add_new_knowledge(self, new_knowledge: NewKnowledgeComponent):
        for proposition in self.get_propositions():
            proposition.new_knowledge.append(new_knowledge)

    def add_relations(self, relations: list[RelationComponent]):
        for proposition in self.get_propositions():
            proposition.relations += relations

    def duration_clause(self, new_knowledge: NewKnowledgeComponent,
                        duration_value: ValueComponent, attribute_name: str):
        copy: Proposition = self._original_rule.copy()  # create the new proposition to express the duration
        new_knowledge.new_entity.set_name(Utility.create_unique_identifier())  # support entity
        copy.add_requisite([new_knowledge.new_entity])  # add the support entity to the new proposition requisite
        copy.new_knowledge[0].condition = ConditionComponent()
        copy.cardinality = None
        for copy_new_knowledge in copy.new_knowledge:
            # find the starting value of the temporal attribute
            try:
                entity = self._original_rule.get_entity_by_name(attribute_name)
            except EntityNotFound:
                entity = new_knowledge.new_entity
            if entity.is_temporal_entity():
                starting_value = entity.get_temporal_key().value
            else:
                starting_value = entity.get_attributes_by_name(attribute_name)[0].value
            # set the duration to the final entity
            copy_new_knowledge.new_entity.set_attribute_value(attribute_name,
                                                              RangeValueComponent(starting_value,
                                                                                  f'{starting_value}+{duration_value}'))
            copy.relations = []  # set the relations also for the copy
            for relation in self._original_rule.relations:
                for new_knowledge in self._original_rule.new_knowledge:
                    if new_knowledge.condition.components:
                        for entity in new_knowledge.condition.components:
                            # do not copy the entity related with the condition part, since
                            # it is not present in the new proposition
                            if not (relation.relation_component_1 == entity or relation.relation_component_2 == entity):
                                copy.relations.append(relation.copy())
                    else:
                        copy.relations.append(relation.copy())
            # the final entity is related with all the entities in requisite
            for requisite_entity in copy.requisite.get_entities():
                copy.relations.append(RelationComponent(copy_new_knowledge.new_entity, requisite_entity))
        self._derived_rules.append(copy)

    def create_new_signature(self, new_entity: EntityComponent) -> EntityComponent:
        return self._original_rule.create_new_signature(new_entity)

    def add_discriminant(self, discriminant: list[AttributeComponent]):
        pass

    def add_defined_attributes(self, defined_attributes: list[AttributeComponent]):
        for proposition in self.get_propositions():
            proposition.defined_attributes += defined_attributes

    def add_auxiliary_verb(self, param):
        for new_knowledge in self._original_rule.new_knowledge:
            new_knowledge.auxiliary_verb = param

    def add_subject(self, param):
        for new_knowledge in self._original_rule.new_knowledge:
            new_knowledge.subject = param


class PreferencePropositionBuilder(PropositionBuilder):
    def __init__(self, proposition: PreferenceProposition = None):
        preference_proposition = proposition if proposition else PreferenceProposition()
        super(PreferencePropositionBuilder, self).__init__(preference_proposition)

    def add_weight(self, weight: str):
        for proposition in self.get_propositions():
            proposition.weight = weight

    def add_level(self, level: int):
        for proposition in self.get_propositions():
            proposition.level = level

    def add_discriminant(self, discriminants: list[AttributeComponent]):
        for proposition in self.get_propositions():
            for discriminant in discriminants:
                if discriminant.value != Utility.NULL_VALUE:
                    proposition.add_discriminant(discriminant)

    def add_type(self, proposition_type: PREFERENCE_PROPOSITION_TYPE):
        for proposition in self.get_propositions():
            proposition.type = proposition_type
