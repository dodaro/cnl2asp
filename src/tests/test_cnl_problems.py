import os
import unittest
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
Whenever there is a patient P, whenever there is an assignment with registration patient P, with timeslot T, and with day D, whenever there is a registration R with patient P, and with a duration of the fourth phase PH4 greater than 0, then we can have a position with seat id S, with timeslot T, with day D in exactly 1 seat S for PH4 timeslots.
It is required that the number of patient that have position in seat S, day D, timeslot TS is less than 2, whenever there is a day D, whenever there is a timeslot TS, whenever there is a seat with id S.
It is required that the assignment A is after 11:20 AM, whenever there is a registration R with a duration of the fourth phase greater than 50 timeslots, whenever there is an assignment A with registration R.
It is preferred as much as possible, with high priority, that a patient P with preference T has a position in a seat S, whenever there is a seat S with type T.''',
                                   '''\
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
day(0,"01/01/2022").
day(1,"02/01/2022").
day(2,"03/01/2022").
day(3,"04/01/2022").
day(4,"05/01/2022").
day(5,"06/01/2022").
day(6,"07/01/2022").
1 <= {assignment(RGSTRTN_D,0,DY_DY,TMSLT_TMSLT): day(DY_DY,_), timeslot(TMSLT_TMSLT,_)} <= 1 :- registration(RGSTRTN_D,0,_,_,_,_,_).
1 <= {assignment(P,OR,D+W,TMSLT_TMSLT): timeslot(TMSLT_TMSLT,_)} <= 1 :- registration(P,OR,W,_,_,_,_), assignment(P,OR-1,D,_), day(D+W,_).
:- registration(_,_,_,RGSTRTN_DRTN_F_TH_FRST_PHS,RGSTRTN_DRTN_F_TH_SCND_PHS,RGSTRTN_DRTN_F_TH_THRD_PHS,_), assignment(_,_,_,T), (RGSTRTN_DRTN_F_TH_FRST_PHS + RGSTRTN_DRTN_F_TH_SCND_PHS + RGSTRTN_DRTN_F_TH_THRD_PHS) <= T, registration(RGSTRTN_D,RGSTRTN_RDR,_,RGSTRTN_DRTN_F_TH_FRST_PHS,RGSTRTN_DRTN_F_TH_SCND_PHS,RGSTRTN_DRTN_F_TH_THRD_PHS,_), assignment(RGSTRTN_D,RGSTRTN_RDR,_,T).
1 <= {x_support(S,T,D,P,SSGNMNT_RDR): seat(S,_)} <= 1 :- patient(P,_), assignment(P,SSGNMNT_RDR,D,T), registration(P,SSGNMNT_RDR,_,_,_,_,PH4), PH4 > 0.
position_in(S,T..T+PH4,D,P,SSGNMNT_RDR) :- patient(P,_), assignment(P,SSGNMNT_RDR,D,T), registration(P,SSGNMNT_RDR,_,_,_,_,PH4), x_support(S,T,D,P,SSGNMNT_RDR).
:- #count{D1: position_in(S,TS,D,D1,_), seat(S,_), day(D,_), timeslot(TS,_)} >= 2, day(D,_), timeslot(TS,_), seat(S,_).
:- assignment(_,_,_,TMSLT_SSGNMNT), TMSLT_SSGNMNT <= 23, registration(RGSTRTN_D,RGSTRTN_RDR,_,_,_,_,DRTN_F_TH_FRTH_PHS), assignment(RGSTRTN_D,RGSTRTN_RDR,_,TMSLT_SSGNMNT), DRTN_F_TH_FRTH_PHS > 50.
:~ patient(P,T), position_in(S,_,_,P,_), seat(S,T). [1@3,T]''')

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

    def test_ham_path(self):
        self.check_input_to_output('''A path is identified by a first node, by a second node.
A node goes from 1 to 5.
Node 1 is connected to node X, where X is one of 2, 3.
Node 2 is connected to node X, where X is one of 1, 4.
Node 3 is connected to node X, where X is one of 1, 4.
Node 4 is connected to node X, where X is one of 3, 5.
Node 5 is connected to node X, where X is one of 3, 4.
start is a constant equal to 1.
Every node X can have a path with first node X, with second node Y to a node Y connected to node X.
It is required that the number of nodes where node X has a path with first node X, with second node Y to node Y is equal to 1.
It is required that the number of nodes where node Y has a path with first node X, with second node Y to node X is equal to 1.
Node start is reachable.
Node Y is reachable when node X is reachable and also node X has a path with first node X, with second node Y to node Y.
It is required that every node is reachable.
''', '''\
#const start = 1.
node(1..5).
connected_to(1,X) :- node(1), node(X), X = 2.
connected_to(1,X) :- node(1), node(X), X = 3.
connected_to(2,X) :- node(2), node(X), X = 1.
connected_to(2,X) :- node(2), node(X), X = 4.
connected_to(3,X) :- node(3), node(X), X = 1.
connected_to(3,X) :- node(3), node(X), X = 4.
connected_to(4,X) :- node(4), node(X), X = 3.
connected_to(4,X) :- node(4), node(X), X = 5.
connected_to(5,X) :- node(5), node(X), X = 3.
connected_to(5,X) :- node(5), node(X), X = 4.
{path(X,Y): node(Y), connected_to(Y,X)} :- node(X).
:- node(X), #count{Y: path(X,Y), node(Y)} != 1.
:- node(Y), #count{X: path(X,Y), node(X)} != 1.
reachable(start) :- node(start).
reachable(Y) :- reachable(X), node(X), path(X,Y), node(Y).
:- node(RCHBL_D), not reachable(RCHBL_D).''')

    def test_input_file(self):
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
Whenever there is a movie with id I, with director equal to nolan then we must have a scoreAssignment with movie I, and with value equal to 3 or a scoreAssignment with movie I, and with value equal to 2.
There is a movie with id equal to 1, with director equal to spielberg, with title equal to jurassicPark, with year equal to 1993.
There is a movie with id equal to 1, with director equal to spielberg, with year equal to 1993, with title equal to jurassicPark.
There is a movie with director equal to spielberg, with year equal to 1993, with id equal to 1, with title equal to jurassicPark.
Every patron can drink in exactly 1 pub for each day.
Every waiter can serve a drink.
Every movie with id I must have a scoreAssignment with movie I, and with value equal to 1 or a scoreAssignment with movie I, and with value equal to 2, or a scoreAssignment with movie I, and with value equal to 3.
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
timeslot(0,"07:00 AM").
timeslot(1,"07:30 AM").
timeslot(2,"08:00 AM").
timeslot(3,"08:30 AM").
timeslot(4,"09:00 AM").
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
working(W) :- waiter(W), serve(W,DRNK_D), drink(DRNK_D).
topmovie(X) :- movie(X,_,_,"spielberg").
{topmovie(I): movie(I,_,_,X)} <= 1 :- director(X), X != "spielberg".
scoreassignment(I,3) | scoreassignment(I,2) :- movie(I,_,_,"nolan").
movie(1,"jurassicPark",1993,"spielberg").
movie(1,"jurassicPark",1993,"spielberg").
movie(1,"jurassicPark",1993,"spielberg").
1 <= {drink_in(DY_D,PTRN_D,PB_D): pub(PB_D)} <= 1 :- day(DY_D), patron(PTRN_D).
{serve(WTR_D,DRNK_D): drink(DRNK_D)} :- waiter(WTR_D).
scoreassignment(I,1) | scoreassignment(I,2) | scoreassignment(I,3) :- movie(I,_,_,_).
:- waiter(W1), work_in(W1,P1), waiter(W2), work_in(W2,P1), pub(P1), W1 != W2.
:- X = Y, movie(X,_,1964,_), topmovie(Y).
:- #min{VL: scoreassignment(X,VL)} = 1, topmovie(X).
:- #sum{VL: scoreassignment(X,VL), topmovie(X)} != 10.
:- waiter(WRK_N_D), #count{D: work_in(WRK_N_D,D)} >= 2.
:- work_in(X,P1), pub(P1), waiter(X), work_in(X,P2), pub(P2), P1 != P2.
:- V != 3, movie(I,_,_,"spielberg"), scoreassignment(I,V).
:- waiter(PYD_D), not payed(PYD_D).
:~ #count{D: serve(_,D)} = CNT. [-CNT@1]
:~ V = 1, scoreassignment(I,V), topmovie(I). [1@3,I,V]
:~ topmovie(I), scoreassignment(I,V). [-V@2,I,V]
:~ #sum{VL: scoreassignment(_,VL)} = SM. [-SM@2]''')

    def test_integer_sets(self):
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
positivematch(X,Y) :- match(X,Y), Y < X.
negativematch(X,Y) :- match(X,Y), Y > X.
:- #count{match(E,MTCH_SCND): match(E,MTCH_SCND)} != 1, set("set1",E).
:- #count{match(MTCH_FRST,E): match(MTCH_FRST,E)} != 1, set("set2",E).
:- #count{positivematch(PSTVMTCH_FRST,PSTVMTCH_SCND): positivematch(PSTVMTCH_FRST,PSTVMTCH_SCND)} = CNT, #count{negativematch(NGTVMTCH_FRST,NGTVMTCH_SCND): negativematch(NGTVMTCH_FRST,NGTVMTCH_SCND)} = CNT1, CNT != CNT1.''')

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
link(J2,J1) :- link(J1,J2).
{rotation(J1,J2,A,AI,T): joint(J1), joint(J2), angle(A), link(J1,J2), position(J1,AI,T)} <= 1 :- T > 0, time(T,_).
:- T >= timemax, rotation(_,_,_,_,T).
:- J1 <= J2, rotation(J1,J2,_,_,_).
:- (A)/360 = (AI)/360, rotation(_,_,A,AI,_).
:- (A + granularity)/360 != (AI)/360, rotation(_,_,A,AI,_), (A)/360 > (0)/360, (AI)/360 > (A)/360.
:- (AI + granularity)/360 != (A)/360, rotation(_,_,A,AI,_), (A)/360 > (AI)/360, (AI)/360 > (0)/360.
:- (360 - granularity)/360 != (A)/360, rotation(_,_,A,0,_).
:- (360 - granularity)/360 != (AI)/360, rotation(_,_,A,AI,_), (A)/360 = (0)/360.
1 <= {position(J,A,T): angle(A)} <= 1 :- joint(J), time(T,_).
:- (A1)/360 != (A2)/360, position(J,A1,T), position(J,A2,T+1), not rotation(_,_,_,_,T), T <= timemax.
:- (A1)/360 != (A2)/360, position(J1,A1,T), rotation(J1,_,A2,_,T-1).
:- (AN)/360 != (|AC+(A-AP)+360|)/360, time(T,_), position(J1,AN,T+1), rotation(J2,_,_,AP,T), position(J1,AC,T), J1 > J2.
:- (A1)/360 != (A2)/360, position(J1,A1,T), position(J1,A2,T+1), rotation(J2,_,_,_,T), J2 > J1, T <= timemax.
:- (A1)/360 != (A2)/360, goal(J,A1), position(J,A2,timemax).''')

    def test_maxclique(self):
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
:~ #count{D: chosen(D)} = CNT. [-CNT@3]''')

    def test_undirected_graph(self):
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
1 <= {assigned_to(ND_D,ND_WGHT,ST_D): set(ST_D)} <= 1 :- node(ND_D,ND_WGHT).
:- node(N1,SSGND_T_WGHT), assigned_to(N1,SSGND_T_WGHT,S1), node(N2,SSGND_T_WGHT1), assigned_to(N2,SSGND_T_WGHT1,S1), set(S1), edge(N1,N2).
:- #count{D: assigned_to(D,_,S1), set(S1)} = CNT, #count{D1: assigned_to(D1,_,S2), set(S2)} = CNT1, CNT <= CNT1, S1 = 1, S2 = 2.
:- #sum{WGHT: assigned_to(_,WGHT,S2), set(S2)} = SM, #sum{WGHT1: assigned_to(_,WGHT1,S1), set(S1)} = SM1, SM < SM1, S1 = 1, S2 = 2.''')

    def test_nursescheduling(self):
        self.check_input_to_output('''A shift is identified by an id, and has a number, and hour.
numberOfNurses is a constant.
A nurse goes from 1 to numberOfNurses.
A day goes from 1 to 365.
maxNurseMorning is a constant.
maxNurseAfternoon is a constant.
maxNurseNight is a constant.
minNurseMorning is a constant.
minNurseAfternoon is a constant.
minNurseNight is a constant.
maxHours is a constant equal to 1692.
minHours is a constant equal to 1687.
maxDay is a constant equal to 82.
maxNight is a constant equal to 61.
minDay is a constant equal to 74.
minNight is a constant equal to 58.
balanceNurseDay is a constant equal to 78.
balanceNurseAfternoon is a constant equal to 78.
balanceNurseNight is a constant equal to 60.
Every nurse can work in exactly 1 shift for each day.
It is required that the number of nurses that work in shift S, and day D is at most M, whenever there is a day D, where S is one of morning, afternoon, night and M is respectively one of maxNurseMorning, maxNurseAfternoon, maxNurseNight.
It is prohibited that the number of nurses that work in shift S, and day D is less than M, where S is one of morning, afternoon, night and M is respectively one of minNurseMorning, minNurseAfternoon, minNurseNight.
It is prohibited that the total of hour, in a day, where a nurse works in shift S is more than maxHours.
It is prohibited that the total of hour, in a day, where a nurse works in shift S is less than minHours.
It is prohibited that the number of days with shift equal to vacation where a nurse works in is different from 30.
It is prohibited that a nurse N works with day D in shift with id S1, with number N1, when nurse N works with day D+1 in shift with id S2, with number N2 less than N1, whenever there is a shift with id X, with number equal to morning, whenever there is a shift with id Y, with number equal to night, where S1 is between X and Y.
It is required that the number of days D where a nurse works in a shift with id equal to rest is at least 2, whenever there is a day D2 where D is between D2 and D2+13 and D2 is less than 353.
It is required that a nurse N works in a day D, shift specrest, whenever we have that the number of days D1 where a nurse N works in shift night is equal to 2, whenever there is a day D, where D1 is between D-2 and D-1.
It is prohibited that a nurse N works in a day D, shift specrest, whenever we have that the number of days D1 where a nurse N works in shift night is different from 2, whenever there is a day D, where D1 is between D-2 and D-1.
It is prohibited that the number of days where a nurse works in shift S is more than M, where S is one of morning, afternoon, night and M is respectively one of maxDay, maxDay, maxNight.
It is prohibited that the number of days where a nurse works in shift S is less than M, where S is one of morning, afternoon, night and M is respectively one of minDay, minDay, minNight.
It is preferred, with high priority, that the difference in absolute value between B, and DAYS is minimized, where DAYS is equal to the number of days where a nurse with id N works in a shift and DAYS is between minDay and maxDay and B is one of balanceNurseDay, balanceNurseAfternoon and S is respectively one of morning, afternoon.
It is preferred as much as possible, with high priority, that the difference in absolute value between balanceNurseNight, and DAYS is minimized, where DAYS is equal to the number of days where a nurse with id N works in shift with id equal to night and DAYS is between minNight and maxNight.''', '''#const maxHours = 1692.
#const minHours = 1687.
#const maxDay = 82.
#const maxNight = 61.
#const minDay = 74.
#const minNight = 58.
#const balanceNurseDay = 78.
#const balanceNurseAfternoon = 78.
#const balanceNurseNight = 60.
nurse(1..numberOfNurses).
day(1..365).
1 <= {work_in(DY_D,NRS_D,SHFT_D): shift(SHFT_D,_,_)} <= 1 :- day(DY_D), nurse(NRS_D).
:- #count{D1: work_in(D,D1,S), shift(S,_,_), day(D)} <= M, day(D), S = "morning", M = maxNurseMorning.
:- #count{D1: work_in(D,D1,S), shift(S,_,_), day(D)} <= M, day(D), S = "afternoon", M = maxNurseAfternoon.
:- #count{D1: work_in(D,D1,S), shift(S,_,_), day(D)} <= M, day(D), S = "night", M = maxNurseNight.
:- #count{D1: work_in(D,D1,S), shift(S,_,_), day(D)} < M, S = "morning", M = minNurseMorning.
:- #count{D1: work_in(D,D1,S), shift(S,_,_), day(D)} < M, S = "afternoon", M = minNurseAfternoon.
:- #count{D1: work_in(D,D1,S), shift(S,_,_), day(D)} < M, S = "night", M = minNurseNight.
:- nurse(WRK_N_D), #sum{HR,D: work_in(D,WRK_N_D,S), shift(S,_,HR)} > maxHours.
:- nurse(WRK_N_D), #sum{HR,D: work_in(D,WRK_N_D,S), shift(S,_,HR)} < minHours.
:- nurse(WRK_N_D), #count{D: work_in(D,WRK_N_D,"vacation")} != 30.
:- work_in(D,N,S1), shift(S1,N1,_), nurse(N), work_in(D+1,N,S2), shift(S2,N2,_), shift(X,"morning",_), shift(Y,"night",_), X <= S1, S1 <= Y, N2 < N1.
:- nurse(WRK_N_D), #count{D: work_in(D,WRK_N_D,"rest"), shift("rest",_,_), D2 <= D, D <= D2+13} < 2, day(D2), D2 < 353.
:- not work_in(D,N,"specrest"), shift("specrest",_,_), nurse(N), #count{D1: work_in(D1,N,"night"), shift("night",_,_), D-2 <= D1, D1 <= D-1} = 2, day(D).
:- work_in(D,N,"specrest"), shift("specrest",_,_), nurse(N), #count{D1: work_in(D1,N,"night"), shift("night",_,_), D-2 <= D1, D1 <= D-1} != 2, day(D).
:- nurse(WRK_N_D), #count{D: work_in(D,WRK_N_D,S), shift(S,_,_)} > M, S = "morning", M = maxDay.
:- nurse(WRK_N_D), #count{D: work_in(D,WRK_N_D,S), shift(S,_,_)} > M, S = "afternoon", M = maxDay.
:- nurse(WRK_N_D), #count{D: work_in(D,WRK_N_D,S), shift(S,_,_)} > M, S = "night", M = maxNight.
:- nurse(WRK_N_D), #count{D: work_in(D,WRK_N_D,S), shift(S,_,_)} < M, S = "morning", M = minDay.
:- nurse(WRK_N_D), #count{D: work_in(D,WRK_N_D,S), shift(S,_,_)} < M, S = "afternoon", M = minDay.
:- nurse(WRK_N_D), #count{D: work_in(D,WRK_N_D,S), shift(S,_,_)} < M, S = "night", M = minNight.
:~ nurse(N), DAYS = #count{D: work_in(D,N,WRK_N_D1), shift(WRK_N_D1,_,_)}, minDay <= DAYS, DAYS <= maxDay, ((B - DAYS)) = BSLT_VL, B = balanceNurseDay, S = "morning". [BSLT_VL@3,N]
:~ nurse(N), DAYS = #count{D: work_in(D,N,WRK_N_D1), shift(WRK_N_D1,_,_)}, minDay <= DAYS, DAYS <= maxDay, ((B - DAYS)) = BSLT_VL, B = balanceNurseAfternoon, S = "afternoon". [BSLT_VL@3,N]
:~ nurse(N), DAYS = #count{D: work_in(D,N,"night"), shift("night",_,_)}, minNight <= DAYS, DAYS <= maxNight, ((balanceNurseNight - DAYS)) = BSLT_VL. [BSLT_VL@3,N]''')


    def test_gun_1(self):
        self.check_input_to_output('''A gun is identified by a status.
A shooter is identified by an id.

The following propositions apply in the initial state:
There is a gun with status equal to unloaded.

The following propositions always apply:
There is a shooter with id 1.

The following propositions always apply except in the initial state:
Whenever there is a shooter X, then we must have a gun with status equal to shooting, or a gun with status equal to  loading, or a gun with status equal to  waiting.

Whenever there is a gun loading then we must have a gun with status equal to loaded.
Whenever there is not a gun unloaded, whenever there is previously a gun loaded then we must have a gun with status equal to loaded.

Whenever there is a gun shooting, whenever there is previously a gun loaded then we must have a gun with status equal to unloaded.
Whenever there is previously a gun unloaded, whenever there is not a gun loaded then we must have a gun with status equal to unloaded.

It is prohibited that there is a gun loading, whenever there is previously a gun loaded.''', '''\
#program initial.
gun("unloaded").

#program always.
shooter(1).

#program dynamic.
gun("shooting") | gun("loading") | gun("waiting") :- shooter(X).
gun("loaded") :- gun("loading").
gun("loaded") :- not gun("unloaded"), 'gun("loaded").
gun("unloaded") :- gun("shooting"), 'gun("loaded").
gun("unloaded") :- 'gun("unloaded"), not gun("loaded").
:- gun("loading"), 'gun("loaded").''')

    def test_gun_2(self):
        self.check_input_to_output('''\
A gun is identified by a status.
A shooter is identified by an id.

The following propositions apply in the initial state:
There is a gun with status equal to unloaded.

The following propositions always apply:
There is a shooter with id 1.

The following propositions always apply except in the initial state:
Whenever there is a shooter X, then we must have a gun with status equal to shooting, or a gun with status equal to  loading, or a gun with status equal to waiting.

Whenever there is a gun loading then we must have a gun with status equal to loaded.
Whenever there is not a gun unloaded, whenever there is previously a gun loaded then we must have a gun with status equal to loaded.

Whenever there is a gun shooting, whenever there is previously a gun loaded, whenever there is not a gun broken, then we must have a gun with status equal to unloaded.
Whenever there is previously a gun unloaded, whenever there is not a gun loaded then we must have a gun with status equal to unloaded.

It is prohibited that there is a gun loading, whenever there is previously a gun loaded.

//Whenever there is a gun shooting, whenever before there is always a gun unloaded and from before there is eventually a gun shooting, then we must have a gun with status equal to broken.
Whenever there is a gun shooting, whenever there is before a gun unloaded that always holds and there is eventually a gun shooting that holds since before, then we must have a gun with status equal to broken.

Whenever there is previously a gun broken, then we must have a gun with status equal to broken.

The following propositions apply in the final state:
It is prohibited that, before here, there are not a gun loaded and a gun shooting that eventually hold.
''', '''\
#program initial.
gun("unloaded").

#program always.
shooter(1).

#program dynamic.
gun("shooting") | gun("loading") | gun("waiting") :- shooter(X).
gun("loaded") :- gun("loading").
gun("loaded") :- not gun("unloaded"), 'gun("loaded").
gun("unloaded") :- gun("shooting"), 'gun("loaded"), not gun("broken").
gun("unloaded") :- 'gun("unloaded"), not gun("loaded").
:- gun("loading"), 'gun("loaded").
gun("broken") :- gun("shooting"),not not &tel {(<* gun("unloaded")) & (< <? gun("shooting"))}.
gun("broken") :- 'gun("broken").

#program final.
:- not &tel {<? (gun("loaded") & gun("shooting"))}.''')

    def test_hanoi(self):
        self.check_input_to_output('''\
A disk is identified by an id.
A peg is identified by an id.
A goal is identified by a disk, and by a peg.


The following propositions always apply:
There is a disk with id 0.
There is a disk with id 1.
There is a disk with id 2.
There is a disk with id 3.

There is a peg with id 1.
There is a peg with id 2.
There is a peg with id 3.

There is a goal with disk id 3, with peg 3.
There is a goal with disk id 2, with peg 3.
There is a goal with disk id 1, with peg 3.

The following propositions apply in the initial state:
Every disk X must be on peg 1, where X is greater than 0.

The following propositions always apply except in the initial state:
Whenever there is a disk D, then D can be moved to a peg.
It is required that the number of disks that are moved to a peg is equal to 1.

A disk D is on a peg P when disk D is moved to peg P.
A disk D is moved when disk D is moved to a peg P.
A disk D is on a peg P when disk D is previously on peg P and also disk D is not moved.

A disk X is blocked in peg P when disk D is previously on peg P, where X is equal to D-1.
A disk X is blocked in peg P when disk D is blocked in peg P, where X is equal to D-1.

It is prohibited that a disk D is moved to a peg P, when a disk X is blocked in peg P, where X is equal to D-1.
It is prohibited that a disk D is moved to a peg P1, when disk D is previously on peg P2 and also disk D is blocked in peg P2.
//It is prohibited that the number of peg P where a disk D is on is different from 1, whenever there is a disk with id D greater than 0.

The following propositions apply in the final state:
It is prohibited that disk D is not on peg P, whenever there is a goal with disk id D, with peg id P.
''', '''\
#program always.
disk(0).
disk(1).
disk(2).
disk(3).
peg(1).
peg(2).
peg(3).
goal(3,3).
goal(2,3).
goal(1,3).

#program initial.
on(X,1): peg(1) :- X > 0, disk(X).

#program dynamic.
{moved_to(D,PG_D): peg(PG_D)} :- disk(D).
:- #count{D: moved_to(D,MVD_T_D), peg(MVD_T_D)} != 1.
on(D,P) :- disk(D), moved_to(D,P), peg(P).
moved(D) :- disk(D), moved_to(D,P), peg(P).
on(D,P) :- 'on(D,P), peg(P), disk(D), not moved(D).
blocked_in(X,P) :- disk(X), disk(D), 'on(D,P), peg(P), X = D-1.
blocked_in(X,P) :- disk(X), disk(D), blocked_in(D,P), peg(P), X = D-1.
:- disk(D), moved_to(D,P), disk(X), blocked_in(X,P), peg(P), X = D-1.
:- moved_to(D,P1), peg(P1), 'on(D,P2), disk(D), blocked_in(D,P2), peg(P2).

#program final.
:- disk(D), not on(D,P), peg(P), goal(D,P).''')

    def test_logistic(self):
        self.check_input_to_output('''\
An object is identified by an id.
A vehicle is identified by a object.
A truck is identified by a object.
An airplane is identified by a object.
A package is identified by an id.
A location is identified by an id.
A city is identified by a location, and by a name.
An airport is identified by a location.
A goal is identified by a package, and by a location.

The following propositions always apply:
A truck T is a vehicle.
An airplane A is a vehicle.
Whenever there is a city with location L, then we must have a location with id L.

The following propositions always apply except in the initial state:

Every vehicle V can load at most 1 package P, when package with id P is previously deposited in location L and also vehicle V is previously at location L
    and also package with id P is not previously loaded.
Every vehicle V can unload a package P, when a package with id P is previously loaded in vehicle V.


A package P is loaded in vehicle V, when package P is previously loaded in vehicle V and also vehicle V does not unload package P.
A package P is loaded, when package P is loaded in a vehicle V.
A package P is loaded in vehicle V, when a vehicle V loads package P.
It is prohibited that a vehicle V1 loads a package P and also vehicle V2 loads package P, where V1 is different from V2.

A vehicle V has a cargo when vehicle V load package P.
A vehicle V has a cargo when vehicle V unload package P.

Every airplane A can move to at most 1 airport with location L different from M, when airplane A is previously at location M.
Every truck T can move to at most 1 city with location L different from M, with name C, when truck T is previously at location M, whenever there is a city with location M, with name C.

It is prohibited that a vehicle V moves to a location L whenever there is a cargo with vehicle V.

A vehicle V is moving, when vehicle V moves to a location.
A package P is deposited in location L, when package P is loaded in vehicle V and also vehicle V is at location L.
A vehicle V is at location L, when vehicle V moves to location L.

A truck T is at location L when truck T is previously at location L and also truck T is not moving.
An airplane A is at location L when airplane A is previously at location L and also airplane A is not moving.
A package P is deposited in location L when package P is previously deposited in location L and also package P is not loaded.

It is prohibited that a vehicle with object id V is moving, whenever there is not after a cargo V.

The following propositions apply in the final state:
It is prohibited that package P is not deposited in location L, whenever there is a goal with package P, and with location L.
It is prohibited that package P is loaded, whenever there is a goal with package P.''', '''\
#program always.
vehicle(T) :- truck(T).
vehicle(A) :- airplane(A).
location(L) :- city(L,_).

#program dynamic.
{load(V,P)} <= 1 :- 'deposited_in(P,L), 'at(V,L), location(L), package(P), not 'loaded(P), vehicle(V).
{unload(V,P)} :- package(P), 'loaded_in(P,V), vehicle(V).
loaded_in(P,V) :- 'loaded_in(P,V), vehicle(V), not unload(V,P), package(P).
loaded(P) :- package(P), loaded_in(P,V), vehicle(V).
loaded_in(P,V) :- vehicle(V), load(V,P), package(P).
:- vehicle(V1), load(V1,P), vehicle(V2), load(V2,P), package(P), V1 != V2.
cargo(V) :- vehicle(V), load(V,P), package(P).
cargo(V) :- vehicle(V), unload(V,P), package(P).
{move_to(A,L): airport(L), L != M} <= 1 :- 'at(A,M), location(M), airplane(A).
{move_to(T,L): city(L,C), L != M} <= 1 :- 'at(T,M), location(M), city(M,C), truck(T).
:- vehicle(V), move_to(V,L), location(L), cargo(V).
moving(V) :- vehicle(V), move_to(V,LCTN_D), location(LCTN_D).
deposited_in(P,L) :- package(P), loaded_in(P,V), vehicle(V), at(V,L), location(L).
at(V,L) :- vehicle(V), move_to(V,L), location(L).
at(T,L) :- 'at(T,L), location(L), truck(T), not moving(T).
at(A,L) :- 'at(A,L), location(L), airplane(A), not moving(A).
deposited_in(P,L) :- 'deposited_in(P,L), location(L), package(P), not loaded(P).
:- vehicle(V), moving(V), not &tel {> cargo(V)}.

#program final.
:- package(P), not deposited_in(P,L), location(L), goal(P,L).
:- package(P), loaded(P), goal(P,_).''')

    def test_monkey(self):
        self.check_input_to_output('''\
An agent is identified by a name.
A monkey is identified by an agent.
A box is identified by an agent.
A banana is identified by an agent.

The following propositions always apply:
A location is one of door, window, middle.
There is monkey with agent name 1.
There is box with agent name 2.
There is banana with agent name 3.

The following propositions apply in the initial state:
Monkey M is at location door.
Box B is at location window.

The following propositions always apply except in the initial state:
Whenever there is a monkey M, then M must walk to a location X or push to a location X or climb or grasp.
A monkey M has moved, when monkey M is at location X and also monkey M is previously at location Y, where X is different from Y.
A box B has moved, when box B is at location X and also box B is previously at location Y, where X is different from Y.
Monkey M is at location X when monkey M is previously at location X and also monkey M has not moved.
Box B is at location X when box B is previously at location X and also box B has not moved.
Monkey M is on box B when monkey M is previously on box B.
A monkey M is at a location X when monkey M walks to location X.
It is prohibited that a monkey M walks to location X when monkey M is previously at a location X.
It is prohibited that a monkey M walks to location X when monkey M is previously on a box B.
It is prohibited that a monkey M push to location X when monkey M is previously on a box B.
It is prohibited that a monkey M push to location X when monkey M is previously at location X.
It is prohibited that a monkey M push to location X, a box B when monkey M is previously at location Y and also box B is previously at location Z, where Y is different from Z.
Monkey M gets a banana B when monkey M grasps.
It is prohibited that monkey M grasp a banana BA when monkey M is not previously on box BO.
It is prohibited that monkey M grasps banana B when monkey M is previously at location X, where X is different from middle.
Monkey M is on box B when monkey M climb box B.
It is prohibited that monkey M climb box B when monkey M is previously on box B.
It is prohibited that monkey M climbs box B when monkey M is at location X and also box B is at location Y, where X is different from Y.
A monkey M is at location X when monkey M push to location X.
A box B is at location X when monkey M push to location X, box B.

The following propositions apply in the final state:
It is required that monkey M gets banana B.
''', '''\
#program always.
location("door").
location("window").
location("middle").
monkey(1).
box(2).
banana(3).

#program initial.
at(M,"door") :- monkey(M), location("door").
at(B,"window") :- box(B), location("window").

#program dynamic.
walk_to(M,X): location(X) | push_to(M,X): location(X) | climb(M) | grasp(M) :- monkey(M).
moved(M) :- at(M,X), location(X), monkey(M), 'at(M,Y), location(Y), X != Y.
moved(B) :- at(B,X), location(X), box(B), 'at(B,Y), location(Y), X != Y.
at(M,X) :- 'at(M,X), location(X), monkey(M), not moved(M).
at(B,X) :- 'at(B,X), location(X), box(B), not moved(B).
on(M,B) :- monkey(M), 'on(M,B), box(B).
at(M,X) :- monkey(M), walk_to(M,X), location(X).
:- walk_to(M,X), monkey(M), 'at(M,X), location(X).
:- walk_to(M,X), location(X), monkey(M), 'on(M,B), box(B).
:- push_to(M,X), location(X), monkey(M), 'on(M,B), box(B).
:- push_to(M,X), monkey(M), 'at(M,X), location(X).
:- push_to(M,X), location(X), monkey(M), 'at(M,Y), location(Y), box(B), 'at(B,Z), location(Z), Y != Z.
get(M,B) :- banana(B), monkey(M), grasp(M).
:- grasp(M), banana(BA), monkey(M), not 'on(M,BO), box(BO).
:- grasp(M), banana(B), monkey(M), 'at(M,X), location(X), X != "middle".
on(M,B) :- monkey(M), climb(M), box(B).
:- climb(M), monkey(M), 'on(M,B), box(B).
:- climb(M), monkey(M), at(M,X), location(X), box(B), at(B,Y), location(Y), X != Y.
at(M,X) :- monkey(M), push_to(M,X), location(X).
at(B,X) :- monkey(M), push_to(M,X), location(X), box(B).

#program final.
:- monkey(M), not get(M,B), banana(B).''')

    def test_moore(self):
        self.check_input_to_output('''\
A variable is identified by an id.
A process is identified by a variable.
A value is identified by a number.
An instruction is identified by a value.
target is a constant.

The following propositions always apply:
A process goes from 1 to 2.
There is a variable r1. // corresponding to process 1 register
There is a variable r2. // corresponding to process 2 register
There is a variable c.
An instruction goes from 0 to 2.
A value goes from 0 to target.

The following propositions apply in the initial state:
Process P holds instruction 0.
Variable c holds value 1.
Variable a holds instruction 0.
Variable b holds instruction 0.

The following propositions always apply except in the initial state:
Every process can fetch at most 1 instruction.
It is prohibited that a process P1 fetch an instruction I1, when process P2 fetch, where P1 is different from P2 and I1 is less than 2.
It is prohibited that the number of process variable P that fetch an instruction I is equal to 0.

Process P changes instruction with value equal to (I+1)\\3, when process P fetch instruction X and also process P previously holds instruction I.

Variable V changes value with number equal to C, when process P fetch instruction I and also process P previously holds instruction with value 0 and also variable c previously holds value C, where P is equal to 1 and V is equal to r1.
Variable V changes value with number equal to C, when process P fetch instruction I and also process P previously holds instruction with value 0 and also variable c previously holds value C, where P is equal to 2 and V is equal to r2.

Variable V changes value with number equal to R+C, when process P fetch instruction I and also process P previously holds instruction with value 1 and also variable c previously holds value C and also variable V previously holds value R, where P is equal to 1 and V is equal to r1 where R+C is less than or equal to target.
Variable V changes value with number equal to R+C, when process P fetch instruction I and also process P previously holds instruction with value 1 and also variable c previously holds value C and also variable V previously holds value R, where P is equal to 2 and V is equal to r2 where R+C is less than or equal to target.

Variable c changes value with number equal to R, when process P fetch instruction I and also process P previously holds instruction with value 2 and also variable r1 previously holds value R, where P is equal to 1.
Variable c changes value with number equal to R, when process P fetch instruction I and also process P previously holds instruction with value 2 and also variable r2 previously holds value R, where P is equal to 2.

A variable K holds a value V, when a variable K changes value V.
A process K holds a value V, when a process K changes value V.
A variable K holds a value V, when a variable K previously holds a value V and also variable K does not change.
A process K holds a value V, when a process K previously holds a value V and also variable K does not change.

The following propositions apply in the final state:
It is required that variable c holds value target.''', '''\
#program always.
process(1..2).
variable("r1").
variable("r2").
variable("c").
instruction(0..2).
value(0..target).

#program initial.
hold(P,0) :- process(P), instruction(0).
hold("c",1) :- variable("c"), value(1).
hold("a",0) :- variable("a"), instruction(0).
hold("b",0) :- variable("b"), instruction(0).

#program dynamic.
{fetch(PRCSS_D,NSTRCTN_NMBR): instruction(NSTRCTN_NMBR)} <= 1 :- process(PRCSS_D).
:- process(P1), fetch(P1,I1), instruction(I1), process(P2), fetch(P2,_), P1 != P2, I1 < 2.
:- #count{P: fetch(P,I), instruction(I)} = 0.
change(P,(I+1)\\3) :- instruction((I+1)\\3), fetch(P,X), instruction(X), process(P), 'hold(P,I), instruction(I).
change(V,C) :- variable(V), fetch(P,I), instruction(I), process(P), 'hold(P,0), instruction(0), variable("c"), 'hold("c",C), value(C), P = 1, V = "r1".
change(V,C) :- variable(V), fetch(P,I), instruction(I), process(P), 'hold(P,0), instruction(0), variable("c"), 'hold("c",C), value(C), P = 2, V = "r2".
change(V,R+C) :- value(R+C), fetch(P,I), instruction(I), process(P), 'hold(P,1), instruction(1), variable("c"), 'hold("c",C), value(C), variable(V), 'hold(V,R), value(R), P = 1, V = "r1", R+C <= target.
change(V,R+C) :- value(R+C), fetch(P,I), instruction(I), process(P), 'hold(P,1), instruction(1), variable("c"), 'hold("c",C), value(C), variable(V), 'hold(V,R), value(R), P = 2, V = "r2", R+C <= target.
change("c",R) :- variable("c"), fetch(P,I), instruction(I), process(P), 'hold(P,2), instruction(2), variable("r1"), 'hold("r1",R), value(R), P = 1.
change("c",R) :- variable("c"), fetch(P,I), instruction(I), process(P), 'hold(P,2), instruction(2), variable("r2"), 'hold("r2",R), value(R), P = 2.
hold(K,V) :- variable(K), change(K,V), value(V).
hold(K,V) :- process(K), change(K,V), value(V).
hold(K,V) :- 'hold(K,V), value(V), variable(K), not change(K,_).
hold(K,V) :- 'hold(K,V), value(V), process(K), not change(K,_).

#program final.
:- variable("c"), not hold("c",target), value(target).''')

    def test_river(self):
        self.check_input_to_output('''A location is identified by a name.
An item is identified by an id.
A farmer is identified by an item.
A route is identified by a starting location, and by an arriving location.

The following propositions always apply:
An item is one of fox, beans, goose.
There is a farmer with item id 1.
There is a location left_bank.
There is a location right_bank.
There is a route with starting location equal to left_bank, with arriving location equal to right_bank.
There is a route with starting location equal to right_bank, with arriving location equal to left_bank.
Item fox eats item goose.
Item goose eats item beans.

The following propositions apply in the initial state:
Item fox is at location left_bank.
Item goose is at location left_bank.
Item beans are at location left_bank.
Farmer F is at location left_bank.

The following propositions always apply except in the initial state:
Every item I can be moved.
It is prohibited that the number of items that are moved is greater than 1.

Item X is at location B, when item X is previously at location A and also item X is moved, whenever there is a route with starting location A, with arriving location B.
Item X is at location A, when item X is previously at location A and also item X is not moved.
Farmer F is at location B, when farmer F is previously at location A, whenever there is a route with starting location A, with arriving location B.
It is prohibited that item X is moved, when farmer F is previously at location A and also item X is not previously at location A.

The following propositions always apply:
It is prohibited that item X is at location A and also item X is at location B, where A is different from B.

It is prohibited that item X is at location A and also item Y is at location A, when item X eats item Y and also farmer F is not at location A.

The following propositions apply in the final state:
It is required that item X is at location right_bank.''', '''\
#program always.
item("fox").
item("beans").
item("goose").
farmer(1).
location("left_bank").
location("right_bank").
route("left_bank","right_bank").
route("right_bank","left_bank").
eat("fox","goose") :- item("fox"), item("goose").
eat("goose","beans") :- item("goose"), item("beans").

#program initial.
at("fox","left_bank") :- item("fox"), location("left_bank").
at("goose","left_bank") :- item("goose"), location("left_bank").
at("beans","left_bank") :- item("beans"), location("left_bank").
at(F,"left_bank") :- farmer(F), location("left_bank").

#program dynamic.
{moved(I)} :- item(I).
:- #count{D: moved(D)} > 1.
at(X,B) :- location(B), 'at(X,A), location(A), item(X), moved(X), route(A,B).
at(X,A) :- 'at(X,A), location(A), item(X), not moved(X).
at(F,B) :- location(B), farmer(F), 'at(F,A), location(A), route(A,B).
:- moved(X), farmer(F), 'at(F,A), item(X), not 'at(X,A), location(A).

#program always.
:- at(X,A), location(A), item(X), at(X,B), location(B), A != B.
:- at(X,A), at(Y,A), item(X), eat(X,Y), item(Y), farmer(F), not at(F,A), location(A).

#program final.
:- item(X), not at(X,"right_bank"), location("right_bank").''')

    def test_queen(self):
        self.check_input_to_output('''Row goes from 1 to 8.
Column goes from 1 to 8.

Queen goes from 1 to 8.

Every queen can be assigned_row exactly 1 row.
Every queen can be assigned_column exactly 1 column.

Queen Q1 is sharing_row with queen Q2 when
    queen Q1 is assigned_row row R1 and also
    queen Q2 is assigned_row row R2.

Whenever there is a sharing_row with queen Q1, with queen Q2, then we can have a queen.''', '''\
row(1..8).
column(1..8).
queen(1..8).
1 <= {assigned_row(QN_D,RW_D): row(RW_D)} <= 1 :- queen(QN_D).
1 <= {assigned_column(QN_D,CLMN_D): column(CLMN_D)} <= 1 :- queen(QN_D).
sharing_row(Q2,Q1) :- queen(Q1), assigned_row(Q1,R1), row(R1), queen(Q2), assigned_row(Q2,R2), row(R2).
{queen(Q1)} :- sharing_row(Q1,Q2).''')

    def test_cell_and_rows(self):
        self.check_input_to_output('''A row is identified by an id.
A column is identified by an id.
A cell is identified by a column, and by a row.
A value is identified by a number.

Every cell can be assigned to exactly 1 value.
A row R has_duplicates whenever we have that the number of row id R that are assigned to value V is greater than 1.''',
                                '''\
1 <= {assigned_to(CLL_D,CLL_D1,VL_NMBR): value(VL_NMBR)} <= 1 :- cell(CLL_D,CLL_D1).
has_duplicate(R) :- row(R), #count{R: assigned_to(_,R,V), value(V)} > 1.''')
