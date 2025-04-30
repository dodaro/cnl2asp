import unittest
from textwrap import dedent
from cnl2asp.cnl2asp import Cnl2asp, MODE
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.specification.signaturemanager import SignatureManager


class TestTheoryExtPropositions(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        SignatureManager.signatures = []
        asp_converter: ASPConverter = ASPConverter()
        asp_converter.clear_support_variables()

    def check_input_to_output(self, input_string, expected_output, mode=MODE.ASP):
        encoding = Cnl2asp(input_string, mode).compile()
        self.assertEqual(encoding.strip(), dedent(expected_output))

    def test_multiple_problems(self):
        self.check_input_to_output('''A node is identified by an id.
                                    The following propositions apply in the initial state:
                                    There is a node with id 1.
                                    The following propositions apply in the final state:
                                    There is a node with id 2.''',
                                   '''\
                                    #program initial.
                                    node(1).

                                    #program final.
                                    node(2).''', mode=MODE.TELINGO)

    def test_initially_inside_temporal_formulas(self):
        self.check_input_to_output("""
                                    A monkey is identified by a name.
                                    Whenever there is initially a monkey M or the true constant, then M can jump.""",
                                   """{jump(M)} :- not not &tel {<< monkey(M) | &true}.""", MODE.TELINGO)

    def test_diff_logic(self):
        self.check_input_to_output('''\
            A sequence is identified by a first starting time, by first machine, by a second starting time, by a second machine, by a time.
            A starting is identified by a time, by machine.
            Whenever there is a sequence with first starting time T1, with first machine M1,
                with second starting time T2, with second machine M2, with time T,
            then the difference between starting with time T1, with machine M1, and 
                starting with time T2, with machine M2 is less than or equal to -T.
            It is prohibited that the difference between starting with time T1, with machine M1, and 
                starting with time T2, with machine M2 is less than or equal to -T, whenever there is a sequence with first starting time T1, with first machine M1,
                with second starting time T2, with second machine M2, with time T.''',
                                   '&diff {starting(T1,M1) - starting(T2,M2)} <= -T :- sequence(T1,M1,T2,M2,T).\n'
                                   ':- sequence(T1,M1,T2,M2,T), &diff {starting(T1,M1) - starting(T2,M2)} <= -T.',
                                   MODE.DIFF_LOGIC)
