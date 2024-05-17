#program always.
location("door").
location("window").
location("middle").
monkey(1).
box(2).
banana(3).

#program initial.
at("door",M) :- monkey(M), location("door").
at("window",B) :- box(B), location("window").

#program dynamic.
walk_to(X,M): location(X) ; push_to(X,M): location(X) ; climb(M) ; grasp(M) :- monkey(M).
moved(M) :- at(X,M), location(X), 'at(Y,M), location(Y), X != Y, monkey(M).
moved(B) :- at(X,B), location(X), 'at(Y,B), location(Y), X != Y, box(B).
at(X,M) :- 'at(X,M), not moved(M), monkey(M), location(X).
at(X,B) :- 'at(X,B), not moved(B), box(B), location(X).
on(M,B) :- 'on(M,B), monkey(M), box(B).
at(X,M) :- walk_to(X,M), monkey(M), location(X).
:- walk_to(X,M), monkey(M), 'at(X,M), location(X).
:- walk_to(X,M), location(X), monkey(M), 'on(M,B), box(B).
:- push_to(X,M), location(X), monkey(M), 'on(M,B), box(B).
:- push_to(X,M), monkey(M), 'at(X,M), location(X).
:- push_to(X,M), location(X), monkey(M), 'at(Y,M), location(Y), box(B), 'at(Z,B), location(Z), Y != Z.
get(M,B) :- grasp(M), monkey(M), banana(B).
:- grasp(M), banana(BA), monkey(M), not 'on(M,BO), box(BO).
:- grasp(M), banana(B), monkey(M), 'at(X,M), location(X), X != "middle".
on(M,B) :- climb(M), monkey(M), box(B).
:- climb(M), monkey(M), 'on(M,B), box(B).
:- climb(M), monkey(M), at(X,M), location(X), box(B), at(Y,B), location(Y), X != Y.
at(X,M) :- push_to(X,M), monkey(M), location(X).
at(X,B) :- monkey(M), push_to(X,M), box(B), location(X).

#program final.
:- monkey(M), not get(M,B), banana(B).