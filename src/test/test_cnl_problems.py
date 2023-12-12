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

    @patch('cnl2asp.utility.utility.uuid4')
    def test_cts(self, mock_uuid):
        mock_uuid.return_value = 'support'
        self.check_input_to_output('''A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.
A day is a temporal concept expressed in days ranging from 01/01/2022 to 07/01/2022.
A patient is identified by an id, and has a preference.
A registration is identified by a patient, and by an order, and has a number of waiting days, a duration of the first phase, a duration of the second phase, a duration of the third phase, and a duration of the fourth phase.
A seat is identified by an id, and has a type.
An assignment is identified by a registration, by a day, and by a timeslot.
//A position in is identified by a patient, by an id, by a timeslot, and by a day.
Whenever there is a registration R with an order equal to 0, then R can have an assignment to exactly 1 day, and timeslot.
Whenever there is a registration R with patient P, with order OR, and with a number of waiting days W, whenever there is an assignment with registration patient P, with registration order OR-1, and with day D, whenever there is a day with day D+W, then we can have an assignment with registration R, and with day D+W to exactly 1 timeslot.
It is required that the sum between the duration of the first phase of the registration R, the duration of the second phase of the registration R, and the duration of the third phase of the registration R is greater than the timeslot of the assignment A, whenever there is a registration R, whenever there is an assignment A with registration R, with timeslot T.
Whenever there is a patient P, whenever there is an assignment with registration patient P, with timeslot T, and with day D, whenever there is a registration R with patient P, and with a duration of the fourth phase PH4 greater than 0, then P can have a position with seat id S, with timeslot T, with day D in exactly 1 seat S for PH4 timeslots.
It is required that the number of patient that have position in seat S, day D, timeslot TS is less than 2, whenever there is a day D, whenever there is a timeslot TS, whenever there is a seat with id S.
It is required that the assignment A is after 11:20 AM, whenever there is a registration R with a duration of the fourth phase greater than 50 timeslots, whenever there is an assignment A with registration R.
It is preferred as much as possible, with high priority, that a patient P with preference T has a position in a seat S, whenever there is a seat S with type T.''',
                                   '''day(0,"01/01/2022").
day(1,"02/01/2022").
day(2,"03/01/2022").
day(3,"04/01/2022").
day(4,"05/01/2022").
day(5,"06/01/2022").
day(6,"07/01/2022").
timeslot(0,"07:30 AM").
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
1 <= {assignment_to(DY_DY,RGSTRTN_D,0,TMSLT_TMSLT): day(DY_DY,_), timeslot(TMSLT_TMSLT,_)} <= 1 :- registration(RGSTRTN_D,0,_,_,_,_,_).
1 <= {assignment_to(D+W,P,OR,TMSLT_TMSLT): timeslot(TMSLT_TMSLT,_)} <= 1 :- registration(P,OR,W,_,_,_,_), assignment(P,OR-1,D,_), day(D+W,_).
:- registration(_,_,_,RGSTRTN_DRTN_F_TH_FRST_PHS,RGSTRTN_DRTN_F_TH_SCND_PHS,RGSTRTN_DRTN_F_TH_THRD_PHS,_), assignment(_,_,_,T), (RGSTRTN_DRTN_F_TH_FRST_PHS + RGSTRTN_DRTN_F_TH_SCND_PHS + RGSTRTN_DRTN_F_TH_THRD_PHS) <= T, registration(RGSTRTN_D,RGSTRTN_RDR,_,RGSTRTN_DRTN_F_TH_FRST_PHS,RGSTRTN_DRTN_F_TH_SCND_PHS,RGSTRTN_DRTN_F_TH_THRD_PHS,_), assignment(RGSTRTN_D,RGSTRTN_RDR,_,T).
1 <= {x_support(D,S,P,SSGNMNT_RDR,T): seat(S,_)} <= 1 :- patient(P,_), assignment(P,SSGNMNT_RDR,D,T), PH4 > 0, registration(P,SSGNMNT_RDR,_,_,_,_,PH4).
position_in(D,S,P,SSGNMNT_RDR,T..T+PH4) :- patient(P,_), assignment(P,SSGNMNT_RDR,D,T), registration(P,SSGNMNT_RDR,_,_,_,_,PH4), x_support(D,S,P,SSGNMNT_RDR,T).
:- #count{D1: position_in(D,S,D1,_,TS), seat(S,_), day(D,_), timeslot(TS,_)} >= 2, day(D,_), timeslot(TS,_), seat(S,_).
:- assignment(_,_,_,TMSLT_SSGNMNT), TMSLT_SSGNMNT <= 23, DRTN_F_TH_FRTH_PHS > 50, registration(RGSTRTN_D,RGSTRTN_RDR,_,_,_,_,DRTN_F_TH_FRTH_PHS), assignment(RGSTRTN_D,RGSTRTN_RDR,_,TMSLT_SSGNMNT).
:~ patient(P,T), position_in(_,S,P,_,_), seat(S,T). [1@3,T,T]''')

    def test_graph_coloring(self):
        self.check_input_to_output('''A node goes from 1 to 3.
A color is one of red, green, blue.

Node 1 is connected to node X, where X is one of 2, 3.
Node 2 is connected to node X, where X is one of 1, 3.
Node 3 is connected to node X, where X is one of 1, 2.

Every node can be assigned to exactly 1 color.

It is required that when node X is connected to node Y then node X is not assigned to color C and also node Y is not assigned to color C.''',
                                   '''node(1..3).
color("red").
color("green").
color("blue").
connected_to(1,X) :- node(1), node(X), X = 2.
connected_to(1,X) :- node(1), node(X), X = 3.
connected_to(2,X) :- node(2), node(X), X = 1.
connected_to(2,X) :- node(2), node(X), X = 3.
connected_to(3,X) :- node(3), node(X), X = 1.
connected_to(3,X) :- node(3), node(X), X = 2.
1 <= {assigned_to(ND_D,CLR_D): color(CLR_D)} <= 1 :- node(ND_D).
:- connected_to(X,Y), node(X), assigned_to(X,C), node(Y), assigned_to(Y,C), color(C).''')

    @patch('cnl2asp.parser.parser.uuid4')
    def test_input_file(self, mock_uuid):
        mock_uuid.return_value = 'TOT'
        self.check_input_to_output('''A movie is identified by an id, and has a title, a director, and a year.
A director is identified by a name.
A topMovie is identified by an id.
A scoreAssignment is identified by a movie, and by a value.
A timeslot is a temporal concept expressed in minutes ranging from 07:00 AM to 09:00 AM with a length of 30 minutes.
minKelvinTemperature is a constant equal to 0.
acceptableTemperature is a constant.
A ColdTemperature goes from minKelvinTemperature to acceptableTemperature.
A day goes from 1 to 365.
A drink is one of alcoholic, nonalcoholic.
 //and has color that is equal to respectively blue, yellow.
John is a waiter.
1 is a pub.
Alice is a patron.
Pub 1 is close to pub 2, and pub X where X is one of 3,4.
Waiter John works in pub 1.
Waiter John serves a drink alcoholic.
Waiter W is working when waiter W serves a drink.
Whenever there is a movie with director equal to spielberg, with id X then we must have a topmovie with id X.
Whenever there is a director with name X different from spielberg then we can have at most 1 topmovie with id I such that there is a movie with director X, and with id I.
Whenever there is a movie with id I, with director equal to nolan then we can have a scoreAssignment with movie I, and with value equal to 3 or a scoreAssignment with movie I, and with value equal to 2.
There is a movie with id equal to 1, with director equal to spielberg, with title equal to jurassicPark, with year equal to 1993.
There is a movie with id equal to 1, with director equal to spielberg, with year equal to 1993, with title equal to jurassicPark.
There is a movie with director equal to spielberg, with year equal to 1993, with id equal to 1, with title equal to jurassicPark.
Every patron can drink in exactly 1 pub for each day.
Every waiter can serve a drink.
Every movie with id I can have a scoreAssignment with movie I, and with value equal to 1 or a scoreAssignment with movie I, and with value equal to 2, or a scoreAssignment with movie I, and with value equal to 3.
It is prohibited that waiter W1 work in pub P1 and also waiter W2 work in pub P1, where W1 is different from W2.
It is prohibited that X is equal to Y, whenever there is a movie with id X, and with year equal to 1964, whenever there is a topMovie with id Y.
It is prohibited that the lowest value of a scoreAssignment with movie id X is equal to 1, whenever there is a topMovie with id X.
It is required that the total value of a scoreAssignment with movie id X is equal to 10, such that there is a topMovie with id X.
It is required that the number of pub where a waiter work in is less than 2.
It is required that when waiter X works in pub P1 then waiter X does not work in pub P2, where P1 is different from P2.
It is required that V is equal to 3, whenever there is a movie with id I, and with director equal to spielberg, whenever there is a scoreAssignment with movie I, and with value V.
It is required that every waiter is payed.
It is preferred with low priority that the number of drinks that are serve is maximized.
It is preferred as little as possible, with high priority, that V is equal to 1, whenever there is a scoreAssignment with movie I, and with value V, whenever there is a topMovie with id I.
It is preferred, with medium priority, that whenever there is a topMovie with id I, whenever there is a scoreAssignment with movie I, and with value V, V is maximized.
It is preferred, with medium priority, that the total value of a scoreAssignment is maximized.''','''#const minKelvinTemperature = 0.
coldtemperature(minKelvinTemperature..acceptableTemperature).
day(1..365).
drink("alcoholic").
drink("nonalcoholic").
waiter("John").
pub(1).
patron("Alice").
close_to(1,2,X) :- pub(1), pub(2), pub(X), X = 3.
close_to(1,2,X) :- pub(1), pub(2), pub(X), X = 4.
work_in("John",1) :- waiter("John"), pub(1).
serve("John","alcoholic") :- waiter("John"), drink("alcoholic").
working(W) :- serve(W,DRNK_D), drink(DRNK_D), waiter(W).
topmovie(X) :- movie(X,"spielberg",_,_).
{topmovie(I): movie(I,X,_,_)} <= 1 :- X != "spielberg", director(X).
scoreassignment(I,3) | scoreassignment(I,2) :- movie(I,"nolan",_,_).
movie(1,"spielberg","jurassicPark",1993).
movie(1,"spielberg","jurassicPark",1993).
movie(1,"spielberg","jurassicPark",1993).
1 <= {drink_in(DY_D,PTRN_D,PB_D): pub(PB_D)} <= 1 :- day(DY_D), patron(PTRN_D).
{serve(WTR_D,DRNK_D): drink(DRNK_D)} :- waiter(WTR_D).
scoreassignment(I,1) | scoreassignment(I,2) | scoreassignment(I,3) :- movie(I,_,_,_).
:- waiter(W1), work_in(W1,P1), waiter(W2), work_in(W2,P1), pub(P1), W1 != W2.
:- X = Y, movie(X,_,_,1964), topmovie(Y).
:- #min{VL: scoreassignment(X,VL)} = 1, topmovie(X).
:- #sum{VL: scoreassignment(X,VL), topmovie(X)} != 10.
:- waiter(WRK_N_D), #count{D: work_in(WRK_N_D,D)} >= 2.
:- work_in(X,P1), pub(P1), waiter(X), work_in(X,P2), pub(P2), P1 != P2.
:- V != 3, movie(I,"spielberg",_,_), scoreassignment(I,V).
:- waiter(PYD_D), not payed(PYD_D).
:~ #count{D: serve(_,D)} = X_TOT. [-X_TOT@1]
:~ V = 1, scoreassignment(I,V), topmovie(I). [1@3,I,V]
:~ topmovie(I), scoreassignment(I,V). [-V@2,I,V]
:~ #sum{VL: scoreassignment(_,VL)} = X_TOT. [-X_TOT@2]''')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_integer_sets(self, mock_uuid):
        mock_uuid.side_effect = ['TOT1', 'TOT2']
        self.check_input_to_output('''set1 is a set.
set2 is a set.
A match is identified by a first, and by a second.
A positivematch is identified by a match.
A negativematch is identified by a match.

Whenever there is an element X in set1, whenever there is an element Y in set2, then we can have a match with first X, and with second Y.

Whenever there is a match M with first X, and with second Y less than X, then we must have a positivematch with match M.
Whenever there is a match M with first X, and with second Y greater than X, then we must have a negativematch with match M.

It is required that the number of match occurrences with first E is equal to 1, whenever there is an element E in set1.
It is required that the number of match occurrences with second E is equal to 1, whenever there is an element E in set2.

It is required that the number of positivematch is equal to the number of negativematch.''',
                                   '''{match(X,Y)} :- set("set1",X), set("set2",Y).
positivematch(X,Y) :- Y < X, match(X,Y).
negativematch(X,Y) :- Y > X, match(X,Y).
:- #count{match(E,MTCH_SCND): match(E,MTCH_SCND)} != 1, set("set1",E).
:- #count{match(MTCH_FRST,E): match(MTCH_FRST,E)} != 1, set("set2",E).
:- #count{positivematch(PSTVMTCH_FRST,PSTVMTCH_SCND): positivematch(PSTVMTCH_FRST,PSTVMTCH_SCND)} = X_TOT1, #count{negativematch(NGTVMTCH_FRST,NGTVMTCH_SCND): negativematch(NGTVMTCH_FRST,NGTVMTCH_SCND)} = X_TOT2, X_TOT1 != X_TOT2.''')

    def test_mao(self):
        self.check_input_to_output('''A time is a temporal concept expressed in steps ranging from 0 to 10.
A joint is identified by an id.
An angle is identified by a value.
A position is identified by a joint, by an angle, and by a time.
A link is identified by a first joint, and by a second joint.
A rotation is identified by a first joint, by a second joint, by a desired angle, by a current angle, and by a time.
A goal is identified by a joint, and by an angle.
granularity is a constant equal to 90.
timemax is a constant equal to 90.
Whenever there is a link with a first joint J1, and with a second joint J2, then we must have a link with a first joint J2, and with a second joint J1.
Whenever there is a time T that is after 0, then we can have at most 1 rotation with a first joint J1, with a second joint J2, with a desired angle A, with a current angle AI, and with time T such that there is a joint J1, a joint J2, an angle A, a link with first joint J1, and with second joint J2, a position with joint J1, with angle AI, and with time T.
It is required that T is less than timemax, whenever there is a rotation with time T.
It is required that the first joint J1 of the rotation R is greater than the second joint J2 of the rotation R, whenever there is a rotation R with first joint J1, with second joint J2.
It is required that the desired angle A of the rotation R is different from the current angle AI of the rotation R,  whenever there is a rotation R with desired angle A, and with current angle AI.
It is required that the sum between the desired angle A of the rotation R, and granularity is equal to the current angle AI of the rotation R, whenever there is a rotation R with desired angle A greater than 0, with current angle AI greater than A.
It is required that the sum between the current angle AI of the rotation R, and granularity is equal to the desired angle A of the rotation R, whenever there is a rotation R with current angle AI greater than 0, with desired angle A greater than AI.
It is required that the difference between 360, and granularity is equal to the desired angle A of the rotation R, whenever there is a rotation R with desired angle A, and with current angle equal to 0.
It is required that the difference between 360, and granularity is equal to the current angle AI of the rotation R, whenever there is a rotation R with desired angle A equal to 0, and with current angle AI.
Whenever there is a joint J, whenever there is a time T, then we can have a position with joint J, with angle A, and with time T to exactly 1 angle A.
It is required that the angle A1 of the position P1 is equal to the angle A2 of the position P2, whenever there is a position P1 with joint J, with angle A1, and with time T, whenever there is a position P2 the next step with joint J, and with angle A2, whenever there is not a rotation with time T less than or equal to timemax.
It is required that the angle A1 of the position P is equal to the desired angle A2 of the rotation R, whenever there is a position P with joint J1, with time T, with angle A1, whenever there is a rotation R the previous step with first joint J1, and with desired angle A2.
It is required that the angle AN of the position P is equal to |AC+(A-AP)+360|, whenever there is a time T, whenever there is a position P the next step with joint J1, and with angle AN, whenever there is a rotation with first joint J2, with current angle A, with current angle AP, and with time T, whenever there is a position P2 with joint J1 greater than J2, with angle AC, and with time T.
It is required that the angle A1 of the position P1 is equal to the angle A2 of the position P2, whenever there is a position P1 with joint J1, with angle A1, and with time T, whenever there is a position P2 the next step with joint J1, and with angle A2, whenever there is a rotation with first joint J2 greater than J1, and with time T not after timemax.
It is required that the angle A1 of the goal G is equal to the angle A2 of the position P, whenever there is a goal G with joint J, with angle A1, whenever there is a position P with joint J, with angle A2, and with time equal to timemax.''',
                                   '''#const granularity = 90.
#const timemax = 90.
link(J2,J1) :- link(J1,J2).
time(0,"0").
time(1,"1").
time(2,"2").
time(3,"3").
time(4,"4").
time(5,"5").
time(6,"6").
time(7,"7").
time(8,"8").
time(9,"9").
time(10,"10").
{rotation(J1,J2,A,AI,T): joint(J1), joint(J2), angle(A), link(J1,J2), position(J1,AI,T)} <= 1 :- T > 0, time(T,_).
:- T >= timemax, rotation(_,_,_,_,T).
:- J1 <= J2, rotation(J1,J2,_,_,_).
:- (A)/360 = (AI)/360, rotation(_,_,A,AI,_).
:- (A + granularity)/360 != (AI)/360, (A)/360 > (0)/360, (AI)/360 > (A)/360, rotation(_,_,A,AI,_).
:- (AI + granularity)/360 != (A)/360, (A)/360 > (AI)/360, (AI)/360 > (0)/360, rotation(_,_,A,AI,_).
:- (360 - granularity)/360 != (A)/360, rotation(_,_,A,0,_).
:- (360 - granularity)/360 != (AI)/360, (A)/360 = (0)/360, rotation(_,_,A,AI,_).
1 <= {position_to(J,T,A): angle(A)} <= 1 :- joint(J), time(T,_).
:- (A1)/360 != (A2)/360, position(J,A1,T), position(J,A2,T+1), T <= timemax, not rotation(_,_,_,_,T).
:- (A1)/360 != (A2)/360, position(J1,A1,T), rotation(J1,_,A2,_,T-1).
:- (AN)/360 != (|AC+(A-AP)+360|)/360, time(T,_), position(J1,AN,T+1), rotation(J2,_,_,AP,T), J1 > J2, position(J1,AC,T).
:- (A1)/360 != (A2)/360, position(J1,A1,T), position(J1,A2,T+1), J2 > J1, T <= timemax, rotation(J2,_,_,_,T).
:- (A1)/360 != (A2)/360, goal(J,A1), position(J,A2,timemax).''')

    @patch('cnl2asp.parser.parser.uuid4')
    def test_maxclique(self, mock_uuid):
        mock_uuid.return_value = 'TOT'
        self.check_input_to_output('''A node goes from 1 to 5.
Node 1 is connected to node X, where X is one of 2, 3.
Node 2 is connected to node X, where X is one of 1, 3, 4, 5.
Node 3 is connected to node X, where X is one of 1, 2, 4, 5.
Node 4 is connected to node X, where X is one of 2, 3, 5.
Node 5 is connected to node X, where X is one of 2, 3, 4.
Every node can be chosen. 
It is required that when node X is not connected to node Y then node X is not chosen and also node Y is not chosen, where X is different from Y.
It is preferred with high priority that the number of nodes that are chosen is maximized.''',
                                   '''node(1..5).
connected_to(1,X) :- node(1), node(X), X = 2.
connected_to(1,X) :- node(1), node(X), X = 3.
connected_to(2,X) :- node(2), node(X), X = 1.
connected_to(2,X) :- node(2), node(X), X = 3.
connected_to(2,X) :- node(2), node(X), X = 4.
connected_to(2,X) :- node(2), node(X), X = 5.
connected_to(3,X) :- node(3), node(X), X = 1.
connected_to(3,X) :- node(3), node(X), X = 2.
connected_to(3,X) :- node(3), node(X), X = 4.
connected_to(3,X) :- node(3), node(X), X = 5.
connected_to(4,X) :- node(4), node(X), X = 2.
connected_to(4,X) :- node(4), node(X), X = 3.
connected_to(4,X) :- node(4), node(X), X = 5.
connected_to(5,X) :- node(5), node(X), X = 2.
connected_to(5,X) :- node(5), node(X), X = 3.
connected_to(5,X) :- node(5), node(X), X = 4.
{chosen(ND_D)} :- node(ND_D).
:- not connected_to(X,Y), node(X), chosen(X), node(Y), chosen(Y), X != Y.
:~ #count{D: chosen(D)} = X_TOT. [-X_TOT@3]''')

    @patch('cnl2asp.utility.utility.uuid4')
    def test_undirected_graph(self, mock_uuid):
        mock_uuid.side_effect = ['TOT1', 'TOT2', 'TOT1', 'TOT2']
        self.check_input_to_output('''A node is identified by an id, and by a weight.
An edge is identified by a first node id, and by a second node id.
A set is identified by an id.

There is a node with id 1, with weight 1.
There is a node with id 2, with weight 1.
There is a node with id 3, with weight 1.
There is a node with id 4, with weight 1.
There is a node with id 5, with weight 4.

There is a set with id 1.
There is a set with id 2.

There is an edge with first node id equal to 1, with second node id equal to 2.
There is an edge with first node id equal to 1, with second node id equal to 3.
There is an edge with first node id equal to 4, with second node id equal to 5.

Whenever there is a node N, then N can be assigned to exactly 1 set.

It is prohibited that a node with id N1 is assigned to a set S1
and also a node with id N2 is assigned to S1,
whenever there is an edge with first node id N1, with second node id N2.

It is required that the number of node id that are assigned to a set S1
is greater than
the number of node id that are assigned to a set S2, where S1 is equal to 1 and S2 is equal to 2.

It is required that the total of weights that are assigned to a set S2
is greater than or equal to
the total of weights that are assigned to a set S1, where S1 is equal to 1 and S2 is equal to 2.''',
                                   '''node(1,1).
node(2,1).
node(3,1).
node(4,1).
node(5,4).
set(1).
set(2).
edge(1,2).
edge(1,3).
edge(4,5).
1 <= {assigned_to(ND_D,ST_D,ND_WGHT): set(ST_D)} <= 1 :- node(ND_D,ND_WGHT).
:- node(N1,SSGND_T_WGHT), assigned_to(N1,S1,SSGND_T_WGHT), node(N2,SSGND_T_WGHT1), assigned_to(N2,S1,SSGND_T_WGHT1), set(S1), edge(N1,N2).
:- #count{D: assigned_to(D,S1,_), set(S1)} = X_TOT1, #count{D1: assigned_to(D1,S2,_), set(S2)} = X_TOT2, X_TOT1 <= X_TOT2, S1 = 1, S2 = 2.
:- #sum{WGHT: assigned_to(_,S2,WGHT), set(S2)} = X_TOT1, #sum{WGHT1: assigned_to(_,S1,WGHT1), set(S1)} = X_TOT2, X_TOT1 < X_TOT2, S1 = 1, S2 = 2.''')

    def test_aggregate_range(self):
        self.check_input_to_output('''A top_Movie is identified by an id.
A score_Assignment is identified by an id, and by a va_lue.

It is prohibited that the total va_lue, for each id, that have a score_assignment with id X is between 1 and 2.''', ''':- 1 <= #sum{V_L,X: score_assignment(X,V_L)} <= 2.''')

    def test_whenever_clause_with_aggregate(self):
        self.check_input_to_output('''A top_Movie is identified by an id.
A score_Assignment is identified by an id, and by a value.

Whenever we have that the total value, for each id, that have a score_assignment with id X is between 1 and 2, then we can have a movie.''', '''{movie(X,VL)} :- 1 <= #sum{VL,X: score_assignment(X,VL)} <= 2.''')

if __name__ == '__main__':
    unittest.main()
