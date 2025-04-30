import unittest

from cnl2asp.cnl2asp import Cnl2asp, MODE
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.specification.signaturemanager import SignatureManager


class TestTheoryExtProblems(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        SignatureManager.signatures = []
        asp_converter: ASPConverter = ASPConverter()
        asp_converter.clear_support_variables()

    def compute_telingo(self, string: str) -> str:
        return Cnl2asp(string, MODE.TELINGO).compile().strip()


    def test_gun_1(self):
        self.assertEqual(self.compute_telingo('''A gun is identified by a status.
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

It is prohibited that there is a gun loading, whenever there is previously a gun loaded.'''), '''\
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
        self.assertEqual(self.compute_telingo('''\
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
'''), '''\
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
        self.assertEqual(self.compute_telingo('''\
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
'''), '''\
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
        self.assertEqual(self.compute_telingo('''\
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
It is prohibited that package P is loaded, whenever there is a goal with package P.'''), '''\
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
        self.assertEqual(self.compute_telingo('''\
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
'''), '''\
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
        self.assertEqual(self.compute_telingo('''\
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
It is required that variable c holds value target.'''), '''\
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
        self.assertEqual(self.compute_telingo('''A location is identified by a name.
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
It is required that item X is at location right_bank.'''), '''\
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
        self.assertEqual(self.compute_telingo('''Row goes from 1 to 8.
Column goes from 1 to 8.

Queen goes from 1 to 8.

Every queen can be assigned_row exactly 1 row.
Every queen can be assigned_column exactly 1 column.

Queen Q1 is sharing_row with queen Q2 when
    queen Q1 is assigned_row row R1 and also
    queen Q2 is assigned_row row R2.

Whenever there is a sharing_row with queen Q1, with queen Q2, then we can have a queen.'''), '''\
row(1..8).
column(1..8).
queen(1..8).
1 <= {assigned_row(QN_D,RW_D): row(RW_D)} <= 1 :- queen(QN_D).
1 <= {assigned_column(QN_D,CLMN_D): column(CLMN_D)} <= 1 :- queen(QN_D).
sharing_row(Q2,Q1) :- queen(Q1), assigned_row(Q1,R1), row(R1), queen(Q2), assigned_row(Q2,R2), row(R2).
{queen(Q1)} :- sharing_row(Q1,Q2).''')

    def test_cell_and_rows(self):
        self.assertEqual(self.compute_telingo('''A row is identified by an id.
A column is identified by an id.
A cell is identified by a column, and by a row.
A value is identified by a number.

Every cell can be assigned to exactly 1 value.
A row R has_duplicates whenever we have that the number of row id R that are assigned to value V is greater than 1.'''),
                         '''\
1 <= {assigned_to(CLL_D,CLL_D1,VL_NMBR): value(VL_NMBR)} <= 1 :- cell(CLL_D,CLL_D1).
has_duplicate(R) :- row(R), #count{R: assigned_to(_,R,V), value(V)} > 1.''')
