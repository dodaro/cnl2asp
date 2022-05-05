import io

from cnl.compile import CNLFile, CNLCompiler
from tests.fixtures import nurse_definitions_without_constants, nurse_definitions_results_without_constants, \
    hampath_definitions, hampath_quantified_choice, hampath_definitions_results, hampath_quantified_choice_result

from itertools import count


def test_compounded_clause_range_compiles_to_correct_string():
    string_to_compare = 'A day goes from 1 to 365.'
    expected_result = 'day(1..365).'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_compounded_clause_range_with_composition_compiles_to_correct_string():
    string_to_compare = 'A day goes from 1 to 365 and is made of shifts that are made of hours.'
    expected_result = 'day(1..365).'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_compounded_clause_match_integers_compiles_to_correct_string():
    string_to_compare = 'A shift is one of 1, 2, 3.'
    expected_result = 'shift(1).\n' \
                      'shift(2).\n' \
                      'shift(3).'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_compounded_clause_match_compiles_to_correct_string():
    string_to_compare = 'A shift is one of morning, afternoon, night, specrest, rest, vacation.'
    expected_result = 'shift(1,"morning").\n' \
                      'shift(2,"afternoon").\n' \
                      'shift(3,"night").\n' \
                      'shift(4,"specrest").\n' \
                      'shift(5,"rest").\n' \
                      'shift(6,"vacation").'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_compounded_clause_match_with_match_tail_compiles_to_correct_string():
    string_to_compare = 'A shift is one of morning, afternoon, night, specrest, rest, vacation and has hours that ' \
                        'are equal to respectively 7, 7, 10, 0, 0, 0.'
    expected_result = 'shift(1,"morning",7).\n' \
                      'shift(2,"afternoon",7).\n' \
                      'shift(3,"night",10).\n' \
                      'shift(4,"specrest",0).\n' \
                      'shift(5,"rest",0).\n' \
                      'shift(6,"vacation",0).'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_compounded_clause_match_with_composition_compiles_to_correct_string():
    string_to_compare = 'A shift is one of morning, afternoon, night, specrest, rest, vacation ' \
                        'and is made of aa that are made of bb.'
    expected_result = 'shift(1,"morning").\n' \
                      'shift(2,"afternoon").\n' \
                      'shift(3,"night").\n' \
                      'shift(4,"specrest").\n' \
                      'shift(5,"rest").\n' \
                      'shift(6,"vacation").'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_compounded_clause_match_with_match_tail_and_composition_compiles_to_correct_string():
    string_to_compare = 'A shift is one of morning, afternoon, night, specrest, rest, vacation and ' \
                        'is made of aa that are made of bb and has hours that ' \
                        'are equal to respectively 7, 7, 10, 0, 0, 0.'
    expected_result = 'shift(1,"morning",7).\n' \
                      'shift(2,"afternoon",7).\n' \
                      'shift(3,"night",10).\n' \
                      'shift(4,"specrest",0).\n' \
                      'shift(5,"rest",0).\n' \
                      'shift(6,"vacation",0).'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_constant_definition_compiles_to_correct_string():
    string_to_compare = 'maxNurseMorning is equal to 3.'
    expected_result = ''

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}'


def test_enumerative_definition_clause_compiles_to_correct_string():
    string_to_compare = 'A node goes from 1 to 5.\n' \
                        'Node 1 is connected to node 2.'
    expected_result = 'node(1..5).\n' \
                      'connected_to(1,2).'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_enumerative_definition_clause_with_multi_object_compiles_to_correct_string():
    string_to_compare = 'A node goes from 1 to 5.\n' \
                        'Node 1 is connected to node 2 and node 3.'
    expected_result = 'node(1..5).\n' \
                      'connected_to(1,2,3).'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_enumerative_definition_clause_with_where_compiles_to_correct_string():
    string_to_compare = 'A node goes from 1 to 5.\n' \
                        'Node 1 is connected to node X, where X is one of 2, 3.'
    expected_result = 'node(1..5).\n' \
                      'connected_to(1,2).\n' \
                      'connected_to(1,3).'

    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_conditional_enumerative_definition_clause_compiles_to_correct_string(monkeypatch,
                                                                              hampath_definitions,
                                                                              hampath_definitions_results,
                                                                              hampath_quantified_choice,
                                                                              hampath_quantified_choice_result):
    string_to_compare = hampath_definitions + \
                        hampath_quantified_choice + \
                        'Node Y is reachable when node X is reachable and also node X has a path to node Y.'
    expected_result = hampath_definitions_results + \
                      hampath_quantified_choice_result + \
                      'reachable(Y) :- reachable(X), path_to(X,Y).'

    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_conditional_enumerative_definition_clause_with_where_list_compiles_to_correct_string(monkeypatch,
                                                                                              hampath_definitions,
                                                                                              hampath_definitions_results,
                                                                                              hampath_quantified_choice,
                                                                                              hampath_quantified_choice_result):
    string_to_compare = hampath_definitions + \
                        hampath_quantified_choice + \
                        'Node Y is reachable when node X is reachable and also node X has a path to node Y,' \
                        'where X is one of 1, 2.'
    expected_result = hampath_definitions_results + \
                      hampath_quantified_choice_result + \
                      'reachable(Y) :- reachable(1), path_to(1,Y).\n' \
                      'reachable(Y) :- reachable(2), path_to(2,Y).'

    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_conditional_enumerative_definition_clause_with_where_bounds_compiles_to_correct_string(monkeypatch,
                                                                                                hampath_definitions,
                                                                                                hampath_definitions_results,
                                                                                                hampath_quantified_choice,
                                                                                                hampath_quantified_choice_result):
    string_to_compare = hampath_definitions + \
                        hampath_quantified_choice + \
                        'Node Y is reachable when node X is reachable and also node X has a path to node Y,' \
                        'where X is between 1 and 2.'
    expected_result = hampath_definitions_results + \
                      hampath_quantified_choice_result + \
                      'reachable(Y) :- reachable(X), path_to(X,Y), X >= 1, X <= 2.'

    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_conditional_enumerative_definition_clause_with_where_condition_compiles_to_correct_string(monkeypatch,
                                                                                                   hampath_definitions,
                                                                                                   hampath_definitions_results,
                                                                                                   hampath_quantified_choice,
                                                                                                   hampath_quantified_choice_result):
    string_to_compare = hampath_definitions + \
                        hampath_quantified_choice + \
                        'Node Y is reachable when node X is reachable and also node X has a path to node Y,' \
                        'where X is different from Y.'
    expected_result = hampath_definitions_results + \
                      hampath_quantified_choice_result + \
                      'reachable(Y) :- reachable(X), path_to(X,Y), X != Y.'

    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_conditional_enumerative_definition_clause_with_where_operation_compiles_to_correct_string(monkeypatch,
                                                                                                   hampath_definitions,
                                                                                                   hampath_definitions_results,
                                                                                                   hampath_quantified_choice,
                                                                                                   hampath_quantified_choice_result):
    string_to_compare = hampath_definitions + \
                        hampath_quantified_choice + \
                        'Node Y is reachable when node X is reachable and also node X has a path to node Y,' \
                        'where X is equal to the sum between 2 and 3.'
    expected_result = hampath_definitions_results + \
                      hampath_quantified_choice_result + \
                      'reachable(Y) :- reachable(X), path_to(X,Y), X = 2 + 3.'

    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_conditional_enumerative_definition_clause_with_multi_object_compiles_to_correct_string(monkeypatch,
                                                                                                hampath_definitions,
                                                                                                hampath_definitions_results,
                                                                                                hampath_quantified_choice,
                                                                                                hampath_quantified_choice_result):
    string_to_compare = hampath_definitions + \
                        hampath_quantified_choice + \
                        'Node X is happy with node Y and node Z when node Y is connected to node Z.'
    expected_result = hampath_definitions_results + \
                      'happy_with(X,Y,Z) :- connected_to(Y,Z).\n' + \
                      hampath_quantified_choice_result

    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}'


def test_conditional_enumerative_definition_clause_with_multi_object_and_where_compiles_to_correct_string(monkeypatch,
                                                                                                          hampath_definitions,
                                                                                                          hampath_definitions_results,
                                                                                                          hampath_quantified_choice,
                                                                                                          hampath_quantified_choice_result):
    string_to_compare = hampath_definitions + \
                        hampath_quantified_choice + \
                        'Node X is happy with node Y and node Z when node Y is connected to node Z ' \
                        'and also node Z is connected to node N,' \
                        'where N is one of 1, 2.'
    expected_result = hampath_definitions_results + \
                      'happy_with(X,Y,Z) :- connected_to(Y,Z), connected_to(Z,1).\n' \
                      'happy_with(X,Y,Z) :- connected_to(Y,Z), connected_to(Z,2).\n' + \
                      hampath_quantified_choice_result

    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}'
