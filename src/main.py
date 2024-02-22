import argparse
import json
import tempfile

from clingo import Control
from ngo import optimize, auto_detect_input, auto_detect_output

from cnl2asp.ASP_elements.solver.clingo_wrapper import Clingo
from cnl2asp.ASP_elements.solver.clingo_result_parser import ClingoResultParser
from cnl2asp.ASP_elements.solver.telingo_result_parser import TelingoResultParser
from cnl2asp.ASP_elements.solver.telingo_wrapper import Telingo
from cnl2asp.cnl2asp import Cnl2asp
from cnl2asp.utility.utility import Utility
from clingo.ast import parse_files, ProgramBuilder

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--check-syntax', action='store_true', help='Checks that the input fits the grammar')
    parser.add_argument('--cnl2json', action='store_true', help='Gives a json format of the cnl')
    parser.add_argument('--symbols', action='store_true', help='Gives the list of symbols')
    parser.add_argument('-p', '--print-with-functions', action='store_true',
                        help='Print atoms with functions. ' +
                             'Each attribute is converted into a function,' +
                             'if an entity with same name has been defined')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--solve', type=str, choices=["clingo", "telingo"], help='call the solver')
    parser.add_argument('-o', '--optimize', action='store_true', help='optimize the output')
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
    elif args.symbols:
        print(cnl2asp.get_symbols())
    else:
        asp_encoding = cnl2asp.compile()
        if args.optimize:
            asp_encoding = cnl2asp.optimize(asp_encoding)
        try:
            with open(output_file, "w") as out_file:
                if out_file.write(asp_encoding):
                    print("Compilation completed.")
            if args.solve:
                if args.solve == "clingo":
                    solver = Clingo()
                    print("\n*********")
                    print(f"Running {args.solve}...\n")
                    solver.load(str(asp_encoding))
                    res = solver.solve()
                    clingo_res = ClingoResultParser(cnl2asp.parse_input(), res)
                    model = clingo_res.parse_model()
                    print("SOLUTION:\n" + model)
                elif args.solve == "telingo":
                    solver = Telingo()
                    print("\n*********")
                    print(f"Running {args.solve}...\n")
                    solver.load(str(asp_encoding))
                    res = solver.solve()
                    telingo_res = TelingoResultParser(cnl2asp.parse_input(), res)
                    model = telingo_res.parse_model()
                    print("SOLUTION:\n" + model)

        except Exception as e:
            print("Error in writing output", str(e))


