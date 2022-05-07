import sys

from cnl.compile import CNLFile, CNLCompiler, DefinitionError

if __name__ == '__main__':
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("Usage python3 %s input_file [output_file]" % sys.argv[0])
        exit(2)
    
    output_file = "out.txt"
    if len(sys.argv) == 3:
        output_file = sys.argv[2]

    with open(sys.argv[1], 'r') as in_file, open(output_file, "w") as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        try:
            cnl_compiler.compile(cnl_file).into(out_file)
            print('Compilation completed.')
        except DefinitionError as err:
            print(str(err), 'Compilation failed.')
