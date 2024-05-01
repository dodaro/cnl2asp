import clingo
import telingo
import tempfile

from io import StringIO
import sys

class Telingo:
    def __init__(self):
        self.encoding = ''

    def load(self, encoding: str):
        self.encoding = encoding

    def solve(self):
        with tempfile.NamedTemporaryFile(mode="w") as file:
            file.write(self.encoding)
            file.seek(0)
            sys.stdout = telingo_result = StringIO()
            clingo.clingo_main(telingo.Application(), [file.name, "--verbose=0", "--quiet=1,2,2", "--warn=none"])
            sys.stdout = sys.__stdout__
            return telingo_result.getvalue()
