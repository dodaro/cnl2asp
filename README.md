# cnl2asp

A prototype for a Controlled Natural Language based on English.

A document written in this language is compiled into an equivalent version expressed in Answer Set Programming.

The compiler is written in the Python (>= 3.10) programming language.

## Dependencies

- lark

## Usage

`python3.10 src/main.py input_file [output_file]`

Example:

`python3.10 src/main.py src/examples/3Col 3Col.lp`

If the output_file is not specified a file out.txt will be created.

## Features

Being a Controlled Natural Language, only a subset of the grammar and vocabulary of English is supported. As a result, some things may not be expressible, while others can but have to be rephrased in the supported framework described below.

### Subjects and objects

They can be used to refer to entities in your documents. E.g.

`nurse, waiter, day, hour, salary, ...`

They are case insensitive, so a `nurse` and a `Nurse` are the same thing.
Additionally, they can be followed by either a value or a variable. It is important to keep in mind that, wherever you want to refer to a particular value (or variable) of a particular type of subject (or object), the latter must ALWAYS be specified. E.g.

`Waiter Alice is payed salary minimumWage.` is valid (minimumWage is of type salary)

`Waiter Alice is payed minimumWage.` is not valid (minimumWage has no type)

A notable exception to this rule are variable instantiation defined in **where** clauses (described below) where, since the type of said variable has already been defined, only the variable itself and the relative instantiation has to be specified.

### Values and variables

Subjects and objects can be followed by alphanumeric values, when dealing with specific instances, or alphanumeric variables, when dealing with generic ones.
The difference between these two is that a variable is restricted to starting with an uppercase letter and then only having uppercase letters and numbers, while a value can have any combination of uppercase and lowercase letters and numbers.
Additionally, you can use `_` to separate words within values and variables. E.g.


`monday, minimumWage, john, 10, special_rest,...` are values

`X, Y2, X_Z` are variables

Also values are case insensitive, so `monday` and `Monday` are the same thing.



### Verbs and copulas

Verbs represent meaningful relationships and properties among elements in your document and can be accompanied by one of the propositions listed below:

- `to`
- `for`
- `from`
- `on`
- `at`
- `about`
- `with`
- `in`

E.g.

`work in, connected to, ...`

Another way of fulfilling the role of verbs in a phrase is by also using names introduced by a copula and, optionally, followed by a proposition. E.g.

`has a path to, is chosen, ...`

### Definitions

Definitions are what you use to define concepts that are later used inside your document. There are different kinds of definitions that are supported by the CNL:
- Constant definitions are used to define constant values, with their name in subject position. E.g.

  `myConstant is equal to 10.`


- Compounded definitions use ranges (goes from ... to ...) or lists (is one of *list1*) in subject position to define things all at once. They support the definition of additional information on their tail, such as the composition of their subject (is made of ... that is/are made of ...) and the assignment of additional information w.r.t. the position of the elements inside the list in subject position (has ... that is equal to respectively *list2*) E.g.

  `A day goes from 1 to 365 and is made of hours that are made of minutes.`

  `A drink is one of alcoholic, nonalcoholic and has color that is equal to respectively blue, yellow.`

- Enumerative definitions are used to introduce properties of the element in subject position or relationships between the elements in subject and object position, each having their name specified in verb position. They can always hold true (i.e. facts), or they can be conditioned by an additional definition at the tail (... when ....). E.g.

  `John is a waiter. `

  `Pub 1 is close to pub 2 and pub X, where X is equal to 3,4.`

  `Waiter John works in pub 1.`

  `Waiter W is working when waiter W serves a drink.`

### Quantified Choices

### Strong Constraints

### Weak Constraints