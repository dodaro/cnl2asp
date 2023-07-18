import argparse
import lark
from cnl.compile import CNLFile, CNLCompiler, DefinitionError


def parse_input(in_file):
    cnl_file = None
    try:
        cnl_file = CNLFile(in_file)
    except lark.exceptions.UnexpectedInput as err:
        print("Syntax error in input file:", err)
    return cnl_file


def check_syntax_only(in_file):
    if parse_input(in_file):
        print("Input file fits the grammar.")


def check_syntax_and_compile(in_file, out_file):
    cnl_file = parse_input(in_file)
    if cnl_file:
        cnl_compiler: CNLCompiler = CNLCompiler()
        try:
            cnl_compiler.compile(cnl_file).into(out_file)
            print('Compilation completed.')
        except DefinitionError as err:
            print(str(err), 'Compilation failed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-syntax', action='store_true', help='Checks that the input fits the grammar')
    parser.add_argument('input_file')
    parser.add_argument('output_file', type=str, nargs='?', default='out.txt')
    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file

    with open(input_file, 'r') as in_file, open(output_file, "w") as out_file:
        if args.check_syntax:
            check_syntax_only(in_file)
        else:
            check_syntax_and_compile(in_file, out_file)
