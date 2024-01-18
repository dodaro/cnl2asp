from cnl2asp.utility.utility import Utility


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
    def __init__(self, unexpected_char: str, line_number: int, col_number: int, context: str, line: str, allowed: list[str]):
        expected_tokens = ''
        for word in allowed:
            if word.startswith('_CNL_'):
                expected_tokens += f' * {word.removeprefix("_CNL_")}\n'
            elif word == 'SPACE':
                expected_tokens += f' * SPACE (" ")\n'
            else:
                expected_tokens += f' * {word}\n'
        unrecognised_word = self.get_uncrecognized_word(line, col_number-1)
        hint = ''
        if unrecognised_word in Utility.LOCKED_KEYWORDS and "STRING" in allowed or "PARAMETER_NAME" in allowed:
            hint = f"Might be caused by the usage of a locked keyword \"{unrecognised_word}\" as a name"
        super(ParserError, self).__init__(f'Parser error at line {line_number}, col {col_number}. Unexpected char "{unexpected_char}":\n'
                                          f'{context}'
                                          f'Expected one of:\n{expected_tokens}'
                                          f'\n\n{hint}')

    def get_uncrecognized_word(self, string: str, index: int):
        up = index
        while string[up] != " ":
            up += 1
        down = index
        while string[down] != " ":
            down -= 1
        return string[down+1:up]


class LabelNotFound(Exception):
    def __init__(self, msg: str):
        super(LabelNotFound, self).__init__(msg)


class TypeNotFound(Exception):
    def __init__(self, msg: str):
        super(TypeNotFound, self).__init__(msg)
