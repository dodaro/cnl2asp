class CompilationError(Exception):
    def __init__(self, msg: str, line: int):
        super(CompilationError, self).__init__(f"Compilation Error at line {line}: {msg}")


class EntityNotDefined(Exception):
    def __init__(self, msg: str):
        super(EntityNotDefined, self).__init__(msg)


class EntityNotFound(Exception):
    def __init__(self, msg: str):
        super(EntityNotFound, self).__init__(msg)


class AttributeNotFound(Exception):
    def __init__(self, msg: str):
        super(AttributeNotFound, self).__init__(msg)

class AttributeError(Exception):
    def __init__(self, msg: str):
        super(AttributeError, self).__init__(msg)

class ParserError(Exception):
    def __init__(self, msg: str):
        super(ParserError, self).__init__(f"Parser Error: {msg}")


class LabelNotFound(Exception):
    def __init__(self, msg: str):
        super(LabelNotFound, self).__init__(msg)
