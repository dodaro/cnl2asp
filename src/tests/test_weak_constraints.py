import io

from src.cnl.compile import CNLFile, CNLCompiler
from tests.fixtures import *

from itertools import count


def test_weak_constraint_compiles_to_correct_string(monkeypatch,
                                                    max_clique_definitions,
                                                    max_clique_definitions_results,
                                                    max_clique_quantified_choice,
                                                    max_clique_quantified_choice_result):
    string_to_compare = max_clique_definitions + \
                        max_clique_quantified_choice + \
                        'It is preferred with high priority that the number of nodes that are chosen is maximized.'
    expected_result = max_clique_definitions_results + max_clique_quantified_choice_result + \
                      ':~ #count{X_3: chosen(X_3)} = X_2. [-X_2@3]'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_weak_constraint_with_operation_and_range_compiles_to_correct_string(monkeypatch,
                                                                             nurse_definitions_with_constants,
                                                                             nurse_definitions_results_without_constants,
                                                                             nurse_quantified_choice,
                                                                             nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is preferred, with high priority, that the difference in absolute value between ' \
                        'balanceNurseNight and the number of days with shift night where a nurse works in ranging ' \
                        'between minNight and maxNight is minimized. '
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':~ nurse(X_17), #count{X_18: work_in(X_17,X_18,"night")} = X_16, X_16 >= 58, ' \
                      'X_16 <= 61, X_15 = |balanceNurseNight - X_16|. [X_15@3, X_17]'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_weak_constraint_with_operation_compiles_to_correct_string(monkeypatch,
                                                                   nurse_definitions_with_constants,
                                                                   nurse_definitions_results_without_constants,
                                                                   nurse_quantified_choice,
                                                                   nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is preferred, with high priority, that the difference in absolute value between ' \
                        'balanceNurseNight and the number of days with shift night where a nurse works in is ' \
                        'minimized. '
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':~ nurse(X_17), #count{X_18: work_in(X_17,X_18,"night")} = X_16, X_15 = |' \
                      'balanceNurseNight - X_16|. [X_15@3, X_17]'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_weak_constraint_with_operation_no_absolute_compiles_to_correct_string(monkeypatch,
                                                                               nurse_definitions_with_constants,
                                                                               nurse_definitions_results_without_constants,
                                                                               nurse_quantified_choice,
                                                                               nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is preferred, with high priority, that the difference between ' \
                        'balanceNurseNight and the number of days with shift night where a nurse works in is ' \
                        'minimized. '
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':~ nurse(X_17), #count{X_18: work_in(X_17,X_18,"night")} = X_16, X_15 = ' \
                      'balanceNurseNight - X_16. [X_15@3, X_17]'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_weak_constraint_with_operation_no_absolute_and_range_compiles_to_correct_string(monkeypatch,
                                                                                         nurse_definitions_with_constants,
                                                                                         nurse_definitions_results_without_constants,
                                                                                         nurse_quantified_choice,
                                                                                         nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is preferred, with high priority, that the difference between ' \
                        'balanceNurseNight and the number of days with shift night where a nurse works in ranging ' \
                        'between minNight and maxNight is minimized. '
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':~ nurse(X_17), #count{X_18: work_in(X_17,X_18,"night")} = X_16, X_16 >= 58, ' \
                      'X_16 <= 61, X_15 = balanceNurseNight - X_16. [X_15@3, X_17]'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_weak_constraint_with_where_list_and_operation_and_range_compiles_to_correct_string(monkeypatch,
                                                                                            nurse_definitions_with_constants,
                                                                                            nurse_definitions_results_without_constants,
                                                                                            nurse_quantified_choice,
                                                                                            nurse_quantified_choice_result):
    string_to_compare = nurse_definitions_with_constants + \
                        nurse_quantified_choice + \
                        'It is preferred, with high priority, that the difference in absolute value between B and the ' \
                        'number of days with shift S where a nurse works in ranging between minDay and maxDay is ' \
                        'minimized, where B is one of balanceNurseDay, balanceNurseAfternoon and S is one of morning, ' \
                        'afternoon. '
    expected_result = nurse_definitions_results_without_constants + nurse_quantified_choice_result + \
                      ':~ nurse(X_17), #count{X_18: work_in(X_17,X_18,"morning")} = X_16, X_16 >= ' \
                      '74, X_16 <= 82, X_15 = |balanceNurseDay - X_16|. [X_15@3, X_17]\n' \
                      ':~ nurse(X_17), #count{X_18: work_in(X_17,X_18,"afternoon")} = X_16, X_16 >= ' \
                      '74, X_16 <= 82, X_15 = |balanceNurseAfternoon - X_16|. [X_15@3, X_17]'
    monkeypatch.setattr("src.cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'
