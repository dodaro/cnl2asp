node(1..3).
color(1,"red").
color(2,"green").
color(3,"blue").
connected_to(1,2).
connected_to(1,3).
connected_to(2,1).
connected_to(2,3).
connected_to(3,1).
connected_to(3,2).
1 <= {assigned_to(X_c1d29d83_0f13_47a7_bea0_dcf4538ebb11,X_38b42d9b_236b_4ea0_8134_bff7e8517f01):color(_,X_38b42d9b_236b_4ea0_8134_bff7e8517f01)} <= 1 :- node(X_c1d29d83_0f13_47a7_bea0_dcf4538ebb11).
:- connected_to(X,Y), assigned_to(X,C), assigned_to(Y,C).
