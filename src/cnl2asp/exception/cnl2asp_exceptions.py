class CompilationError(Exception):
    def __init__(self, msg: str, line: int):
        msg = msg.strip('\'')
        super(CompilationError, self).__init__(f"Compilation error at line {line}:\n    {msg}")


class EntityNotFound(Exception):
    def __init__(self, msg: str):
        super(EntityNotFound, self).__init__(msg)

class DuplicatedTypedEntity(Exception):
    def __init__(self, msg: str):
        super(DuplicatedTypedEntity, self).__init__(msg)

class AttributeNotFound(Exception):
    def __init__(self, msg: str):
        super(AttributeNotFound, self).__init__(msg)

class AttributeError(Exception):
    def __init__(self, msg: str):
        super(AttributeError, self).__init__(msg)

class ParserError(Exception):
    def __init__(self, msg: str, line: str):
        line_error = ''
        if line:
            line_error = f' at line {line}'
        super(ParserError, self).__init__(f"Parser Error{line_error}: {msg}")


class LabelNotFound(Exception):
    def __init__(self, msg: str):
        super(LabelNotFound, self).__init__(msg)

class TypeNotFound(Exception):
    def __init__(self, msg: str):
        super(TypeNotFound, self).__init__(msg)
