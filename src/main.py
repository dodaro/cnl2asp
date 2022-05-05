import sys

from cnl.compile import CNLFile, CNLCompiler, DefinitionError

if __name__ == '__main__':
    with open("examples/HamPath", 'r') as in_file, open("out.txt", "w") as out_file:
        cnl_file: CNLFile = CNLFile(in_file)
        cnl_compiler: CNLCompiler = CNLCompiler()
        try:
            cnl_compiler.compile(cnl_file).into(out_file)
            print('Compilation completed.')
        except DefinitionError as err:
            print(str(err), 'Compilation failed.')
