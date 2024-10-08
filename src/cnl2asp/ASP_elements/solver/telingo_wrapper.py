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

    def solve(self, time_limit=0) -> list:
        with tempfile.NamedTemporaryFile(mode="w") as file:
            file.write(self.encoding)
            file.seek(0)
            stdout_tmp = sys.stdout
            sys.stdout = telingo_result = StringIO()
            clingo.clingo_main(telingo.TelApp(), [file.name, "--verbose=0", "--quiet=1,2,2", "--warn=none", f"--time-limit={time_limit}"])
            sys.stdout = stdout_tmp
            res = telingo_result.getvalue()
            print(res)
            return res
