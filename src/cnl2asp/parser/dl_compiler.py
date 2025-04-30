from cnl2asp.parser.asp_compiler import ASPTransformer
from cnl2asp.specification.proposition import NewKnowledgeComponent


class DlTransformer(ASPTransformer):
    def __init__(self):
        super().__init__()

    def dl_head(self, elem):
        self._proposition.add_new_knowledge(NewKnowledgeComponent(elem[0]))
