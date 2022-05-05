import io

from cnl.compile import CNLFile, CNLCompiler
from tests.fixtures import nurse_definitions_without_constants, nurse_definitions_results_without_constants, \
    max_clique_definitions, max_clique_definitions_results, three_col_definitions, three_col_definitions_results, \
    hampath_definitions, hampath_definitions_results

from itertools import count


def test_quantified_choice_compiles_to_correct_string(monkeypatch, max_clique_definitions,
                                                      max_clique_definitions_results):
    string_to_compare = max_clique_definitions + 'Every node can be chosen.'
    expected_result = max_clique_definitions_results + '{chosen(X_1)} :- node(X_1).'
    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_quantified_choice_clause_with_object_clause_compiles_to_correct_string(monkeypatch, hampath_definitions,
                                                                                hampath_definitions_results):
    string_to_compare = hampath_definitions + 'Every node X can have a path to a node connected to node X.'
    expected_result = hampath_definitions_results + '{path_to(X,X_1):connected_to(X,X_1)} :- node(X).'
    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_quantified_choice_clause_with_multi_object_compiles_to_correct_string(monkeypatch, three_col_definitions,
                                                                               three_col_definitions_results):
    string_to_compare = three_col_definitions + 'Every node can be assigned to exactly 1 color.'
    expected_result = three_col_definitions_results + '1 <= {assigned_to(X_2,X_3):color(_,X_3)} <= 1 :- node(X_2).'
    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_quantified_choice_clause_with_foreach_compiles_to_correct_string(monkeypatch, max_clique_definitions,
                                                      max_clique_definitions_results):
    string_to_compare = max_clique_definitions + 'Every node can be chosen for each node N.'
    expected_result = max_clique_definitions_results + '{chosen(X_1,N)} :- node(X_1), node(N).'
    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'


def test_quantified_choice_clause_with_exact_quantity_and_foreach_compiles_to_correct_string(monkeypatch,
                                                                                             nurse_definitions_without_constants,
                                                                                             nurse_definitions_results_without_constants):
    string_to_compare = nurse_definitions_without_constants + 'Every nurse can work in exactly 1 shift for each day.'
    expected_result = nurse_definitions_results_without_constants + '1 <= {work_in(X_12,X_13,X_14):shift(_,X_14,_)} ' \
                                                                    '<= 1 :- nurse(X_12), day(X_13).'
    monkeypatch.setattr("cnl.compile.uuid4", count().__next__)
    with io.StringIO(string_to_compare) as in_file, \
            io.StringIO() as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        cnl_compiler.compile(cnl_file).into(out_file)

        assert out_file.getvalue() == f'{expected_result}\n'
