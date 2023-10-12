import pytest


@pytest.fixture()
def nurse_definitions_without_constants():
    return 'A day goes from 1 to 365 and is made of shifts that are made of hours.\n' \
           'A shift is one of morning, afternoon, night, specrest, rest, vacation and has hours that are equal to ' \
           'respectively 7, 7, 10, 0, 0, 0.\n' \
           'A nurse goes from 1 to 10.\n'


@pytest.fixture()
def nurse_definitions_with_constants(nurse_definitions_without_constants):
    return nurse_definitions_without_constants + 'maxNurseMorning is equal to 3.\n' \
                                                 'maxNurseAfternoon is equal to 3.\n' \
                                                 'maxNurseNight is equal to 2.\n' \
                                                 'minNurseMorning is equal to 2.\n' \
                                                 'minNurseAfternoon is equal to 2.\n' \
                                                 'minNurseNight is equal to 1.\n' \
                                                 'maxHours is equal to 1692.\n' \
                                                 'minHours is equal to 1687.\n' \
                                                 'maxDay is equal to 82.\n' \
                                                 'maxNight is equal to 61.\n' \
                                                 'minDay is equal to 74.\n' \
                                                 'minNight is equal to 58.'


@pytest.fixture()
def nurse_definitions_results_without_constants():
    return 'day(1..365).\n' \
           'shift(1,"morning",7).\n' \
           'shift(2,"afternoon",7).\n' \
           'shift(3,"night",10).\n' \
           'shift(4,"specrest",0).\n' \
           'shift(5,"rest",0).\n' \
           'shift(6,"vacation",0).\n' \
           'nurse(1..10).\n'


@pytest.fixture()
def nurse_definitions_results_with_constants(nurse_definitions_results_without_constants):
    return nurse_definitions_results_without_constants + 'maxNurseMorning(3).\n' \
                                                         'maxNurseAfternoon(3).\n' \
                                                         'maxNurseNight(2).\n' \
                                                         'minNurseMorning(2).\n' \
                                                         'minNurseAfternoon(2).\n' \
                                                         'minNurseNight(1).\n' \
                                                         'maxHours(1692).\n' \
                                                         'minHours(1687).\n' \
                                                         'maxDay(82).\n' \
                                                         'maxNight(61).\n' \
                                                         'minDay(74).\n' \
                                                         'minNight(58).\n'


@pytest.fixture()
def nurse_quantified_choice():
    return 'Every nurse can work in exactly 1 shift for each day.'


@pytest.fixture()
def nurse_quantified_choice_result():
    return '1 <= {work_in(X_12,X_13,X_14):shift(_,X_14,_)} <= 1 :- nurse(X_12), day(X_13).\n'


@pytest.fixture()
def three_col_definitions():
    return 'A node goes from 1 to 3.\n' \
           'A color is one of red, green, blue.\n' \
           'Node 1 is connected to node X, where X is one of 2, 3.\n' \
           'Node 2 is connected to node X, where X is one of 1, 3.\n' \
           'Node 3 is connected to node X, where X is one of 1, 2.\n'


@pytest.fixture()
def three_col_definitions_results():
    return 'node(1..3).\n' \
           'color(1,"red").\n' \
           'color(2,"green").\n' \
           'color(3,"blue").\n' \
           'connected_to(1,2).\n' \
           'connected_to(1,3).\n' \
           'connected_to(2,1).\n' \
           'connected_to(2,3).\n' \
           'connected_to(3,1).\n' \
           'connected_to(3,2).\n'


@pytest.fixture()
def hampath_definitions():
    return 'A node goes from 1 to 5.\n' \
           'Node 1 is connected to node X, where X is one of 2, 3.\n' \
           'Node 2 is connected to node X, where X is one of 1, 4.\n' \
           'Node 3 is connected to node X, where X is one of 1, 4.\n' \
           'Node 4 is connected to node X, where X is one of 3, 5.\n' \
           'Node 5 is connected to node X, where X is one of 3, 4.\n' \
           'Start is equal to 1.\n'


@pytest.fixture()
def hampath_definitions_results():
    return 'node(1..5).\n' \
           'connected_to(1,2).\n' \
           'connected_to(1,3).\n' \
           'connected_to(2,1).\n' \
           'connected_to(2,4).\n' \
           'connected_to(3,1).\n' \
           'connected_to(3,4).\n' \
           'connected_to(4,3).\n' \
           'connected_to(4,5).\n' \
           'connected_to(5,3).\n' \
           'connected_to(5,4).\n'


@pytest.fixture()
def hampath_quantified_choice():
    return 'Every node X can have a path to a node connected to node X.'


@pytest.fixture()
def hampath_quantified_choice_result():
    return '{path_to(X,X_1):connected_to(X,X_1)} :- node(X).\n'


@pytest.fixture()
def max_clique_definitions():
    return 'A node goes from 1 to 5.\n' \
           'Node 1 is connected to node X, where X is one of 2, 3.\n' \
           'Node 2 is connected to node X, where X is one of 1, 3, 4, 5.\n' \
           'Node 3 is connected to node X, where X is one of 1, 2, 4, 5.\n' \
           'Node 4 is connected to node X, where X is one of 2, 3, 5.\n' \
           'Node 5 is connected to node X, where X is one of 2, 3, 4.\n'


@pytest.fixture()
def max_clique_definitions_results():
    return 'node(1..5).\n' \
           'connected_to(1,2).\n' \
           'connected_to(1,3).\n' \
           'connected_to(2,1).\n' \
           'connected_to(2,3).\n' \
           'connected_to(2,4).\n' \
           'connected_to(2,5).\n' \
           'connected_to(3,1).\n' \
           'connected_to(3,2).\n' \
           'connected_to(3,4).\n' \
           'connected_to(3,5).\n' \
           'connected_to(4,2).\n' \
           'connected_to(4,3).\n' \
           'connected_to(4,5).\n' \
           'connected_to(5,2).\n' \
           'connected_to(5,3).\n' \
           'connected_to(5,4).\n'


@pytest.fixture()
def max_clique_quantified_choice():
    return 'Every node can be chosen.\n'


@pytest.fixture()
def max_clique_quantified_choice_result():
    return '{chosen(X_1)} :- node(X_1).\n'
