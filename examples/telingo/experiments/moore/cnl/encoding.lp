#program always.
process(1..2).
variable("r1").
variable("r2").
variable("c").
instruction(0..2).
value(0..n).

#program initial.
hold(P,0) :- process(P), instruction(0).
hold("c",1) :- variable("c"), value(1).
hold("a",0) :- variable("a"), instruction(0).
hold("b",0) :- variable("b"), instruction(0).

#program dynamic.
{fetch(PRCSS_D,NSTRCTN_NMBR): instruction(NSTRCTN_NMBR)} <= 1 :- process(PRCSS_D).
:- process(P1), fetch(P1,I1), instruction(I1), process(P2), fetch(P2,_), P1 != P2, I1 < 2.
:- #count{P: fetch(P,I), instruction(I)} = 0.
change(P,(I+1)\3) :- fetch(P,X), instruction(X), 'hold(P,I), instruction(I), process(P), instruction((I+1)\3).
change(V,C) :- fetch(P,I), instruction(I), process(P), 'hold(P,0), instruction(0), variable("c"), 'hold("c",C), P = 1, V = "r1", variable(V), value(C).
change(V,C) :- fetch(P,I), instruction(I), process(P), 'hold(P,0), instruction(0), variable("c"), 'hold("c",C), P = 2, V = "r2", variable(V), value(C).
change(V,R+C) :- fetch(P,I), instruction(I), process(P), 'hold(P,1), instruction(1), variable("c"), 'hold("c",C), value(C), 'hold(V,R), value(R), P = 1, V = "r1", R+C <= n, variable(V), value(R+C).
change(V,R+C) :- fetch(P,I), instruction(I), process(P), 'hold(P,1), instruction(1), variable("c"), 'hold("c",C), value(C), 'hold(V,R), value(R), P = 2, V = "r2", R+C <= n, variable(V), value(R+C).
change("c",R) :- fetch(P,I), instruction(I), process(P), 'hold(P,2), instruction(2), variable("r1"), 'hold("r1",R), P = 1, variable("c"), value(R).
change("c",R) :- fetch(P,I), instruction(I), process(P), 'hold(P,2), instruction(2), variable("r2"), 'hold("r2",R), P = 2, variable("c"), value(R).
hold(K,V) :- change(K,V), variable(K), value(V).
hold(K,V) :- change(K,V), process(K), value(V).
hold(K,V) :- 'hold(K,V), not change(K,_), variable(K), value(V).
hold(K,V) :- 'hold(K,V), not change(K,_), process(K), value(V).

#program final.
:- variable("c"), not hold("c",n), value(n).
