#program always.
disk(0..n).
peg(1;2;3).
goal(1..n,3).


#program initial.
on(X,1) :- X > 0; disk(X); peg(1).
#program dynamic.
{ moved_to(D,PG_D): peg(PG_D) } :- disk(D).
#false :- 1 != #sum+ { 1,D: moved_to(D,MVD_T_D) }.
on(D,P) :- moved_to(D,P).
moved(D) :- moved_to(D,_).
on(D,P) :- 'on(D,P); not moved(D); disk(D); peg(P).
blocked_in((D-1),P) :- disk(D); 'on(D,P); disk((D-1)); peg(P).
blocked_in((D-1),P) :- blocked_in(D,P); disk((D-1)).
#false :- moved_to(D,P); blocked_in((D-1),P).
#false :- moved_to(D,_); 'on(D,P2); blocked_in(D,P2).
#false :- 1 != #sum+ { 1,P: on(D,P) }; disk(D); D > 0.
#program final.
#false :- disk(D); not on(D,P); peg(P); goal(D,P).


