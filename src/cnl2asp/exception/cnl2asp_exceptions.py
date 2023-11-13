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


class AttributeGenericError(Exception):
    def __init__(self, msg: str):
        super(AttributeGenericError, self).__init__(msg)


class ParserError(Exception):
    def __init__(self, unexpected_char: str, line: int, col: int, context: str, allowed: list[str]):
        expected_tokens = ''
        for word in allowed:
            if word.startswith('_CNL_'):
                expected_tokens += f' * {word.removeprefix("_CNL_")}\n'
            elif word == 'SPACE':
                expected_tokens += f' * SPACE (" ")\n'
            else:
                expected_tokens += f' * {word}\n'
        super(ParserError, self).__init__(f'Parser error at line {line}, col {col}. Unexpected char "{unexpected_char}":\n'
                                          f'{context}'
                                          f'Expected one of:\n{expected_tokens}')


class LabelNotFound(Exception):
    def __init__(self, msg: str):
        super(LabelNotFound, self).__init__(msg)


class TypeNotFound(Exception):
    def __init__(self, msg: str):
        super(TypeNotFound, self).__init__(msg)
