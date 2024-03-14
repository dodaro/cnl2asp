import unittest
from unittest.mock import patch

from lark import Lark

from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.parser.parser import CNLTransformer
from cnl2asp.specification.signaturemanager import SignatureManager

cnl_parser = Lark(open("cnl2asp/grammar.lark", "r").read())


class TestCnlPropositions(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        SignatureManager.signatures = []
        asp_converter: ASPConverter = ASPConverter()
        asp_converter.clear_support_variables()

    def compute_asp(self, string: str) -> str:
        problem = CNLTransformer().transform(cnl_parser.parse(string))
        asp_converter: ASPConverter = ASPConverter()
        program: ASPProgram = problem.convert(asp_converter)
        return str(program)

    def check_input_to_output(self, input_string, expected_output):
        asp = self.compute_asp(input_string)
        self.assertEqual(asp.strip(), expected_output)

    def test_constant_numeric(self):
        self.check_input_to_output('k is a constant equal to 20.','#const k = 20.')

    def test_constant_string(self):
        self.check_input_to_output('k is a constant equal to Kelvin.','#const k = "Kelvin".')

    def test_whenever_then_clause_proposition(self):
        self.check_input_to_output('''A timeslot is identified by a timeslot.
A day is identified by a day.
A patient is identified by an id, and has a preference.
A registration is identified by a patient, and by an order, and has a number of waiting days, a duration of the first phase, a duration of the second phase, a duration of the third phase, and a duration of the fourth phase.

Whenever there is a registration R with an order O, then R can have an assignment to exactly 1 day, and timeslot.''',
                         '1 <= {assignment_to(DY_DY,RGSTRTN_D,O,TMSLT_TMSLT): day(DY_DY), timeslot(TMSLT_TMSLT)} <= 1 :- registration(RGSTRTN_D,O,_,_,_,_,_).')

    def test_quantified_choice_proposition(self):
        self.check_input_to_output('''
        A patron is identified by an id.
A drink is identified by an id.
A pub is identified by an id.
A day is identified by a day.

Every patron can drink in exactly 1 pub for each day.''',
                         '1 <= {drink_in(DY_DY,PTRN_D,PB_D): pub(PB_D)} <= 1 :- day(DY_DY), patron(PTRN_D).')

    def test_constraint_with_aggregate(self):
        self.check_input_to_output('''
            A scoreAssignment is identified by a movie, and by a value.
A topMovie is identified by an id.
It is required that the total value of a scoreAssignment with movie X is equal to 10, such that there is a topMovie with id X.
''',
                         ':- #sum{VL: scoreassignment(X,VL), topmovie(X)} != 10.')

    def test_constaint_with_variable_comparison_and_string_field(self):
        self.check_input_to_output('''
A director is identified by a name.
A movie is identified by a id, and has a title, a director, and a year.
A topMovie is identified by a id.
A scoreAssignment is identified by a movie, and by a value.
It is required that V is equal to 3, whenever there is a movie with id I, and with director equal to spielberg, whenever there is a scoreAssignment with movie I, and with value V.''',':- V != 3, movie(I,_,"spielberg",_), scoreassignment(I,V).')

    def test_when_then_constraint(self):
        self.check_input_to_output('''
        A pub is identified by an id.
        A waiter is identified by an id.
Every waiter can work in a pub.
Every waiter can be payed.
It is required that when waiter X works in pub P1 then waiter X does not work in pub P2, where P1 is different from P2.''','''{work_in(WTR_D,PB_D): pub(PB_D)} :- waiter(WTR_D).
{payed(WTR_D)} :- waiter(WTR_D).
:- work_in(X,P1), pub(P1), waiter(X), work_in(X,P2), pub(P2), P1 != P2.''')

    def test_quantified_simple_clause_constraint(self):
        self.check_input_to_output('''
        A pub is identified by an id.
        A waiter is identified by an id.
Every waiter can is work in a pub.
Every waiter can be payed.
        It is required that every waiter is payed.''','''{work_in(WTR_D,PB_D): pub(PB_D)} :- waiter(WTR_D).
{payed(WTR_D)} :- waiter(WTR_D).
:- waiter(PYD_D), not payed(PYD_D).''')

    def test_enumerative_definition(self):
        self.check_input_to_output('''
        A waiter is identified by an id.
A pub is identified by an id.
A drink is identified by an id.
Waiter W works in pub P.
Waiter J serves a drink A.
Waiter W is working, when waiter W serves a drink.''','''work_in(W,P) :- waiter(W), pub(P).
serve(J,A) :- waiter(J), drink(A).
working(W) :- serve(W,DRNK_D), drink(DRNK_D), waiter(W).''')

    def test_compounded_clause_definition(self):
        self.check_input_to_output('''
        A day goes from 1 to 365.''','''day(1..365).''')

    def test_compounded_clause_match(self):
        self.check_input_to_output('''
        A color is one of red, green, blue.''','''color("red").
color("green").
color("blue").''')

    def test_compounded_clause_match_with_tail(self):
        self.check_input_to_output('''A drink is one of alcoholic, nonalcoholic and has color that is equal to respectively blue, yellow.
''','''drink("alcoholic","blue").
drink("nonalcoholic","yellow").''')

    def test_fact_proposition(self):
        self.check_input_to_output('A movie is identified by an id, by a director, by a title, by a year.' \
                 'There is a movie with id equal to 1, with director equal to spielberg, ' \
                 'with title equal to jurassicPark, with year equal to 1993.','''movie(1,"spielberg","jurassicPark",1993).''')

    def test_weak_constraint_with_comparison(self):
        self.check_input_to_output('''A movie is identified by an id, and has a title, a director, and a year.
A director is identified by a name.
A topMovie is identified by an id.
A scoreAssignment is identified by a movie, and by a value.
It is preferred as little as possible, with high priority, that V is equal to 1, whenever there is a scoreAssignment with movie I, and with value V, whenever there is a topMovie with id I.
        ''',''':~ V = 1, scoreassignment(I,V), topmovie(I). [1@3,I,V]''')

    def test_weak_constraint_with_variable_maximized(self):
        self.check_input_to_output('''A movie is identified by an id, and has a title, a director, and a year.
A director is identified by a name.
A topMovie is identified by an id.
A scoreAssignment is identified by a movie, and by a value.
It is preferred, with medium priority, that whenever there is a topMovie with id I, whenever there is a scoreAssignment with movie I, and with value V, V is maximized.
                ''',''':~ topmovie(I), scoreassignment(I,V). [-V@2,I,V]''')

    def test_weak_constraint_with(self):
        self.check_input_to_output('''A movie is identified by an id, and has a title, a director, and a year.
A director is identified by a name.
A topMovie is identified by an id.
A scoreAssignment is identified by a movie, and by a value.
It is preferred, with medium priority, that the total value of a scoreAssignment is minimized.''', ''':~ #sum{VL: scoreassignment(_,VL)} = SM. [SM@2]''')

    def test_variable_substitution(self):
        self.check_input_to_output('''
        A node is identified by an id.
        Node 1 is connected to node X, where X is one of 2, 3, 4.''','''connected_to(1,X) :- node(1), node(X), X = 2.
connected_to(1,X) :- node(1), node(X), X = 3.
connected_to(1,X) :- node(1), node(X), X = 4.''')

    def test_temporal_definitions_and_constraints_after(self):
        self.check_input_to_output('''A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
An entity is identified by an id, and by a timeslot.
It is required that the entity E is after 11:20 AM.''',''':- entity(_,TMSLT_NTTY), TMSLT_NTTY <= 23.''')

    def test_temporal_definitions_and_constraints_before(self):
            self.check_input_to_output('''A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
    An entity is identified by an id, and by a timeslot.
    It is required that the entity E is before 11:20 AM.''', ''':- entity(_,TMSLT_NTTY), TMSLT_NTTY >= 23.''')

    def test_artithmentic_operations_with_parameters(self):
        self.check_input_to_output('''A day is identified by an id.
A patient is identified by an id, and has a preference.
It is required that the sum between the id of the patient I, and the id of the day is equal to 1.''',
                                   ''':- patient(PTNT_D,_), day(DY_D), (PTNT_D + DY_D) != 1.''')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_duration_clause_with_parameter_as_entity(self, mock_uuid):
        mock_uuid.return_value = "support"
        self.check_input_to_output('''A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
A day is identified by a day.
A patient is identified by an id, and has a preference.

Whenever there is a patient P, whenever there is a timeslot T, then we can have a position in a day D for 2 timeslots.''','''timeslot(0,"07:30 AM").
timeslot(1,"07:40 AM").
timeslot(2,"07:50 AM").
timeslot(3,"08:00 AM").
timeslot(4,"08:10 AM").
timeslot(5,"08:20 AM").
timeslot(6,"08:30 AM").
timeslot(7,"08:40 AM").
timeslot(8,"08:50 AM").
timeslot(9,"09:00 AM").
timeslot(10,"09:10 AM").
timeslot(11,"09:20 AM").
timeslot(12,"09:30 AM").
timeslot(13,"09:40 AM").
timeslot(14,"09:50 AM").
timeslot(15,"10:00 AM").
timeslot(16,"10:10 AM").
timeslot(17,"10:20 AM").
timeslot(18,"10:30 AM").
timeslot(19,"10:40 AM").
timeslot(20,"10:50 AM").
timeslot(21,"11:00 AM").
timeslot(22,"11:10 AM").
timeslot(23,"11:20 AM").
timeslot(24,"11:30 AM").
timeslot(25,"11:40 AM").
timeslot(26,"11:50 AM").
timeslot(27,"12:00 PM").
timeslot(28,"12:10 PM").
timeslot(29,"12:20 PM").
timeslot(30,"12:30 PM").
timeslot(31,"12:40 PM").
timeslot(32,"12:50 PM").
timeslot(33,"01:00 PM").
timeslot(34,"01:10 PM").
timeslot(35,"01:20 PM").
timeslot(36,"01:30 PM").
{x_support(D,P,T): day(D)} :- patient(P,_), timeslot(T,_).
position_in(X_SPPRT_DY,P,T..T+2) :- patient(P,_), timeslot(T,_), x_support(X_SPPRT_DY,P,T).''')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_duration_clause_with_parameter_as_attribute(self, mock_uuid):
        mock_uuid.return_value = "support"
        self.check_input_to_output('''A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
    A day is identified by a day.
    A patient is identified by an id, and has a preference.

    Whenever there is a patient P, then we can have a position with timeslot T in a day D for 2 timeslots.''','''{x_support(D,P,T): day(D)} :- patient(P,_).
position_in(X_SPPRT_DY,P,T..T+2) :- patient(P,_), x_support(X_SPPRT_DY,P,T).''')

    def test_substitute_subsequent_event_next(self):
        self.check_input_to_output("""
A time is a temporal concept expressed in steps ranging from 1 to 10.
A joint is identified by an id.
An rotation is identified by a value.
A position is identified by a joint, by an rotation, and by a time.
It is required that the rotation A1 of the position P1 is equal to the rotation A2 of the position P2, whenever there is a position P1 with joint J, with rotation A1, and with time T, whenever there is a position P2 the next step with joint J, and with rotation A2.""",''':- A1 != A2, position(J,A1,T), position(J,A2,T+1).''')

    def test_substitute_subsequent_event_previous(self):
            self.check_input_to_output("""
    A time is a temporal concept expressed in steps ranging from 1 to 10.
    A joint is identified by an id.
    An rotation is identified by a value.
    A position is identified by a joint, by an rotation, and by a time.
    It is required that the rotation A1 of the position P1 is equal to the rotation A2 of the position P2, whenever there is a position P1 with joint J, with rotation A1, and with time T, whenever there is a position P2 the previous step with joint J, and with rotation A2.""",
                                       ''':- A1 != A2, position(J,A1,T), position(J,A2,T-1).''')

    def test_entity_as_parameter(self):
        self.check_input_to_output( """
        A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
        A patient is identified by an id, and has a preference.
A registration is identified by a patient, and by an order, and has a number of waiting days, a duration of the first phase, a duration of the second phase, a duration of the third phase, and a duration of the fourth phase.
        Whenever there is a registration R with patient P, with order OR, and with a number of waiting days W, then we can have an assignment with registration R to exactly 1 timeslot.""",
                         '''timeslot(0,"07:30 AM").
timeslot(1,"07:40 AM").
timeslot(2,"07:50 AM").
timeslot(3,"08:00 AM").
timeslot(4,"08:10 AM").
timeslot(5,"08:20 AM").
timeslot(6,"08:30 AM").
timeslot(7,"08:40 AM").
timeslot(8,"08:50 AM").
timeslot(9,"09:00 AM").
timeslot(10,"09:10 AM").
timeslot(11,"09:20 AM").
timeslot(12,"09:30 AM").
timeslot(13,"09:40 AM").
timeslot(14,"09:50 AM").
timeslot(15,"10:00 AM").
timeslot(16,"10:10 AM").
timeslot(17,"10:20 AM").
timeslot(18,"10:30 AM").
timeslot(19,"10:40 AM").
timeslot(20,"10:50 AM").
timeslot(21,"11:00 AM").
timeslot(22,"11:10 AM").
timeslot(23,"11:20 AM").
timeslot(24,"11:30 AM").
timeslot(25,"11:40 AM").
timeslot(26,"11:50 AM").
timeslot(27,"12:00 PM").
timeslot(28,"12:10 PM").
timeslot(29,"12:20 PM").
timeslot(30,"12:30 PM").
timeslot(31,"12:40 PM").
timeslot(32,"12:50 PM").
timeslot(33,"01:00 PM").
timeslot(34,"01:10 PM").
timeslot(35,"01:20 PM").
timeslot(36,"01:30 PM").
1 <= {assignment_to(P,OR,TMSLT_TMSLT): timeslot(TMSLT_TMSLT,_)} <= 1 :- registration(P,OR,W,_,_,_,_).''')

    def test_handle_duplicated_parameters(self):
        """
        Since there are multiple entities with parameter id, we expect position in to have different id attributes.
        An id is declared for position in, however being initialized with the same value of seat, it is the
        same id attribute of the entity seat.
        """
        self.check_input_to_output( """
        A patient is identified by an id.
        A seat is identified by an id.
        Whenever there is a patient P, then P can have a position with id S in exactly 1 seat S.""",
                         '''1 <= {position_in(S,P): seat(S)} <= 1 :- patient(P).''')

    def test_aggregate_with_objects(self):
        self.check_input_to_output( """
        A patient is identified by an id.
        A seat is identified by an id.
        Whenever there is a patient P then P can have a position in exactly 1 seat S.
        It is required that the number of patient that have a position in seat S is less than 2.
        """,
                         '''1 {position_in(P,S): seat(S)} 1 :- patient(P).\n:- #count{D: position_in(D,S), seat(S)} >= 2.''')

    def test_aggregate_with_objects(self):
        self.check_input_to_output("""
        A patient is identified by an id.
        A seat is identified by an id.
        Whenever there is a patient P then P can have a position in exactly 1 seat S.
        It is required that the highest of patient that have a position in seat S is less than 2.
        """,
                         '''1 <= {position_in(P,S): seat(S)} <= 1 :- patient(P).\n:- #max{D: position_in(D,S), seat(S)} >= 2.''')

    def test_angle_operation(self):
        self.check_input_to_output( '''An angle is identified by a value.
A rotation is identified by a first joint, by a second joint, by a desired angle, by a current angle, and by a time.
It is required that the desired angle A of the rotation R is different from the current angle AI of the rotation R,  whenever there is a rotation R with desired angle A, and with current angle AI.''',
                         ''':- (A)/360 = (AI)/360, rotation(_,_,A,AI,_).''')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_operation_between_two_aggregate(self, mock_uuid):
        mock_uuid.side_effect = ['X', 'Y']
        self.check_input_to_output( '''
A patient is identified by an id, and has a preference.
An assignment is identified by a patient, by a day, and by a timeslot.
It is required that the number of patient that have an assignment with day D, with timeslot TS is less than the number of patient that have an assignment with day D+1, with timeslot TS.''',
                         ''':- #count{D1: assignment(D1,D,TS)} = CNT, #count{D2: assignment(D2,D+1,TS)} = CNT1, CNT >= CNT1.''')


    def test_do_not_link_choice_elements_with_body(self):
        self.check_input_to_output( '''
        A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
A day is a temporal concept expressed in days ranging from 01/01/2022 to 07/01/2022.
A patient is identified by an id, and has a preference.
A registration is identified by a patient, and by an order, and has a number of waiting days, a duration of the first phase, a duration of the second phase, a duration of the third phase, and a duration of the fourth phase.
An assignment is identified by a registration, by a day, and by a timeslot.
A registration is identified by a patient, and by an order, and has a number of waiting days, a duration of the first phase, a duration of the second phase, a duration of the third phase, and a duration of the fourth phase.
        Whenever there is a registration R with patient P, with order OR, and with a number of waiting days W, whenever there is an assignment with registration patient P, with registration order OR-1, and with day D, whenever there is a day with day D+W, then we can have an assignment with registration R, and with day D+W to exactly 1 timeslot.
        ''',
                         '''timeslot(0,"07:30 AM").
timeslot(1,"07:40 AM").
timeslot(2,"07:50 AM").
timeslot(3,"08:00 AM").
timeslot(4,"08:10 AM").
timeslot(5,"08:20 AM").
timeslot(6,"08:30 AM").
timeslot(7,"08:40 AM").
timeslot(8,"08:50 AM").
timeslot(9,"09:00 AM").
timeslot(10,"09:10 AM").
timeslot(11,"09:20 AM").
timeslot(12,"09:30 AM").
timeslot(13,"09:40 AM").
timeslot(14,"09:50 AM").
timeslot(15,"10:00 AM").
timeslot(16,"10:10 AM").
timeslot(17,"10:20 AM").
timeslot(18,"10:30 AM").
timeslot(19,"10:40 AM").
timeslot(20,"10:50 AM").
timeslot(21,"11:00 AM").
timeslot(22,"11:10 AM").
timeslot(23,"11:20 AM").
timeslot(24,"11:30 AM").
timeslot(25,"11:40 AM").
timeslot(26,"11:50 AM").
timeslot(27,"12:00 PM").
timeslot(28,"12:10 PM").
timeslot(29,"12:20 PM").
timeslot(30,"12:30 PM").
timeslot(31,"12:40 PM").
timeslot(32,"12:50 PM").
timeslot(33,"01:00 PM").
timeslot(34,"01:10 PM").
timeslot(35,"01:20 PM").
timeslot(36,"01:30 PM").
day(0,"01/01/2022").
day(1,"02/01/2022").
day(2,"03/01/2022").
day(3,"04/01/2022").
day(4,"05/01/2022").
day(5,"06/01/2022").
day(6,"07/01/2022").
1 <= {assignment_to(D+W,P,OR,TMSLT_TMSLT): timeslot(TMSLT_TMSLT,_)} <= 1 :- registration(P,OR,W,_,_,_,_), assignment(P,OR-1,D,_), day(D+W,_).''')

    def test_remove_duplicates_from_condition(self):
        self.check_input_to_output( '''
        A node goes from 1 to 5.
        Every node X can have a path to a node connected to node X.''',
                         '''node(1..5).\n{path_to(CNNCTD_T_D,X): node(CNNCTD_T_D), connected_to(CNNCTD_T_D,X)} :- node(X).''')

    def test_parameter_temporal_ordering(self):
        self.check_input_to_output( '''
        A time is a temporal concept expressed in steps ranging from 1 to 10.
        A joint is identified by an id.
        An angle is identified by a value.
        A position is identified by a joint, by an angle, and by a time.
        A link is identified by a first joint, and by a second joint.
        A rotation is identified by a first joint, by a second joint, by a desired angle, by a current angle, and by a time.
        A goal is identified by a joint, and by an angle.
        It is required that the angle A1 of the position P1 is equal to the angle A2 of the position P2, whenever there is a position P1 with joint J1, with angle A1, and with time T, whenever there is a position P2 with joint J1, and with angle A2, and with the next step respect to T, whenever there is a rotation with first joint J2 greater than J1, and with time T not after timemax.
        ''',':- (A1)/360 != (A2)/360, position(J1,A1,T), position(J1,A2,T+1), rotation(J2,_,_,_,T), J2 > J1, T <= "timemax".')

    def test_simple_definition(self):
        self.check_input_to_output( '''John is a waiter.''','waiter("John").')

    def test_simple_aggregate(self):
        self.check_input_to_output( '''A positivematch is identified by a match.
A negativematch is identified by a match.
It is required that the number of positivematch is equal to the number of negativematch.
It is required that the number of positivematch occurrences is equal to the number of negativematch occurrences.''',''':- #count{positivematch(PSTVMTCH_MTCH): positivematch(PSTVMTCH_MTCH)} = CNT, #count{negativematch(NGTVMTCH_MTCH): negativematch(NGTVMTCH_MTCH)} = CNT1, CNT != CNT1.
:- #count{positivematch(PSTVMTCH_MTCH): positivematch(PSTVMTCH_MTCH)} = CNT, #count{negativematch(NGTVMTCH_MTCH): negativematch(NGTVMTCH_MTCH)} = CNT1, CNT != CNT1.''')

    def test_parameter_entity_link(self):
        self.check_input_to_output( '''Node is identified by an id.
Vertex has an id.
It is required that the id of the node is greater than the id of the vertex.''',''':- node(ND_D), vertex(VRTX_D), ND_D <= VRTX_D.''')

    def test_set_entity(self):
        self.check_input_to_output('''set1 is a set.
set2 is a set.
set1 contains 1, 2, 3.
it is prohibited that X is equal to 1, whenever there is an element X in set1, whenever there is an element Y greater than 2 in set2.''', ''':- X = 1, set("set1",X), set("set2",Y), Y > 2.''')

    def test_list_element_order(self):
        self.check_input_to_output('''shift is a list.
shift contains morning, afternoon, night.
A nurse is identified by an id.

It is prohibited that a nurse works in the shift element after night.''', ''':- nurse(WRK_N_D), work_in(WRK_N_D,LMNT,"shift"), list("shift",LMNT,"morning").''')

    def test_list_element_index(self):
        self.check_input_to_output('''shift is a list.
shift contains morning, afternoon, night.
A nurse is identified by an id.

It is prohibited that a nurse works in the 1st element in shift.''', ''':- nurse(WRK_N_D), work_in(WRK_N_D,LMNT,"shift"), list("shift",LMNT,"morning").''')

    def test_multiple_problems(self):
        self.check_input_to_output('''A node is identified by an id.
        The following propositions apply in the initial state:
        There is a node with id 1.
        The following propositions apply in the final state:
        There is a node with id 2.''', '''#program initial.\nnode(1).\n\n#program final.\nnode(2).''')

    def test_initially_inside_temporal_formulas(self):
        self.check_input_to_output("""A tourist is identified by a name.
A city is identified by a name.

Whenever there is initially a tourist or the true constant, then we can have a movement.""", """{movement(TRST_NM)} :- not not &tel {<< tourist(TRST_NM) | &true}.""")

    def test_priority_level_number(self):
        self.check_input_to_output('''A drink is identified by an id.
A serve is identified by a drink.
It is preferred with priority 5 that the number of drinks that are serve is maximized.''', ':~ #count{D: serve(D)} = CNT. [-CNT@5]')
