# Experiments

These are the results obtained by running [telingo](https://github.com/potassco/telingo) with the CNL2TEL generated encodings and the orginal human written encodings taken from the [telingo](https://github.com/potassco/telingo/tree/master/examples)'s repository.

You can reproduce the experiments by runnnig:
    
`telingo {DOMAIN}/{TYPE}/encoding.lp`

where DOMAIN is one of the problem name: 
 - gun, 
 - hanoi, 
 - logistic, 
 - monkey, 
 - moore, 
 - river_crossing;

and TYPE is one of: cnl, original.

Moreover, for the hanoi, logistic and moore problems you have to specify the instance by adding the following flag
`-c n={VALUE}` 
