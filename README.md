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
