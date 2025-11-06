1 <= {assignment(X,MD_MCHN,MD_PRCSS_TM): mode(X,MD_MCHN,MD_PRCSS_TM)} <= 1 :- operation(X,_,_).
order(X,Y) :- operation(X,J1,_), assignment(X,_,_), operation(Y,J2,_), assignment(Y,_,_), J2 > J1.
{choice(X,Y)} :- order(X,Y).
choice(Y,X) :- order(X,Y), not choice(X,Y).
start(X,0) :- operation(X,_,1).
start(X,E) :- choice(X,Y), end(X,E).
start(Y,E) :- end(X,E), operation(X,J,N), operation(Y,J,N+1).
end(X,S+P) :- start(X,S), assignment(X,_,P), timeslot(S).
:- start(X,S), not timeslot(S).
makespan(K) :- end(X,K), operation(X,J,N), operation(X+1,J,N+1).
makespan(K) :- makespan(K+1), K < 0.
:~ makespan(K). [1@3,K]
