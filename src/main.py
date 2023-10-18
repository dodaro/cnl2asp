import argparse
import traceback


from cnl2asp.cnl2asp import Cnl2asp
from cnl2asp.utility.utility import Utility

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--check-syntax', action='store_true', help='Checks that the input fits the grammar')
    parser.add_argument('-p', '--print-with-functions', action='store_true',
                        help='Print atoms with functions.' +
                             'Each attribute is converted into a function,' +
                             'if an entity with same name has been defined')
    parser.add_argument('input_file')
    parser.add_argument('output_file', type=str, nargs='?', default='out.txt')
    args = parser.parse_args()

    if args.print_with_functions:
        Utility.PRINT_WITH_FUNCTIONS = True

    input_file = args.input_file
    output_file = args.output_file

    in_file = open(input_file, 'r')
    cnl2asp = Cnl2asp(in_file)

    if args.check_syntax:
        cnl2asp.check_syntax()
    else:
        asp_encoding = cnl2asp.compile()
        try:
            with open(output_file, "w") as out_file:
                if out_file.write(asp_encoding):
                    print("Compilation completed.")
        except Exception as e:
            traceback.print_exc()
            print("Error in writing output", str(e))
