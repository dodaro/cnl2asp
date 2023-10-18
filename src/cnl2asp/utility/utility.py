from uuid import uuid4


class Utility:
    NULL_VALUE = '_'
    ASP_NULL_VALUE = '_'
    PRINT_WITH_FUNCTIONS = False
    DEFAULT_ATTRIBUTE = 'id'

    @staticmethod
    def create_unique_identifier():
        return 'x_' + str(uuid4()).replace('-', '_')
