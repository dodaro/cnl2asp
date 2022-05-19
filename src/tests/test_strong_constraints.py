import io

from src.cnl.compile import CNLFile, CNLCompiler
from src.tests.fixtures import nurse_definitions_without_constants, nurse_definitions_with_constants, \
    nurse_definitions_results_without_constants, nurse_quantified_choice, nurse_quantified_choice_result, \
    max_clique_definitions, max_clique_definitions_results, three_col_definitions, three_col_definitions_results, \
    hampath_definitions, hampath_definitions_results, hampath_quantified_choice, hampath_quantified_choice_result, \
    max_clique_quantified_choice, max_clique_quantified_choice_result

from itertools import count


def test_strong_constraint_active_aggregate_compiles_to_correct_string(monkeypatch, nurse_definitions_with_constants,
                                                                       nurse_definitions_results_without_constants,
                                                                       nurse_quantified_choice,
                                                                       nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is prohibited that the total of hours in a day where a nurse works in is more than ' \
                        'maxHours.'
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':- nurse(X_15), #sum{X_16,X_17: work_in(X_15,X_17,X_18), shift(_,X_18,X_16)} > 1692.'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_strong_constraint_passive_aggregate_compiles_to_correct_string(monkeypatch, nurse_definitions_with_constants,
                                                                        nurse_definitions_results_without_constants,
                                                                        nurse_quantified_choice,
                                                                        nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is prohibited that the number of days with shift vacation where a nurse works in is ' \
                        'different from 30. '
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':- nurse(X_15), #count{X_16: work_in(X_15,X_16,"vacation")} != 30.'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_strong_constraint_aggregate_with_where_list_compiles_to_correct_string(monkeypatch,
                                                                                nurse_definitions_with_constants,
                                                                                nurse_definitions_results_without_constants,
                                                                                nurse_quantified_choice,
                                                                                nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is required that the number of nurses that work in shift S for each day is at most M, ' \
                        'where S is one of morning, afternoon, night and M is one of respectively maxNurseMorning, ' \
                        'maxNurseAfternoon, maxNurseNight.'
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':- day(X_16), #count{X_15: work_in(X_15,X_16,"morning")} > 3.\n' \
                      ':- day(X_16), #count{X_15: work_in(X_15,X_16,"afternoon")} > 3.\n' \
                      ':- day(X_16), #count{X_15: work_in(X_15,X_16,"night")} > 2.'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_strong_constraint_aggregate_with_window_compiles_to_correct_string(monkeypatch,
                                                                            nurse_definitions_with_constants,
                                                                            nurse_definitions_results_without_constants,
                                                                            nurse_quantified_choice,
                                                                            nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is required that the number of occurrences between each 14 days with shift rest where a ' \
                        'nurse works in is at least 2.'
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':- nurse(X_15), day(X_17), X_17 <= 352, #count{X_16: ' \
                      'work_in(X_15,X_16,"rest"), X_16 >= X_17, X_16 <= X_17+13} < 2.'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_strong_constraint_simple_with_where_bounds_compiles_to_correct_string(monkeypatch,
                                                                               nurse_definitions_with_constants,
                                                                               nurse_definitions_results_without_constants,
                                                                               nurse_quantified_choice,
                                                                               nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is prohibited that a nurse works in shift S in a day and also the next day works in a ' \
                        'shift before S, where S is between morning and night.'
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':- shift(X_19,X_21,_), shift(X_20,S,_), work_in(X_15,X_16,S), ' \
                      'work_in(X_15,X_16+1,X_21), X_19 < X_20, X_20 >= 1, X_20 <= 3, X_19 >= 1, ' \
                      'X_19 <= 6.'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_strong_constraint_simple_with_where_condition_compiles_to_correct_string(monkeypatch,
                                                                                  max_clique_definitions,
                                                                                  max_clique_definitions_results,
                                                                                  max_clique_quantified_choice,
                                                                                  max_clique_quantified_choice_result):
    string_to_compare = max_clique_definitions + \
                        max_clique_quantified_choice + \
                        'It is required that when node X is not connected to node Y then node X is not chosen and ' \
                        'also node Y is not chosen, where X is different from Y. '
    expected_result = max_clique_definitions_results + max_clique_quantified_choice_result + \
                      ':- not connected_to(X,Y), chosen(X), chosen(Y), X != Y.'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_strong_constraint_aggregate_with_where_operation_compiles_to_correct_string(monkeypatch,
                                                                                     nurse_definitions_with_constants,
                                                                                     nurse_definitions_results_without_constants,
                                                                                     nurse_quantified_choice,
                                                                                     nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is prohibited that the number of days with shift vacation where a nurse works in is ' \
                        'different from X, where X is equal to the sum between 1 and 2. '
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':- nurse(X_15), #count{X_16: work_in(X_15,X_16,"vacation")} != X, X = 1 + 2.'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_strong_constraint_simple_with_object_consecution_compiles_to_correct_string(monkeypatch,
                                                                                     nurse_definitions_with_constants,
                                                                                     nurse_definitions_results_without_constants,
                                                                                     nurse_quantified_choice,
                                                                                     nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is required that when a nurse works in shift night for 2 consecutive days then the next ' \
                        'day works in shift specrest.'
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':- day(X_17), #count{X_16: work_in(X_15,X_16,"night"), X_16 >= X_17, X_16 <= ' \
                      'X_17+1} = 2, not work_in(X_15,X_17+2,"specrest"), nurse(X_15).'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_strong_constraint_simple_with_subject_consecution_compiles_to_correct_string(monkeypatch,
                                                                                      nurse_definitions_with_constants,
                                                                                      nurse_definitions_results_without_constants,
                                                                                      nurse_quantified_choice,
                                                                                      nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is prohibited that a nurse works in a day in shift specrest and also the previous 2 ' \
                        'consecutive days does not work in shift night.'
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':- work_in(X_15,X_16,"specrest"), day(X_16), #count{X_18: ' \
                      'work_in(X_15,X_18,"night"), X_18 >= X_16-2, X_18 <= X_16-1} != 2.'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_strong_constraint_quantified_compiles_to_correct_string(monkeypatch,
                                                                 hampath_definitions,
                                                                 hampath_definitions_results,
                                                                 hampath_quantified_choice,
                                                                 hampath_quantified_choice_result):
    string_to_compare = hampath_definitions + \
                        hampath_quantified_choice + \
                        'Node Y is reachable when node X is reachable and also node X has a path to node Y.\n' + \
                        'Node start is reachable.' + \
                        'It is required that every node is reachable.'
    expected_result = hampath_definitions_results + 'reachable(1).\n' + hampath_quantified_choice_result + \
                      ':- not reachable(X_2), node(X_2).\n' + \
                      'reachable(Y) :- reachable(X), path_to(X,Y).'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'
