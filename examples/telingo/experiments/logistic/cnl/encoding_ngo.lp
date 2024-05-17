#program always.
truck(truck(C)) :- city(C).
airplane(plane1;plane2).
airport(airport(C)) :- city(C).
city((central(C);airport(C);po(C)),C):- city(C).


package(1..n).
city(1..n+1).
goal(X,po(X+1)) :- package(X).

#program initial.
% Each city has a central, an airport, a post office and a truck initially there
deposited_in(P,po(1)) :- package(P).
at((plane1;plane2),airport(1)).
at(truck(C),po(C)) :- city(C).

#show load/2.
#show unload/2.
#show move_to/2.

#program base.
#program always.
vehicle(T) :- truck(T).
vehicle(A) :- airplane(A).
location(L) :- city(L,_).
#program dynamic.
1 >= { load(V,P) } :- 'deposited_in(P,L); 'at(V,L); location(L); package(P); not 'loaded(P); vehicle(V).
{ unload(V,P) } :- package(P); 'loaded_in(P,V); vehicle(V).
loaded_in(P,V) :- 'loaded_in(P,V); not unload(V,P); package(P); vehicle(V).
loaded(P) :- loaded_in(P,_).
loaded_in(P,V) :- load(V,P).
__dom_load(P) :- 'deposited_in(P,L); 'at(V,L); location(L); package(P); not 'loaded(P); vehicle(V).
#false :- __dom_load(P); 2 <= #count { V1: load(V1,P) }.
cargo(V) :- load(V,_).
cargo(V) :- unload(V,_).
1 >= { move_to(A,L): airport(L), L != M } :- 'at(A,M); location(M); airplane(A).
1 >= { move_to(T,L): city(L,C), L != M } :- 'at(T,M); location(M); city(M,C); truck(T).
#false :- move_to(V,L); location(L); cargo(V).
moving(V) :- move_to(V,LCTN_D); location(LCTN_D); vehicle(V).
deposited_in(P,L) :- loaded_in(P,V); at(V,L).
at(V,L) :- move_to(V,L); vehicle(V); location(L).
at(T,L) :- 'at(T,L); not moving(T); truck(T); location(L).
at(A,L) :- 'at(A,L); not moving(A); airplane(A); location(L).
deposited_in(P,L) :- 'deposited_in(P,L); not loaded(P); package(P); location(L).
#false :- moving(V); not &tel { (> cargo(V)) }.
#program final.
#false :- package(P); not deposited_in(P,L); location(L); goal(P,L).
#false :- loaded(P); goal(P,_).
