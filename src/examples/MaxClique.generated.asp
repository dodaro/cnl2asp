node(1..5).
connected_to(1,2).
connected_to(1,3).
connected_to(2,1).
connected_to(2,3).
connected_to(2,4).
connected_to(2,5).
connected_to(3,1).
connected_to(3,2).
connected_to(3,4).
connected_to(3,5).
connected_to(4,2).
connected_to(4,3).
connected_to(4,5).
connected_to(5,2).
connected_to(5,3).
connected_to(5,4).
{chosen(X_d249125f_3e44_4fba_9676_42cac72b7fb3)} :- node(X_d249125f_3e44_4fba_9676_42cac72b7fb3).
:- not connected_to(X,Y), chosen(X), chosen(Y), X != Y.
:~ #count{X_c7a4c9aa_cb01_4c44_93de_f920ac1584f1: chosen(X_c7a4c9aa_cb01_4c44_93de_f920ac1584f1)} = X_63b146db_99ad_43b8_849f_d049a9bb3bc3. [-X_63b146db_99ad_43b8_849f_d049a9bb3bc3@3]
