# USER CNL DEFINITION

## Definire la grammatica
Ci sono due tipi di regole:
- le regole di supporto. Queste regole definiscono costrutti che possono essere riutilizzati all'interno di altre regole
- regole di produzione. Queste regole definiscono le proposizioni vere e proprie.
### Regole di supporto
```
[aggregate]
aggregate: "the" sum{aggregate.operator} "of" VALUE{aggregate.discriminant} "of" ENTITY{aggregate.body}.
```

Le regole di supporto sono identificate da un elemento che specifica che **tipo di costruzione** si vuole avere (nell'esempio ```[aggregate]```), una **label** che sarà l'identificativo con cui questa costruzione verrà richiamata nelle altre proposizioni (```aggregate:```) e, infine, la specifica della proposizione (```"the" sum{aggregate.operator} "of" VALUE{aggregate.discriminant} "of" ENTITY{aggregate.body}.```).
Nell'esempio si possono notare altri due elementi che permettono di specificare le parti della proposizione. In particolare ci sono simboli terminali, che sono usati solo per la costruzione del linguaggio e sono quelli tra " " (```"the"```, ```"of"```).
E dei simboli non temrinali, quelli che richiamano regole di supporto (```sum```, ```value```, ```entity```). Questi hanno inoltre tra { } una **funzione** che specifica che permette al tool di capire come andrà tradotto il simbolo.

Le label supportate sono:
- [constraint]: crea una constraint
- [assignment]: crea una assegnazione semplice
- [choice]: crea una choice
- [preference]: crea un weak constraint
- [aggregate]: crea un aggregato
- [operation]: crea un'operazione

Inoltre sono supportate labels per definire gli operatori degli aggregati:
- [aggregate.operator.sum]
- [aggregate.operator.count]
- [aggregate.operator.min]
- [aggregate.operator.max]

E gli operatori temporali:
- [operation.operator.sum]
- [operation.operator.difference]
- [operation.operator.multiplication]
- [operation.operator.division]
- [operation.operator.equality]
- [operation.operator.inequality]
- [operation.operator.greater_than]
- [operation.operator.less_than]
- [operation.operator.greater_than_or_equal_to]
- [operation.operator.less_than_or_equal_to]
- [operation.operator.conjunction]
- [operation.operator.disjunction]
- [operation.operator.left_implication]
- [operation.operator.right_implication]
- [operation.operator.equivalence]
- [operation.operator.negation]
- [operation.operator.previous]
- [operation.operator.weak_previous]
- [operation.operator.trigger]
- [operation.operator.always_before]
- [operation.operator.since]
- [operation.operator.eventually_before]
- [operation.operator.precede]
- [operation.operator.weak_precede]
- [operation.operator.next]
- [operation.operator.weak_next]
- [operation.operator.release]
- [operation.operator.always_after]
- [operation.operator.until]
- [operation.operator.eventually_after]
- [operation.operator.follow]
- [operation.operator.weak_follow]

### Regole di produzione
```
[constraint]
"It is forbidden that" operation{body}.
```
Queste regole hanno sempre l'identificativo iniziale (choice, constraint,..), ma non hanno la label e sono costituite solo da simboli terminali (" ") o utilizzano labels già definite con la corrispondente funzione tra { }. 

Se viene usato un simbolo non terminale non definito, questo considerato come una stringa.

Le funzioni supportate sono:
- [head]: aggiunge l'entità nella testa della regola
- [body]: aggiunge l'entità nel corpo
- [condition]: aggiunge l'entità come condizione
- [aggregate.operator]: l'elemento è usato come identificatore dell'opetore dell'aggregato
- [aggregate.body]: l'elemento viene inserito nel corpo dell'aggregato
- [aggregate.discriminant]: l'elemento viene inserito nel discriminante dell'aggregato
- [operation.operator]: l'elemento è usato come identificatore dell'opetore dell'operazione
- [operation.operand]: l'elemento viene inserito negli operatori dell'operazione (se più di uno, viene seguito l'ordine di definizione da sinistra verso destra)

## Esempio
**CNL**
```
import explicit_definition_proposition
[aggregate.operator.sum]
sum: "sum".
[aggregate]
aggregate: "the" sum{aggregate.operator} "of" VALUE{aggregate.discriminant} "of a" ENTITY{aggregate.body}.
[operation.operator.equality]
equal: "equal to".
[operation]
operation: aggregate{operation.operand} "is" equal{operation.operator} VALUE{operation.operand}.
[constraint]
"It is forbidden that" operation{body}.
```

**Input**
```
A node is identified by an id. 
It is forbidden that the sum of id of a node is equal to 1.
```

**Traduzione**
```
:- #sum{D: node(D)} = 1.
```