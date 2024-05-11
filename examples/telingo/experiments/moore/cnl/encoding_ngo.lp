#program base.
#program always.
process((1..2)).
variable("r1").
variable("r2").
variable("c").
instruction((0..2)).
value((0..n)).
#program initial.
hold(P,0) :- process(P); instruction(0).
hold("c",1) :- variable("c"); value(1).
hold("a",0) :- variable("a"); instruction(0).
hold("b",0) :- variable("b"); instruction(0).
#program dynamic.
1 >= { fetch(PRCSS_D,NSTRCTN_NMBR): instruction(NSTRCTN_NMBR) } :- process(PRCSS_D).
#false :- fetch(P1,I1); fetch(P2,_); P1 != P2; I1 < 2.
#false :- 0 = #sum+ { 1,P: fetch(P,I) }.
change(P,((I+1)\3)) :- fetch(P,_); 'hold(P,I); instruction(I); instruction(((I+1)\3)).
change("r1",C) :- fetch(1,_); 'hold(1,0); instruction(0); variable("c"); 'hold("c",C); variable("r1"); value(C).
change("r2",C) :- fetch(2,_); 'hold(2,0); instruction(0); variable("c"); 'hold("c",C); variable("r2"); value(C).
change("r1",(R+C)) :- fetch(1,_); 'hold(1,1); instruction(1); variable("c"); 'hold("c",C); value(C); 'hold("r1",R); value(R); (R+C) <= n; variable("r1"); value((R+C)).
change("r2",(R+C)) :- fetch(2,_); 'hold(2,1); instruction(1); variable("c"); 'hold("c",C); value(C); 'hold("r2",R); value(R); (R+C) <= n; variable("r2"); value((R+C)).
change("c",R) :- fetch(1,_); 'hold(1,2); instruction(2); variable("r1"); 'hold("r1",R); variable("c"); value(R).
change("c",R) :- fetch(2,_); 'hold(2,2); instruction(2); variable("r2"); 'hold("r2",R); variable("c"); value(R).
hold(K,V) :- change(K,V); variable(K); value(V).
hold(K,V) :- change(K,V); process(K); value(V).
hold(K,V) :- 'hold(K,V); not change(K,_); variable(K); value(V).
hold(K,V) :- 'hold(K,V); not change(K,_); process(K); value(V).
#program final.
#false :- variable("c"); not hold("c",n); value(n).
