node(1..5).
connected_to(1,2).
connected_to(1,3).
connected_to(2,1).
connected_to(2,4).
connected_to(3,1).
connected_to(3,4).
connected_to(4,3).
connected_to(4,5).
connected_to(5,3).
connected_to(5,4).
reachable(1).
{path_to(X,X_e44831ff_2099_4df7_a3e9_d152f5a7cdc4):connected_to(X,X_e44831ff_2099_4df7_a3e9_d152f5a7cdc4)} :- node(X).
:- node(X), #count{X_028ac505_08a0_4a05_87c1_571ec25b4b2c: path_to(X,X_028ac505_08a0_4a05_87c1_571ec25b4b2c)} != 1.
:- node(X), #count{X_9e9c9c9e_fae3_45dc_9623_585a409a32ae: path_to(X_9e9c9c9e_fae3_45dc_9623_585a409a32ae,X)} != 1.
:- not reachable(X_4c71fb63_ff65_4617_8ef0_4ba3d81dd81f), node(X_4c71fb63_ff65_4617_8ef0_4ba3d81dd81f).
reachable(Y) :- reachable(X), path_to(X,Y).
