# cnl2asp

A prototype for a Controlled Natural Language based on English.

A document written in this language is compiled into an equivalent version expressed in Answer Set Programming.

The compiler is written in the Python (>= 3.10) programming language.

## Dependencies

- lark

## Usage

`python3.10 src/main.py input_file [output_file]`

Example:

`python3.10 src/main.py src/examples/hamp_path hamp_path.lp`

If the output_file is not specified a file out.txt will be created.

## Features

Being a Controlled Natural Language, only a subset of the grammar and vocabulary of English is supported. As a result, some things may not be expressible, while others can but have to be rephrased in the supported framework. Below an overview of our framework or refer to [CNL2ASP: Converting Controlled Natural
Language Sentences into ASP](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/AF5901FADC579E49C583CFD5A10C0192/S1471068423000388a.pdf/div-class-title-cnl2asp-converting-controlled-natural-language-sentences-into-asp-div.pdf) for a more detailed description.

### Input file structure
Our cnl specification consists of two main blocks. In the first block all the concept of the problem are defined, where in our context
a concept is a thing, a place, a person or an object that are used to model entities of the application domain of the CNL (see [Concepts definition](#concepts-definition)).
The second block, on the other hand, constitutes the rules of the problem, i.e. the various assignments and constraints (see [Rules definition](#rules-definition)).

### Concepts definition

In order to define an entity we expect a name, and a series of attributes. 

`A movie has an id, a name, and a duration.`

In this example, *movie* is the **name** of the entity. *id*, *name*, and *duration* are the **attributes**. Therefore, every time this name will be used, it will be recognised by the tool as an entity with this structure.
Moreover, attributes can be defined as keys as in the following:

`A movie is identified by an id, and has a name, and a duration.`

In this case, *id* is saved as a **key** that is the attribute that **identifies** a *movie*.

#### Why keys?
We support constructs in the tool that allow different entities to be automatically linked. In case keys are provided, the tool will try to link only these, otherwise it will take all the attributes. Consider for example the following lines (a more detailed description of this proposition is provided in [Defining new concepts](#defining-new-concepts)):

`An author has written a book.`

You probably want that only the name of the *author* and the id of the *book* are linked by written. You may define author and movie as follow:

`An author is identified by a name, and has an age, and a country.`\
`A book is identified by an id, and has a name, a language.`


### Rules definition
As first is shown how to use an entity (recalling the defined concepts) in the proposition, and then the main constructions of the cnl are presented.

### ENTITY
An *ENTITY* is defined as:

`ENTITY -> NAME LABEL? ATTRIBUTES?`

where *NAME* is one of the defined concepts, LABEL is a temporary name which can be used to refer to the same entity within a proposition, and *ATTRIBUTES* is a comma separated list of *ATTRIBUTE*, defined as follows:

`ATTRIBUTE -> with ATTRIBUTE_NAME VALUE?`

where *ATTRIBUTE_NAME* should recall the attributes defined for that entity, and *VALUE* can be an uppercase string or an operation. 


Examples:

`a movie M` (M is a label)\
`a movie with id MOVIEID` (the attribute id will be initialized with value MOVIEID)\
`a movie with id MOVIEID, with duration 100` (the attribute id will be initialized with value MOVIEID, and the attribute duration with value equal to 100)\
`a movie with id MOVIEID+1` (the attribute id will be initialized with value MOVIEID+1)\
`a movie with id MOVIEID greater than X` (it is also possible to do comparisons between different attributes, result: MOVIEID > X)


### Defining new concepts
From the concepts defined in the first block can be created new concepts, it is possible to not define them in the *Concepts definition* block.
A new concept is something that you probably want to compute, a new knowledge.

#### Simple definition
The simplest way to define a new concept is:

`simple_definition -> ENTITY AUXILIARY_VERB? NEW_DEFINITION LIST_OF_ENTITIES?.`

where *AUXILIARY_VERB* are the verbs to be, to have, and to do, *NEW_DEFINITION* has the same structure of *ENTITY* (we used a different name for explanation reasons) and *LIST_OF_ENTITIES* is a comma separated list of *ENTITY*.

Examples:

`An author has written a movie.` (NEW_DEFINITION = *written*)\
`Director Spielberg has written a movie with name equal to JurassicPark.` (NEW_DEFINITION = *written*)\
`Waiter John serves a drink alcoholic.` (NEW_DEFINITION = *serves*)

#### Quantified choice proposition
A quantified choice proposition is defined as follow:

`quantified_choice_proposition -> QUANTIFIER ENTITY ASSIGNMENT_VERB AUXILIARY_VERB? NEW_DEFINITION CARDINALITY? LIST_OF_ENTITIES?.`
 
where *QUANTIFIER* is a terminal symbol and can be one of "every" or "any", *ASSIGNMENT_VERB*, instead, is one of "can" and "must". "can" is used to define a choice with the corresponding *CARDINALITY*, while "must" is used to define an assignment.

Examples:

`Every patron can drink in exactly 1 pub.`\
`Every waiter must serve a drink.`\
`Every movie with id I can have a scoreAssignment with movie I, and with value greater than 1.`

#### Whenever/Then propositions
First of all, a *WHENEVER_CLAUSE* is defined as follows:

`WHENEVER_CLAUSE -> "Whenever there is" ENTITY`

A Whenever/Then propositions is:

`WHENEVER_THAN_CLAUSE -> LIST_OF_WHENEVER_CLAUSE "then" ENTITY ASSIGNMENT_VERB AUXILIARY_VERB? [CARDINALITY] NEW_DEFINITION LIST_OF_ENTITIES`

where, as previously, LIST_OF_*ELEMENT* is a comma separated list of *ELEMENT*.

Examples:

`Whenever there is a movie with director equal to spielberg, with id X then we must have a topmovie with id X.` (in this example we have an ENTITY = *we*, it is possibile to use pronouns and in that case, it is ignored and not converted into any entity)\
`Whenever there is a movie M, then M can be assigned to exactly 1 director.`


### Constraints
Before describing the constraints some building block must be defined: *AGGREGATE* and *COMPARISON*.

1. `AGGREGATE -> AGGREGATE_OPERATOR "of" ATTRIBUTE "that" AUXILIARY_VERB? ENTITY LIST_OF_ENTITIES?`\
                `| AGGREGATE_OPERATOR "of" ATTRIBUTE "where" ENTITY AUXILIARY_VERB? ENTITY LIST_OF_ENTITIES?`\
  Examples:\
  `the number of waiters that work in a day`\
  `the total value of a scoreAssignment with movie id X` 


2. `COMPARISON -> COMPARISON_OPERAND "is" COMPARISON_OPERATOR COMPARISON_OPERAND`\
  Here, as a *COMPARISON_OPERAND* can be used *AGGREGATE*, arithmetic expressions, *ATTRIBUTE*.\
  Examples:\
  `the number of waiters that work in a day is equal to 2`\
  `X is equal to Y`


Going back to the *CONSTRAINT_PROPOSITION*, a *CONSTRAINT_PROPOSITION* is made as follows:

`CONSTRAINT_PROPOSITION -> CONSTRAINT_OPERATOR (COMPARISON | THERE_IS_ENTITY).`

 where *THERE_IS_CLAUSE* is, intuitively, "there is *ENTITY*".

Examples:\
`It is prohibited that the number of waiters that work in a day is less than 3.`\
`It is prohibited that the lowest value of a scoreAssignment with movie id X is equal to 1.`\
`It is prohibited that there is a scoreAssignment with value V less than 1.`


### Weak Constraints

Similarly to constraint, weak constraints are:

`WEAK_CONSTRAINT -> "It is preferred" OPTIMIZATION_SATEMENT? PRIORITY_LEVEL "that" (COMPARISON | SIMPLE_DEFINITION | AGGREGATE | LIST_OF_WHENEVER_CLAUSES) (ATTRIBUTE "is" ("maximized" | "minimized"))?.`

where *OPTIMIZATION_STATEMENT* is used to express if it is a minimization or a maximization and *PRIORITY_LEVEL* to express, intuitively, the priority level.

Examples:\
`It is preferred with low priority that the number of drinks that are served is maximized.`\
`It is preferred, with medium priority, that whenever there is a topMovie with id I, whenever there is a scoreAssignment with movie I, and with value V, V is maximized.`

### Advanced concepts

#### Terminal clauses
Sentences already presented have a certain degree of expressivity, however they also support terminal clauses at the end.
We defined terminal_clauses as:

`terminal_clause -> (whenever_clause
                   | _CNL_WHERE where_clause
                   | when_clause)`

the whenever_clause as previously add a new condition to be satisfied, the where clause can be used as variable substitution and when_clause, similarly to the whenever clause, add a new condition.

Examples:\
`It is prohibited that X is equal to Y, whenever there is a movie with id X, and with year equal to 1964, whenever there is a topMovie with id Y.`\
`It is prohibited that waiter W1 work in pub P1 and also waiter W2 work in pub P1, where W1 is different from W2.`\
`Waiter W is working when waiter W serves a drink.`

#### Automatic link entities
Verbs express a relation between entities, when their values are not specified, an algorithm link them. 
The algorithm takes 2 entities in input and match all the attributes with the same name and origin.
The origin is the name of the first entity that declare that origin, consider for example:\

`A car is identified by an id.`\
`A node is identified by an id.`

These two attributes called id will not be linked since have a different origin.

#### Typed entities
There are some special entity types supported in CNL2ASP. 
In particular, we currently support temporal entities, list and set. 
* Temporal entities are in the form:

    `A timeslot is a temporal concept expressed in minutes ranging from 07:30 AM to 01:30 PM with a length of 10 minutes.`\
    `A time is a temporal concept expressed in steps ranging from 0 to 10.`
    
    the tool will generate all the values between the range provided and allows you to perform some particular temporal operations:
    
    `It is required that the assignment A is after 11:20 AM,...` (from the cts problem)

* Set:

    `Graph is a set.` (set definition)\
    `Graph containts node1, node2. node3.` (set initialization)\
    `Whenever there is an element X in graph...` (usage)

* List:

    `shift is a list.` (list definition)\
    `shift contains morning, afternoon, night.` (list initialization)\
    `It is prohibited that a nurse works in the shift element after night.` (usage)\
    `It is prohibited that a nurse works in the 1st element in shift.` (usage)\
