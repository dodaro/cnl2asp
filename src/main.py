import argparse
import lark
from cnl2asp.cnl.compile import CNLFile, CNLCompiler, DefinitionError
from cnl2asp.cnl2asp import Cnl2asp

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-syntax', action='store_true', help='Checks that the input fits the grammar')
    parser.add_argument('input_file')
    parser.add_argument('output_file', type=str, nargs='?', default='out.txt')
    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file

    with open(input_file, 'r') as in_file:
        cnl2asp = Cnl2asp(in_file)
        if args.check_syntax:
            if cnl2asp.check_syntax():
                print("Input file fits the grammar.")
        else:
            with open(output_file, "w") as out_file:
                result = cnl2asp.compile()
                if result:
                    out_file.write(result)
                    print("Compilation completed.")
