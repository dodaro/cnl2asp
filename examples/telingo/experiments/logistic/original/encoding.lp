city(1..n+1).
#program initial.

% Each city has a central, an airport, a post office and a truck initially there

in_city((central(C);airport(C);po(C)),C):- city(C).
truck(truck(C)) :- city(C).
at(truck(C),po(C)) :- city(C).

airport(airport(C)) :- city(C).

package(1..n).
at(P,po(1)) :- package(P).

airplane(plane1;plane2).
at((plane1;plane2),airport(1)).

goal_at(X,po(X+1)) :- package(X).

#show load/2.
#show unload/2.
#show move/2.
#program initial.

vehicle(A) :- airplane(A).
vehicle(T) :- truck(T).
location(L) :- in_city(L,_).

#program dynamic.

% Inertia for "at" with trucks (they cannot be outside their city)
at(T,L) :- 'at(T,L), not -at(T,L), _truck(T).
-at(T,L) :- at(T,M), _in_city(M,C), _in_city(L,C), L!=M, _truck(T).

% Inertia for at with airplanes (they are only in airports)
at(A,L) :- 'at(A,L), not -at(A,L), _airplane(A).
-at(A,L) :- at(A,M), _airport(L), L!=M, _airplane(A).

% Inertia for packages
at(P,L) :- 'at(P,L), not -at(P,L), _package(P).
-at(P,L) :- at(P,M), _location(L), L!=M, _package(P).

%%%%%%%%%%% Loading objects

{ load(P,V) } :- _package(P), 'at(P,L), _vehicle(V), 'at(V,L), not 'in(P,V), not 'loaded(P).
:- { load(P,V) } > 1, _package(P).

in(P,V) :- load(P,V).
loaded(P) :- in(P,V).

%%%%%%%%%%% Unloading objects

{ unload(P,V) } :- _package(P), 'in(P,V).

% Frame axiom for "in"
in(P,V) :- 'in(P,V), not unload(P,V).

%%%%%%%%%%% Moving vehicles

{ move(T,L) } :- _truck(T), 'at(T,M), _in_city(M,C), _in_city(L,C), L!=M.
{ move(A,L) } :- _airplane(A), 'at(A,M), _airport(L), L!=M.
:- { move(V,L) } > 1, _vehicle(V).

cargo(V) :- load(P,V).
cargo(V) :- unload(P,V).
:- move(V,L), cargo(V).

at(V,L) :- move(V,L).
moved(V) :- move(V,_).

#program always.

at(P,L) :- in(P,V), at(V,L).

% Control rule: if we move a vehicle, it keeps unmoved until some cargo is done
:- _vehicle(V), moved(V), not &tel{ > (~moved(V) >? cargo(V)) }.

#program final.
:- _goal_at(P,L), not at(P,L), not _testing.
:- _goal_at(P,L), loaded(P),   not _testing.

#defined load/3.
#defined move/3.
#defined unload/3.