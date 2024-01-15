from uuid import uuid4


class Utility:
    NULL_VALUE = '_'
    ASP_NULL_VALUE = '_'
    PRINT_WITH_FUNCTIONS = False
    DEFAULT_ATTRIBUTE = 'id'
    LOCKED_KEYWORDS = ["is", "identified", "and", "equal", "to", "are", "has", "be", "have", "by", "with", "in",
                       "exactly", "at", "most", "least", "any", "every", "more", "less", "greater", "after", "highest",
                       "lowest", "smallest", "biggest", "sum", "difference", "product", "division", "where", "between",
                       "whenever", "such", "that", "there", "than", "also", "then", "required", "prohibited", "or"]

    @staticmethod
    def create_unique_identifier():
        return 'x_' + str(uuid4()).replace('-', '_')

