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

### Values and variables

Subjects and objects can be followed by alphanumeric values, when dealing with specific instances, or alphanumeric variables, when dealing with generic ones.
The difference between these two is that a variable is restricted to starting with an uppercase letter and then only having uppercase letters and numbers, while a value can have any combination of uppercase and lowercase letters and numbers.
Additionally, you can use `_` to separate words within values and variables. E.g.

`monday, minimumWage, john, 10, special_rest,...` are values

`X, Y2, X_Z` are variables

Also values are case insensitive, so `monday` and `Monday` are the same thing.

Variables are special because they can be instantiated using **where** clauses, that you can put at the end of every type of propositions. In this case, there is a notable exception to the rule of always defining the subject type, since the type of said variable has already been defined before. Thus, only the variable itself and the relative instantiation has to be specified, even more that one for **where** clause, using **and** connectors. The istantiations themselves can be of different types:
- list of values (also single-valued lists). E.g.

  `..., where X is one of 10,20 and Y is one of 40,50...`
- ranges. E.g.

  `..., where X is between 20 and 30 ...`
- arithmetic operations (**the sum of**, **the difference of**, **the product of**, **the division of**), even in absolute value. E.g.

  `..., where X is equal to the sum in absolute value of 60 and 100 ...`
- equalities and inequalities (**the same as**, **different from**, **equal to**, **more than**, **greater than**, **less than**, **greater or equal than**, **less or equal than**, **at least**, **at most**)

  `..., where X different that Y ...`

Note that also numeric constants (described below) can be used, and the comma at the start of the clause, although improving the overall legibility, are not mandatory and can be left out.

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

- Compounded definitions use ranges (**goes from ... to ...**) or lists (**is one of** *list1*) in subject position to define things all at once. They support the definition of additional information on their tail, such as the composition of their subject (**is made of ... that is/are made of ...**) and the assignment of additional information w.r.t. the position of the elements inside the list in subject position (**has ... that is equal to respectively** *list2*) E.g.

  `A day goes from 1 to 365 and is made of hours that are made of minutes.`

  `A drink is one of alcoholic, nonalcoholic and has color that is equal to respectively blue, yellow.`

- Enumerative definitions are used to introduce properties of the element in subject position or relationships between the elements in subject and object position, each having their name specified in verb position. They can always hold true (i.e. facts), or they can be conditioned by an additional clause at the tail (**... when ...**). E.g.

  `John is a waiter.`

  `Pub 1 is close to pub 2 and pub X, where X is one of 3,4.`

  `Waiter John works in pub 1.`

  `Waiter W is working when waiter W serves a drink.`

### Quantified Choices

Quantified choice are also used to specify relationships between elements in subject and object positions with name in verb position, although ones that where a choice has to be made between all the values that are legal for the element in object position for every choice of values for the element in subject position and, additionally, also for every choice of values for the objects present in the **for each** clause, that can be specified at the end of the proposition. It follows that, in order for an subject and objects to be valid, they have to be defined beforehand by using one of the possible definition clauses. The number of choices that can be made can also be quantified exactly (**... exactly** *number* **...**) or within a range (**... between** *number1* **and** *number2* **...**). Additionally, values can be chosen from elements of other relationships. E.g.

`Every patron can drink in exactly 1 pub for each day.`

`Every waiter can work in between 1 and 3 pubs.`

`Every waiter can serve a drink.`

`Every patron X can drink with a patron next to patron X.`


### Strong Constraints

Strong constraints introduce conditions that MUST be satisfied, and they come in two flavors: **positive** strong constraints (**It is required that ...**), where you say what you WANT to be true; **negative** strong constraints (**It is prohibited that ...**), where you say what you DON'T WANT to be true (or equivalently, what you want to be false). They differ not only in the starting formula, but also in their body; in fact, positive ones may have a **when** part, where a premise is specified, followed by a **then** part, where the related consequence in specified.
Strong constraints can either contain a list of simple clauses (i.e of subject-verb-object clauses) or aggregate clauses.
Aggregate clauses specify an aggregation of elements in subject position that follow the condition specified in their bodies (**number of ...** for counting up and **total of ...** for summing up) and confronting it to a specific value using one of the aforementioned equality and inequality operators. Aggregates also support aggregating in windows of a specified length followed by the object of which the windows have to be taken (**occurrences between each** *length* *...*), and **for each** clauses, working in a similar manner as those introduced before, mandatory for aggregates in **active** form, that have a body that follows the structure *subject* **that** *verb* *objects* *for_each*, and optional for those in **passive** form have a body that follows the structure *objects* *for_each* **where** *subject* *verb*. E.g.

`It is prohibited that the number of waiters that work in a day is less than 3.`

`It is required that the number of occurrences between each 5 days 
where a waiter works is at least 2`

Simple clauses, on the other hand, can be linked using temporal expressions (**previous**/**next**), even expressing **consecutive** instances, that can be also expressed without them using a **for** clause. E.g.

`It is required that when a waiter works for 2 consecutive days then the next day does not work.`

`It is prohibited that a waiter does not work in a day and also the previous 2 consecutive days does not work.`

`It is required that when waiter X works in pub P1 then waiter X does not work in pub P2, where P1 is different from P2.`

One can also constrain the values that a variable that represent an element in a list can take (**before**/**after**), and use a universal quantifier (**every**) in positive strong constraints to encompass all the instances in subject position to satisfy a particular condition. E.g.

`It is prohibited that waiter X works with waiter W and also waiter X  
works with a waiter before W, where W is between Jack and Mary.`

`It is required that every waiter is payed.`

### Weak Constraints

Strong constraints introduce conditions that are DESIRABLE to be satisfied. They support the definition of a priority level (**high**/**medium**/**low**) and if what you want is the minimization or maximization of a certain value, that can be extracted using an aggregate in much the same way as introduced before. Values obtained it this way can be additionally refined by using an arithmetic operation, or by stating a range of possible legal values.

`It is preferred, with high priority, that the difference in absolute value between 1000 and and the total of items in a box where a drink is stocked ranging between 10 and 5000 is minimized.`

`It is preferred with low priority that the number of drinks that are served is maximized.`

### Additional notes

- Only plurals and third-person verb forms ending in `s` are supported at the moment