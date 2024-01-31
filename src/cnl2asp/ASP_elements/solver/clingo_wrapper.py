import clingo


class Clingo:
    def __init__(self):
        self.prg = clingo.Control()
        # Clingo configurations
        self.prg.configuration.solve.opt_mode = 'optN'
        self.prg.configuration.solve.models = '1'

    def load(self, encoding: str):
        self.prg.add(encoding)

    def solve(self) -> clingo.SolveHandle:
        self.prg.ground([("base", [])])
        with self.prg.solve(yield_=True) as handle:
            for model in handle:
                if model.optimality_proven:
                    return model
        return model
