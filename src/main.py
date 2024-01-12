import argparse
import json
import traceback


from cnl2asp.cnl2asp import Cnl2asp
from cnl2asp.utility.utility import Utility

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--check-syntax', action='store_true', help='Checks that the input fits the grammar')
    parser.add_argument('--cnl2json', action='store_true', help='Gives a json format of the cnl')
    parser.add_argument('-p', '--print-with-functions', action='store_true',
                        help='Print atoms with functions. ' +
                             'Each attribute is converted into a function,' +
                             'if an entity with same name has been defined')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('input_file')
    parser.add_argument('output_file', type=str, nargs='?', default='out.txt')
    args = parser.parse_args()

    Utility.PRINT_WITH_FUNCTIONS = args.print_with_functions

    input_file = args.input_file
    output_file = args.output_file

    in_file = open(input_file, 'r')
    cnl2asp = Cnl2asp(in_file, args.debug)

    if args.check_syntax:
        if cnl2asp.check_syntax():
            print("Input file fits the grammar.")
    elif args.cnl2json:
        print(json.dumps(cnl2asp.cnl_to_json()))
    else:
        asp_encoding = cnl2asp.compile()
        try:
            with open(output_file, "w") as out_file:
                if out_file.write(asp_encoding):
                    print("Compilation completed.")
        except Exception as e:
            print("Error in writing output", str(e))
