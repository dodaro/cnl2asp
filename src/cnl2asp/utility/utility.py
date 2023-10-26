from uuid import uuid4


class Utility:
    NULL_VALUE = '_'
    ASP_NULL_VALUE = '_'
    PRINT_WITH_FUNCTIONS = False
    DEFAULT_ATTRIBUTE = 'id'
    __set_id = 0

    @staticmethod
    def create_unique_identifier():
        return 'x_' + str(uuid4()).replace('-', '_')

    @staticmethod
    def generate_set_id():
        Utility.__set_id += 1
        return Utility.__set_id
