from cnl2asp.parser.proposition_builder import PropositionBuilder
from cnl2asp.proposition.attribute_component import ValueComponent, AttributeComponent
from cnl2asp.proposition.entity_component import EntityComponent
from cnl2asp.proposition.operation_component import OperationComponent, Operators
from cnl2asp.proposition.problem import Problem
from cnl2asp.proposition.proposition import NewKnowledgeComponent


class Command:
    def execute(self):
        return


class SubstituteVariable(Command):
    def __init__(self, proposition: PropositionBuilder, variable: str, values: list[ValueComponent]):
        self.proposition = proposition
        self.variable = variable
        self.values = values

    def execute(self):
        new_propositions = []
        for proposition in self.proposition.get_propositions():
            for value in self.values:
                derived_proposition = proposition.copy()
                derived_proposition.add_requisite([OperationComponent(Operators.EQUALITY,
                                                                      ValueComponent(self.variable),
                                                                      value)])
                new_propositions.append(derived_proposition)
        self.proposition._original_rule = new_propositions[0]
        self.proposition._derived_rules = new_propositions[1:]


class RespectivelySubstituteVariable(Command):
    def __init__(self, proposition: PropositionBuilder, variable: str, values: list[ValueComponent]):
        self.proposition = proposition
        self.variable = variable
        self.values = values

    def execute(self):
        for proposition, value in zip(self.proposition.get_propositions(), self.values):
                proposition.add_requisite([OperationComponent(Operators.EQUALITY,
                                                                      ValueComponent(self.variable),
                                                                      value)])


class DurationClause(Command):
    def __init__(self, proposition: PropositionBuilder, new_knowledge: NewKnowledgeComponent,
                 duration_value: ValueComponent, attribute_name: str):
        self.proposition = proposition
        self.new_knowledge = new_knowledge
        self.duration_value = duration_value
        self.attribute_name = attribute_name

    def execute(self):
        self.proposition.duration_clause(self.new_knowledge, self.duration_value, self.attribute_name)


class CreateSignature(Command):
    def __init__(self, problem: Problem, proposition: PropositionBuilder, entity: EntityComponent):
        self.problem = problem
        self.proposition = proposition
        self.entity = entity

    def execute(self):
        try:
            signature = self.problem.get_signature(self.entity.name)
        except:
            signature = self.proposition.create_new_signature(self.entity)
            self.problem.add_signature(signature)
        signature.set_attributes_value(self.entity.get_keys_and_attributes())
        self.entity.keys = signature.keys
        self.entity.attributes = signature.attributes
