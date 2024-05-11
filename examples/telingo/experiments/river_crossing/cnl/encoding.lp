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
at(X,B) :- 'at(X,A), location(A), moved(X), route(A,B), item(X), location(B).
at(X,A) :- 'at(X,A), not moved(X), item(X), location(A).
at(F,B) :- 'at(F,A), location(A), route(A,B), farmer(F), location(B).
:- moved(X), farmer(F), 'at(F,A), item(X), not 'at(X,A), location(A).

#program always.
:- at(X,A), location(A), item(X), at(X,B), location(B), A != B.
:- at(X,A), at(Y,A), item(X), eat(X,Y), item(Y), farmer(F), not at(F,A), location(A).

#program final.
:- item(X), not at(X,"right_bank"), location("right_bank").