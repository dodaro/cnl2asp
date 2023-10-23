import unittest
from unittest.mock import patch

from lark import Lark

from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.parser.parser import CNLTransformer
from cnl2asp.proposition.entity_component import SetOfTypedEntities
from cnl2asp.proposition.signaturemanager import SignatureManager

cnl_parser = Lark(open("cnl2asp/grammar.lark", "r").read())


class TestASPElements(unittest.TestCase):
    def setUp(self):
        SetOfTypedEntities._TypedEntities = []
        SignatureManager.signatures = []
        asp_converter: ASPConverter = ASPConverter()
        asp_converter.clear_support_variables()

    def compute_asp(self, string: str) -> str:
        problem = CNLTransformer().transform(cnl_parser.parse(string))
        asp_converter: ASPConverter = ASPConverter()
        program: ASPProgram = problem.convert(asp_converter)
        return program.to_string()

    def test_constant_numeric(self):
        string = 'k is a constant equal to 20.'
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '#const k = 20.')

    def test_constant_string(self):
        string = 'k is a constant equal to Kelvin.'
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '#const k = "Kelvin".')

    def test_whenever_then_clause_proposition(self):
        string = '''A timeslot is identified by a timeslot.
A day is identified by a day.
A patient is identified by an id, and has a preference.
A registration is identified by a patient, and by an order, and has a number of waiting days, a duration of the first phase, a duration of the second phase, a duration of the third phase, and a duration of the fourth phase.

Whenever there is a registration R with an order O, then R can have an assignment to exactly 1 day, and timeslot.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         '1 {assignment_to(DY_DY,RGSTRTN_D,O,TMSLT_TMSLT): day(DY_DY), timeslot(TMSLT_TMSLT)} 1 :- registration(RGSTRTN_D,O,_,_,_,_,_).')

    def test_quantified_choice_proposition(self):
        string = '''
        A patron is identified by an id.
A drink is identified by an id.
A pub is identified by an id.
A day is identified by a day.

Every patron can drink in exactly 1 pub for each day.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         '1 {drink_in(DY_DY,PTRN_D,PB_D): pub(PB_D)} 1 :- day(DY_DY), patron(PTRN_D).')

    def test_constraint_with_aggregate(self):
        string = '''
            A scoreAssignment is identified by a movie, and by a value.
A topMovie is identified by an id.
It is required that the total value of a scoreAssignment with movie X is equal to 10, such that there is a topMovie with id X.
'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         ':- #sum{VL: scoreassignment(X,VL), topmovie(X)} != 10.')

    def test_constaint_with_variable_comparison_and_string_field(self):
        string = '''
A director is identified by a name.
A movie is identified by a id, and has a title, a director, and a year.
A topMovie is identified by a id.
A scoreAssignment is identified by a movie, and by a value.
It is required that V is equal to 3, whenever there is a movie with id I, and with director equal to spielberg, whenever there is a scoreAssignment with movie I, and with value V.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), ':- V != 3, movie(I,_,"spielberg",_), scoreassignment(I,V).')

    def test_when_then_constraint(self):
        string = '''
        A pub is identified by an id.
        A waiter is identified by an id.
Every waiter can work in a pub.
Every waiter can be payed.
It is required that when waiter X works in pub P1 then waiter X does not work in pub P2, where P1 is different from P2.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''{work_in(WTR_D,PB_D): pub(PB_D)} 1 :- waiter(WTR_D).
 {payed(WTR_D)} 1 :- waiter(WTR_D).
:- work_in(X,P1), pub(P1), waiter(X), work_in(X,P2), pub(P2), P1 != P2.''')

    def test_quantified_simple_clause_constraint(self):
        string = '''
        A pub is identified by an id.
        A waiter is identified by an id.
Every waiter can is work in a pub.
Every waiter can be payed.
        It is required that every waiter is payed.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''{work_in(WTR_D,PB_D): pub(PB_D)} 1 :- waiter(WTR_D).
 {payed(WTR_D)} 1 :- waiter(WTR_D).
:- waiter(PYD_D), not payed(PYD_D).''')

    def test_enumerative_definition(self):
        string = '''
        A waiter is identified by an id.
A pub is identified by an id.
A drink is identified by an id.
Waiter W works in pub P.
Waiter J serves a drink A.
Waiter W is working, when waiter W serves a drink.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''work_in(W,P) :- waiter(W), pub(P).
serve(J,A) :- waiter(J), drink(A).
working(W) :- serve(W,DRNK_D), drink(DRNK_D), waiter(W).''')

    def test_compounded_clause_definition(self):
        string = '''
        A day goes from 1 to 365.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''day(1..365).''')

    def test_compounded_clause_match(self):
        string = '''
        A color is one of red, green, blue.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''color("red").
color("green").
color("blue").''')

    def test_compounded_clause_match_with_tail(self):
        string = '''A drink is one of alcoholic, nonalcoholic and has color that is equal to respectively blue, yellow.
'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''drink("alcoholic","blue").
drink("nonalcoholic","yellow").''')

    def test_fact_proposition(self):
        string = 'A movie is identified by an id, by a director, by a title, by a year.' \
                 'There is a movie with id equal to 1, with director equal to spielberg, ' \
                 'with title equal to jurassicPark, with year equal to 1993.'
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''movie(1,"spielberg","jurassicPark",1993).''')

    def test_weak_constraint_with_comparison(self):
        string = '''A movie is identified by an id, and has a title, a director, and a year.
A director is identified by a name.
A topMovie is identified by an id.
A scoreAssignment is identified by a movie, and by a value.
It is preferred as little as possible, with high priority, that V is equal to 1, whenever there is a scoreAssignment with movie I, and with value V, whenever there is a topMovie with id I.
        '''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), ''':~ V = 1, scoreassignment(I,V), topmovie(I). [1@3,I,V]''')

    def test_weak_constraint_with_variable_maximized(self):
        string = '''A movie is identified by an id, and has a title, a director, and a year.
A director is identified by a name.
A topMovie is identified by an id.
A scoreAssignment is identified by a movie, and by a value.
It is preferred, with medium priority, that whenever there is a topMovie with id I, whenever there is a scoreAssignment with movie I, and with value V, V is maximized.
                '''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), ''':~ topmovie(I), scoreassignment(I,V). [-V@2,I,V]''')

    def test_weak_csontraint_with(self):
        string = '''A movie is identified by an id, and has a title, a director, and a year.
A director is identified by a name.
A topMovie is identified by an id.
A scoreAssignment is identified by a movie, and by a value.
It is preferred, with medium priority, that the total value of a scoreAssignment is maximized.'''
        asp = self.compute_asp(string)
        asp = asp.strip().split()
        asp[4] = 'X.'
        asp[5] = '[-X@2]'
        asp = ' '.join(asp)
        self.assertEqual(asp, ''':~ #sum{VL: scoreassignment(_,VL)} = X. [-X@2]''')

    def test_variable_substitution(self):
        string = '''
        A node is identified by an id.
        Node 1 is connected to node X, where X is one of 2, 3, 4.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''connected_to(1,X) :- node(1), node(X), X = 2.
connected_to(1,X) :- node(1), node(X), X = 3.
connected_to(1,X) :- node(1), node(X), X = 4.''')

    def test_temporal_definitions_and_constraints(self):
        string = '''A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
An entity is identified by an id, and by a timeslot.
It is required that the entity E is after 11:20 AM.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), ''':- entity(_,TMSLT_NTTY), TMSLT_NTTY <= 23.''')

    def test_artithmentic_operations_with_parameters(self):
        string = '''A day is identified by a day.
A patient is identified by an id, and has a preference.
It is required that the sum between the id of the patient I, and the day of the day is equal to 1.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), ''':- patient(PTNT_D,_), day(DY_DY), PTNT_D + DY_DY != 1.''')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_duration_clause_with_parameter_as_entity(self, mock_uuid):
        mock_uuid.return_value = "support"
        string = '''A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
A day is identified by a day.
A patient is identified by an id, and has a preference.

Whenever there is a patient P, whenever there is a timeslot T, then we can have a position in a day D for 2 timeslots.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''{x_support(D,P,T): day(D)} 1 :- patient(P,_), timeslot(T).
position_in(X_SPPRT_DY,P,T..T+2) :- patient(P,_), timeslot(T), x_support(X_SPPRT_DY,P,T).''')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_duration_clause_with_parameter_as_attribute(self, mock_uuid):
        mock_uuid.return_value = "support"
        string = '''A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
    A day is identified by a day.
    A patient is identified by an id, and has a preference.

    Whenever there is a patient P, then we can have a position with timeslot T in a day D for 2 timeslots.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), '''{x_support(D,P,T): day(D)} 1 :- patient(P,_).
position_in(X_SPPRT_DY,P,T..T+2) :- patient(P,_), x_support(X_SPPRT_DY,P,T).''')

    def test_substitute_subsequent_event(self):
        string = """
A time is a temporal concept expressed in steps ranging from 1 to 10.
A joint is identified by an id.
An rotation is identified by a value.
A position is identified by a joint, by an rotation, and by a time.
It is required that the rotation A1 of the position P1 is equal to the rotation A2 of the position P2, whenever there is a position P1 with joint J, with rotation A1, and with time T, whenever there is a position P2 the next step with joint J, and with rotation A2."""
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), ''':- A1 != A2, position(J,A1,T), position(J,A2,T+1).''')

    def test_entity_as_parameter(self):
        string = """
        A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
        A patient is identified by an id, and has a preference.
A registration is identified by a patient, and by an order, and has a number of waiting days, a duration of the first phase, a duration of the second phase, a duration of the third phase, and a duration of the fourth phase.
        Whenever there is a registration R with patient P, with order OR, and with a number of waiting days W, then we can have an assignment with registration R to exactly 1 timeslot."""
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         '''1 {assignment_to(P,OR,TMSLT_TMSLT): timeslot(TMSLT_TMSLT)} 1 :- registration(P,OR,W,_,_,_,_).''')

    def test_handle_duplicated_parameters(self):
        """
        Since there are multiple entities with parameter id, we expect position in to have different id attributes.
        An id is declared for position in, however being initialized with the same value of seat, it is the
        same id attribute of the entity seat.
        """
        string = """
        A patient is identified by an id.
        A seat is identified by an id.
        Whenever there is a patient P, then P can have a position with id S in exactly 1 seat S."""
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         '''1 {position_in(S,P): seat(S)} 1 :- patient(P).''')

    def test_aggregate_with_objects(self):
        string = """
        A patient is identified by an id.
        A seat is identified by an id.
        Whenever there is a patient P then P can have a position in exactly 1 seat S.
        It is required that the number of patient that have a position in seat S is less than 2.
        """
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         '''1 {position_in(P,S): seat(S)} 1 :- patient(P).\n:- seat(S), #count{D: position_in(D,S)} >= 2.''')

    def test_angle_operation(self):
        string = '''An angle is identified by a value.
A rotation is identified by a first joint, by a second joint, by a desired angle, by a current angle, and by a time.
It is required that the desired angle A of the rotation R is different from the current angle AI of the rotation R,  whenever there is a rotation R with desired angle A, and with current angle AI.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         ''':- (A)/360 = (AI)/360, rotation(_,_,A,AI,_).''')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_operation_between_two_aggregate(self, mock_uuid):
        mock_uuid.side_effect = ['X', 'Y']
        string = '''
A patient is identified by an id, and has a preference.
An assignment is identified by a patient, by a day, and by a timeslot.
It is required that the number of patient that have an assignment with day D, with timeslot TS is less than the number of patient that have an assignment with day D+1, with timeslot TS.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         ''':- #count{D1: assignment(D1,D,TS)} = x_X, #count{D2: assignment(D2,D+1,TS)} = x_Y, x_X >= x_Y.''')


    def test_do_not_link_choice_elements_with_body(self):
        string = '''
        A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
A day is a temporal concept expressed in days ranging from 01/01/2022 to 07/01/2022.
A patient is identified by an id, and has a preference.
A registration is identified by a patient, and by an order, and has a number of waiting days, a duration of the first phase, a duration of the second phase, a duration of the third phase, and a duration of the fourth phase.
An assignment is identified by a registration, by a day, and by a timeslot.
A registration is identified by a patient, and by an order, and has a number of waiting days, a duration of the first phase, a duration of the second phase, a duration of the third phase, and a duration of the fourth phase.
        Whenever there is a registration R with patient P, with order OR, and with a number of waiting days W, whenever there is an assignment with registration patient P, with registration order OR-1, and with day D, whenever there is a day with day D+W, then we can have an assignment with registration R, and with day D+W to exactly 1 timeslot.
        '''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         '''1 {assignment_to(D+W,P,OR,TMSLT_TMSLT): timeslot(TMSLT_TMSLT)} 1 :- registration(P,OR,W,_,_,_,_), assignment(P,OR-1,D,_), day(D+W).''')

    def test_remove_duplicates_from_condition(self):
        string = '''
        A node goes from 1 to 5.
        Every node X can have a path to a node connected to node X.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(),
                         '''node(1..5).\n {path_to(CNNCTD_T_D): node(CNNCTD_T_D), connected_to(CNNCTD_T_D)} 1 :- node(X).''')

    def test_parameter_temporal_ordering(self):
        string = '''
        A time is a temporal concept expressed in steps ranging from 1 to 10.
        A joint is identified by an id.
        An angle is identified by a value.
        A position is identified by a joint, by an angle, and by a time.
        A link is identified by a first joint, and by a second joint.
        A rotation is identified by a first joint, by a second joint, by a desired angle, by a current angle, and by a time.
        A goal is identified by a joint, and by an angle.
        It is required that the angle A1 of the position P1 is equal to the angle A2 of the position P2, whenever there is a position P1 with joint J1, with angle A1, and with time T, whenever there is a position P2 with joint J1, and with angle A2, and with the next step respect to T, whenever there is a rotation with first joint J2 greater than J1, and with time T not after timemax.
        '''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), ':- (A1)/360 != (A2)/360, position(J1,A1,T), position(J1,A2,T+1), J2 > J1, T <= "timemax", rotation(J2,_,_,_,T).')

    def test_simple_definition(self):
        string = '''John is a waiter.'''
        asp = self.compute_asp(string)
        self.assertEqual(asp.strip(), 'waiter("John").')

if __name__ == '__main__':
    unittest.main()
