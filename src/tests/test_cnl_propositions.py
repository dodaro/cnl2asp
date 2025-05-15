import os
import unittest
from textwrap import dedent
from unittest.mock import patch

from lark import Lark

from cnl2asp.ASP_elements.asp_program import ASPProgram
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.parser.parser import CNLTransformer
from cnl2asp.specification.signaturemanager import SignatureManager

cnl_parser = Lark(open(os.path.join(os.path.dirname(__file__), "..", "cnl2asp", "grammar.lark"), "r").read())


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
        self.assertEqual(asp.strip(), dedent(expected_output))

    def test_constant_numeric(self):
        self.check_input_to_output('k is a constant equal to 20.', '#const k = 20.')

    def test_constant_string(self):
        self.check_input_to_output('k is a constant equal to Kelvin.', '#const k = "Kelvin".')

    def test_whenever_then_clause_proposition(self):
        self.check_input_to_output('''\
                                    An entity1 is identified by a field1. 
                                    An entity2 is identified by a field2. 
                                    Whenever there is an entity1 E with a field1 F, 
                                         then E can have a relation exactly 1 entity2.''',
                                   '1 <= {relation(F,NTTY2_FLD2): entity2(NTTY2_FLD2)} <= 1 :- entity1(F).')

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
                                    It is required that the total value of a scoreAssignment with movie X is equal to 10, 
                                        such that there is a topMovie with id X.''',
                                   ':- #sum{VL: scoreassignment(X,VL), topmovie(X)} != 10.')

    def test_constraint_with_variable_comparison(self):
        self.check_input_to_output('''\
                                    A entity is identified by an field.
                                    It is required that X is equal to 1, whenever there is an entity with field X.''',
                                   ':- X != 1, entity(X).')

    def test_when_then_constraint(self):
        self.check_input_to_output('''
                                    A pub is identified by an id.
                                    A waiter is identified by an id.
                                    Every waiter can work in a pub.
                                    It is required that when waiter X works in pub P1 then waiter X does not work in pub P2, where P1 is different from P2.''',
                                   '''\
                                   {work_in(WTR_D,PB_D): pub(PB_D)} :- waiter(WTR_D).
                                   :- work_in(X,P1), pub(P1), waiter(X), work_in(X,P2), pub(P2), P1 != P2.''')

    def test_quantified_simple_clause_constraint(self):
        self.check_input_to_output('''
                                    A waiter is identified by an id.
                                    A payed is identified by a waiter.
                                    It is required that every waiter is payed.''',
                                   ':- waiter(PYD_D), not payed(PYD_D).')

    def test_enumerative_definition(self):
        self.check_input_to_output('''
                                    A waiter is identified by an id.
                                    A pub is identified by an id.
                                    Waiter W works in pub P.''',
                                   'work_in(W,P) :- waiter(W), pub(P).')

    def test_compounded_clause_definition(self):
        self.check_input_to_output('A day goes from 1 to 365.', 'day(1..365).')

    def test_compounded_clause_match(self):
        self.check_input_to_output('A color is one of red, green, blue.',
                                   'color("red").\ncolor("green").\ncolor("blue").')

    def test_compounded_clause_match_with_tail(self):
        self.check_input_to_output(
            'A drink is one of alcoholic, nonalcoholic and has color that is equal to respectively blue, yellow.',
            'drink("alcoholic","blue").\ndrink("nonalcoholic","yellow").')

    def test_fact_proposition(self):
        self.check_input_to_output('A movie is identified by an id, by a director, by a title, by a year.' \
                                   'There is a movie with id equal to 1, with director equal to spielberg, ' \
                                   'with title equal to jurassicPark, with year equal to 1993.',
                                   '''movie(1,"spielberg","jurassicPark",1993).''')

    def test_weak_constraint_with_comparison(self):
        self.check_input_to_output('''
                                    A movie is identified by an id.
                                    It is preferred as little as possible, with high priority, that V is equal to 1, 
                                        whenever there is a movie with id V.''',
                                   ':~ V = 1, movie(V). [1@3,V]')

    def test_weak_constraint_with_variable_maximized(self):
        self.check_input_to_output('''
                                    A movie is identified by an id.
                                    It is preferred, with medium priority, that 
                                        whenever there is a movie with id V, V is maximized.''',
                                   ':~ movie(V). [-V@2,V]')

    def test_weak_constraint_with_aggregate(self):
        self.check_input_to_output('''
                                    A movie is identified by an id.
                                    It is preferred, with medium priority, that the total id of a movie is minimized.''',
                                   ':~ #sum{D: movie(D)} = SM. [SM@2]')

    def test_variable_substitution(self):
        self.check_input_to_output('''
                                    A node is identified by an id.
                                    Node 1 is connected to node X, where X is one of 2, 3, 4.''',
                                   '''\
                                    connected_to(1,X) :- node(1), node(X), X = 2.
                                    connected_to(1,X) :- node(1), node(X), X = 3.
                                    connected_to(1,X) :- node(1), node(X), X = 4.''')

    def test_temporal_definitions_and_constraints_after(self):
        self.check_input_to_output('''
                                    A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM 
                                        to 07:50 AM with a length of 10 minutes.
                                    An entity is identified by a timeslot.
                                    It is required that the entity is after 07:40 AM.''',
                                   '''\
                                    timeslot(0,"07:30 AM").
                                    timeslot(1,"07:40 AM").
                                    timeslot(2,"07:50 AM").
                                    :- entity(TMSLT_NTTY), TMSLT_NTTY <= 1.''')

    def test_arithmetic_operations_with_parameters(self):
        self.check_input_to_output('''
                                    A day is identified by an id.
                                    A patient is identified by an id.
                                    It is required that the sum between the id of the patient I, 
                                        and the id of the day is equal to 1.''',
                                   ':- patient(PTNT_D), day(DY_D), (PTNT_D + DY_D) != 1.')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_duration_clause(self, mock_uuid):
        mock_uuid.return_value = "support"
        self.check_input_to_output('''
                                    A timeslot is a temporal concept expressed in minutes ranging 
                                        from 07:30 AM to 07:40 AM with a length of 10 minutes.
                                    A patient is identified by an id.
                                    Whenever there is a patient P, whenever there is a timeslot T, 
                                        then we can have an assignment for 2 timeslots.''',
                                   '''\
                                    timeslot(0,"07:30 AM").
                                    timeslot(1,"07:40 AM").
                                    {x_support(P,T)} :- patient(P), timeslot(T,_).
                                    assignment(P,T..T+2) :- patient(P), timeslot(T,_), x_support(P,T).''')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_duration_clause_with_parameter_as_attribute(self, mock_uuid):
        mock_uuid.return_value = "support"
        self.check_input_to_output('''
                                    A timeslot is a temporal concept expressed in minutes ranging 
                                        from 07:30 AM to 07:40 AM with a length of 10 minutes.
                                    A day is identified by a day.
                                    A patient is identified by an id.
                                    Whenever there is a patient P, then we can have a position 
                                        with timeslot T in a day D for 2 timeslots.''',
                                   '''\
                                    timeslot(0,"07:30 AM").
                                    timeslot(1,"07:40 AM").
                                    {x_support(T,P,D): day(D)} :- patient(P).
                                    position_in(T..T+2,P,X_SPPRT_DY) :- patient(P), x_support(T,P,X_SPPRT_DY).''')

    def test_substitute_subsequent_event_next(self):
        self.check_input_to_output('''
                                    A time is a temporal concept expressed in steps ranging from 1 to 2.
                                    A position is identified by a time.
                                    It is prohibited that there is a position P1 with time T, 
                                        whenever there is a position P2 the next step.''',
                                   '''\
                                    time(0,"1").
                                    time(1,"2").
                                    :- position(T), position(T+1).''')

    def test_substitute_subsequent_event_previous(self):
        self.check_input_to_output('''
                                    A time is a temporal concept expressed in steps ranging from 1 to 2.
                                    A position is identified by a time.
                                    It is prohibited that there is a position P1 with time T, 
                                        whenever there is a position P2 the previous step.''',
                                   '''\
                                    time(0,"1").
                                    time(1,"2").
                                    :- position(T), position(T-1).''')

    def test_entity_as_parameter(self):
        self.check_input_to_output("""
                                    A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to
                                        07:40 AM with a length of 10 minutes.
                                    A patient is identified by an id, and has a preference.
                                    A registration is identified by a patient.
                                    Whenever there is a registration R with patient P, then we can have an assignment with registration R.""",
                                   '''\
                                    timeslot(0,"07:30 AM").
                                    timeslot(1,"07:40 AM").
                                    {assignment(P)} :- registration(P).''')

    def test_handle_duplicated_parameters(self):
        """
        Parameters with same name and different origin should be considered different.
        Also testing initialization can recognize same value.
        """
        self.check_input_to_output('''
                                    A node is identified by an id.
                                    A vtx is identified by an id.
                                    Whenever there is a node N, then N can have a link1 with id V to vtx V.
                                    Whenever there is a node N, then N can have a link2 with id K to vtx V.''',
                                   '''\
                                    {link1(V,N): vtx(V)} :- node(N).
                                    {link2(K,N,V): vtx(V)} :- node(N).''')

    def test_aggregate_with_objects(self):
        self.check_input_to_output('''
                                    A patient is identified by an id.
                                    A seat is identified by an id.
                                    Whenever there is a patient P then P can have a position in exactly 1 seat S.
                                    It is required that the number of patient that have a position in seat S is less than 2.''',
                                   '''\
                                    1 <= {position_in(P,S): seat(S)} <= 1 :- patient(P).
                                    :- #count{D: position_in(D,S), seat(S)} >= 2.''')

    def test_simple_aggregate(self):
        self.check_input_to_output('''
                                    A positivematch is identified by a match.
                                    A negativematch is identified by a match.
                                    It is required that the number of positivematch is equal to the number of negativematch.
                                    It is required that the number of positivematch occurrences is equal to the number of negativematch occurrences.''',
                                   '''\
                                    :- #count{positivematch(PSTVMTCH_MTCH): positivematch(PSTVMTCH_MTCH)} = CNT, #count{negativematch(NGTVMTCH_MTCH): negativematch(NGTVMTCH_MTCH)} = CNT1, CNT != CNT1.
                                    :- #count{positivematch(PSTVMTCH_MTCH): positivematch(PSTVMTCH_MTCH)} = CNT, #count{negativematch(NGTVMTCH_MTCH): negativematch(NGTVMTCH_MTCH)} = CNT1, CNT != CNT1.''')

    def test_angle_operation(self):
        self.check_input_to_output('''
                                    A rotation is identified by a desired angle, by a current angle, and by a value.
                                    It is required that the desired angle A of the rotation R is different from the value D of the rotation R,  
                                        whenever there is a rotation R with desired angle A, and with current angle AI, with value D.
                                    It is required that the desired angle A of the rotation R is different from the value D of the rotation R,  
                                        whenever there is a rotation R with current angle AI.''',
                                   '''\
                                    :- (A)/360 = (D)/360, rotation(A,AI,D).
                                    :- (A)/360 = (D)/360, rotation(A,AI,D).''')

    def test_operation_between_two_aggregate(self):
        self.check_input_to_output('''
                                    An assignment is identified by a patient, by a day.
                                    It is required that the number of patient that have an assignment with day D 
                                        is less than the number of patient that have an assignment with day D+1.''',
                                   ''':- #count{PTNT: assignment(PTNT,D)} = CNT, #count{PTNT1: assignment(PTNT1,D+1)} = CNT1, CNT >= CNT1.''')

    def test_aggregate_range(self):
        self.check_input_to_output('''
                                    A top_Movie is identified by an id.
                                    A score_Assignment is identified by an id, by a second, by a value.
                                    It is prohibited that the total value, for each id, second, that have a score_assignment with id X is between 1 and 2.''',
                                   ':- 1 <= #sum{VL,X,SCND: score_assignment(X,SCND,VL)} <= 2.')

    def test_whenever_clause_with_aggregate(self):
        self.check_input_to_output('''
                                    A top_Movie is identified by an id.
                                    A score_Assignment is identified by an id, and by a value.
                                    Whenever we have that the total value, for each id, that have a score_assignment with id X is between 1 and 2, 
                                        then we can have a movie with id X.''',
                                   '''{movie(X)} :- 1 <= #sum{VL,X: score_assignment(X,VL)} <= 2.''')

    def test_do_not_link_choice_elements_with_body(self):
        self.check_input_to_output('''
                                    A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 07:40 AM with a length of 10 minutes.
                                    An assignment is identified by a registration, and by a timeslot.
                                    Whenever there is an assignment, then we can have an assignment with registration R to exactly 1 timeslot.''',
                                   '''\
                                    timeslot(0,"07:30 AM").
                                    timeslot(1,"07:40 AM").
                                    1 <= {assignment(R,TMSLT_TMSLT): timeslot(TMSLT_TMSLT,_)} <= 1 :- assignment(R,_).''')

    def test_head_links(self):
        self.check_input_to_output('''
                                    A node is identified by an id.
                                    An edge is identified by an first node, by a second node, and has a weight.
                                    Whenever there is a node N, whenever there is an edge with first node F, with second node S, 
                                        then N can have a test. 
                                    Whenever there is a node N, whenever there is an edge with first node F, with second node S, 
                                        then we can have a test2.
                                    Whenever there is a node N, whenever there is an edge E with first node F, with second node S, with weight W, 
                                        then E can have a test3.
                                    It is prohibited that there is test3 with edge first node F, with edge second node S, with edge weight W. 
                                    Every edge with first node X, with weight Y can have a test4.''',
                                   '''\
                                   {test(N)} :- node(N), edge(F,S,_).
                                   {test2(N,F,S)} :- node(N), edge(F,S,_).
                                   {test3(W,F,S)} :- node(N), edge(F,S,W).
                                   :- test3(W,F,S).
                                   {test4(Y,X,DG_SCND_ND)} :- edge(X,DG_SCND_ND,Y).''')

    def test_remove_duplicates_from_condition(self):
        self.check_input_to_output('''
                                    A node is identified by an id.
                                    Every node X can have a path to a node connected to node X.''',
                                   '{path(CNNCTD_T_D,X): node(CNNCTD_T_D), connected_to(CNNCTD_T_D,X)} :- node(X).')

    def test_parameter_temporal_ordering(self):
        self.check_input_to_output('''
                                    A time is a temporal concept expressed in steps ranging from 1 to 2.
                                    A position is identified by a time.
                                    A rotation is identified by a time.
                                    It is prohibited that there is a position P1 with time T, 
                                        whenever there is a position P2 with the next step respect to T, 
                                        whenever there is a rotation with time T not after timemax.''',
                                   '''\
                                    time(0,"1").
                                    time(1,"2").
                                    :- position(T), position(T+1), rotation(T), T <= "timemax".''')

    def test_simple_definition(self):
        self.check_input_to_output('''John is a waiter.''', 'waiter("John").')

    def test_parameter_entity_link(self):
        self.check_input_to_output('''
                                    Node is identified by an id.
                                    Vertex has an id.
                                    It is required that the id of the node is greater than the id of the vertex.''',
                                   ''':- node(ND_D), vertex(VRTX_D), ND_D <= VRTX_D.''')

    def test_set_entity(self):
        self.check_input_to_output('''
                                    set1 is a set.
                                    set2 is a set.
                                    set1 contains 1, 2, 3.
                                    it is prohibited that X is equal to 1, whenever there is an element X in set1, 
                                        whenever there is an element Y greater than 2 in set2.''',
                                   ''':- X = 1, set("set1",X), set("set2",Y), Y > 2.''')

    def test_list_element(self):
        self.check_input_to_output('''
                                    shift is a list.
                                    shift contains morning, afternoon, night.
                                    A nurse is identified by an id.
                                    It is prohibited that a nurse works in the shift element after night.
                                    It is prohibited that a nurse works in the 1st element in shift.''',
                                   '''\
                                    :- nurse(WRK_N_D), work_in(WRK_N_D,"shift",LMNT), list("shift",LMNT,"morning").
                                    :- nurse(WRK_N_D), work_in(WRK_N_D,"shift",LMNT), list("shift",LMNT,"morning").''')

    def test_priority_level_number(self):
        self.check_input_to_output('''
                                    A served is identified by a drink.
                                    It is preferred with priority 5 that the number of drinks that are served is maximized.''',
                                   ':~ #count{DRNK: served(DRNK)} = CNT. [-CNT@5]')

    def test_label_in_terminal_clause(self):
        self.check_input_to_output('''
                                    A vtx is identified by an id. 
                                    Vtx X have an arc to Vtx Y when Vtx X have an edge to Y.''',
                                    'arc(X,Y) :- vtx(X), edge(X,Y), vtx(Y).')

    def test_multiple_problems(self):
        self.check_input_to_output('''A node is identified by an id.
                                    The following propositions apply in the initial state:
                                    There is a node with id 1.
                                    The following propositions apply in the final state:
                                    There is a node with id 2.''',
                                   '''\
                                    #program initial.
                                    node(1).
                                    
                                    #program final.
                                    node(2).''')

    def test_initially_inside_temporal_formulas(self):
        self.check_input_to_output("""
                                    A monkey is identified by a name.
                                    Whenever there is initially a monkey M or the true constant, then M can jump.""",
                                   """{jump(M)} :- not not &tel {<< monkey(M) | &true}.""")


    def test_quoted_strings(self):
        self.check_input_to_output('A entity is one of "first", "second second".',
                                   'entity("first").\nentity("second second").')
        self.check_input_to_output('A entity is identified by an id.\n'
                                   'There is an entity with id equal to "field value".',
                                   'entity("field value").')
        self.check_input_to_output('A entity is identified by an id.\n'
                                   'Whenever there is an entity with id equal to "field value", '
                                   'then we can have a second_entity with field equal to "field value".',
                                   '{second_entity("field value","field value")} :- entity("field value").')
