import random
import sys
import unittest
from io import StringIO
from textwrap import dedent

from cnl2asp.parser.asp_compiler import ASPTransformer

from cnl2asp.ASP_elements.solver.telingo_result_parser import TelingoResultParser
from cnl2asp.ASP_elements.solver.telingo_wrapper import Telingo
from cnl2asp.cnl2asp import Cnl2asp, MODE
from cnl2asp.ASP_elements.solver.clingo_wrapper import Clingo
from cnl2asp.ASP_elements.solver.clingo_result_parser import ClingoResultParser
from cnl2asp.converter.asp_converter import ASPConverter
from cnl2asp.specification.signaturemanager import SignatureManager


class TestClingoResultParser(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        SignatureManager.signatures = []
        asp_converter: ASPConverter = ASPConverter()
        asp_converter.clear_support_variables()

    def compute_clingo_explaination(self, cnl: str, answer_set: str, ):
        cnl2asp = Cnl2asp(cnl)
        return ClingoResultParser(cnl2asp.get_transformer().transform(cnl2asp.parse_input())).parse_model(
            answer_set.splitlines()).strip()

    def compute_telingo_explaination(self, cnl: str, answer_set: str, ):
        cnl2asp = Cnl2asp(cnl, mode=MODE.TELINGO)
        return TelingoResultParser(cnl2asp.get_transformer().transform(cnl2asp.parse_input())).parse_model(
            answer_set).strip()


    def test_graph_coloring(self):
        cnl = dedent('''\
                A node goes from 1 to 3.
                A color is one of red, green, blue.
                Node 1 is connected to node X, where X is one of 2, 3.
                Node 2 is connected to node X, where X is one of 1, 3.
                Node 3 is connected to node X, where X is one of 1, 2.
                Every node can be assigned to exactly 1 color.
                It is required that when node X is connected to node Y then node X is not assigned to color C and also node Y is not assigned to color C.''')
        answer_set = dedent('''\
                node(1)
                node(2)
                node(3)
                connected_to(1,2)
                connected_to(1,3)
                connected_to(2,1)
                connected_to(2,3)
                connected_to(3,1)
                connected_to(3,2)
                color("red")
                color("green")
                color("blue")
                assigned_to(3,"red")
                assigned_to(2,"green")
                assigned_to(1,"blue")''')
        self.assertEqual(self.compute_clingo_explaination(cnl, answer_set), dedent('''\
                                                    There is node 1.
                                                    There is node 2.
                                                    There is node 3.
                                                    Node 1 is connected to node 2.
                                                    Node 1 is connected to node 3.
                                                    Node 2 is connected to node 1.
                                                    Node 2 is connected to node 3.
                                                    Node 3 is connected to node 1.
                                                    Node 3 is connected to node 2.
                                                    There is color red.
                                                    There is color green.
                                                    There is color blue.
                                                    Node 3 is assigned to color red.
                                                    Node 2 is assigned to color green.
                                                    Node 1 is assigned to color blue.'''))

    def test_monkey_problem(self):
        cnl = dedent('''\
                    An agent is identified by a name.
                    A monkey is identified by an agent.
                    A box is identified by an agent.
                    A banana is identified by an agent.
                    
                    The following propositions always apply:
                    A location is one of door, window, middle.
                    There is monkey with agent name 1.
                    There is box with agent name 2.
                    There is banana with agent name 3.
                    
                    The following propositions apply in the initial state:
                    Monkey M is at location door.
                    Box B is at location window.
                    
                    The following propositions always apply except in the initial state:
                    Whenever there is a monkey M, then M must walk to a location X or push to a location X or climb or grasp.
                    A monkey M has moved, when monkey M is at location X and also monkey M is previously at location Y, where X is different from Y.
                    A box B has moved, when box B is at location X and also box B is previously at location Y, where X is different from Y.
                    Monkey M is at location X when monkey M is previously at location X and also monkey M has not moved.
                    Box B is at location X when box B is previously at location X and also box B has not moved.
                    Monkey M is on box B when monkey M is previously on box B.
                    A monkey M is at a location X when monkey M walks to location X.
                    It is prohibited that a monkey M walks to location X when monkey M is previously at a location X.
                    It is prohibited that a monkey M walks to location X when monkey M is previously on a box B.
                    It is prohibited that a monkey M push to location X when monkey M is previously on a box B.
                    It is prohibited that a monkey M push to location X when monkey M is previously at location X.
                    It is prohibited that a monkey M push to location X, a box B when monkey M is previously at location Y and also box B is previously at location Z, where Y is different from Z.
                    Monkey M gets a banana B when monkey M grasps.
                    It is prohibited that monkey M grasp a banana BA when monkey M is not previously on box BO.
                    It is prohibited that monkey M grasps banana B when monkey M is previously at location X, where X is different from middle.
                    Monkey M is on box B when monkey M climb box B.
                    It is prohibited that monkey M climb box B when monkey M is previously on box B.
                    It is prohibited that monkey M climbs box B when monkey M is at location X and also box B is at location Y, where X is different from Y.
                    A monkey M is at location X when monkey M push to location X.
                    A box B is at location X when monkey M push to location X, box B.
                    
                    The following propositions apply in the final state:
                    It is required that monkey M gets banana B.''')
        answer_set = dedent('''\
                     State 0:
                      banana(3)
                      box(2)
                      location("door") location("middle") location("window")
                      monkey(1)
                      at(1,"door") at(2,"window")
                     State 1:
                      banana(3)
                      box(2)
                      location("door") location("middle") location("window")
                      monkey(1)
                      moved(1)
                      at(1,"window") at(2,"window")
                      walk_to(1,"window")
                     State 2:
                      banana(3)
                      box(2)
                      location("door") location("middle") location("window")
                      monkey(1)
                      moved(1) moved(2)
                      at(1,"middle") at(2,"middle")
                      push_to(1,"middle")
                     State 3:
                      banana(3)
                      box(2)
                      climb(1)
                      location("door") location("middle") location("window")
                      monkey(1)
                      at(1,"middle") at(2,"middle")
                      on(1,2)
                     State 4:
                      banana(3)
                      box(2)
                      grasp(1)
                      location("door") location("middle") location("window")
                      monkey(1)
                      at(1,"middle") at(2,"middle")
                      get(1,3)
                      on(1,2)''')
        self.assertEqual(self.compute_telingo_explaination(cnl, answer_set), dedent('''\
                                                                            -- In the 0 state:
                                                                            There is monkey 1.
                                                                            There is location window.
                                                                            There is location middle.
                                                                            There is location door.
                                                                            There is box 2.
                                                                            There is banana 3.
                                                                            Monkey 1 is at location door.
                                                                            Box 2 is at location window.
                                                                            -- In the 1 state:
                                                                            There is monkey 1.
                                                                            There is location window.
                                                                            There is location middle.
                                                                            There is location door.
                                                                            There is box 2.
                                                                            There is banana 3.
                                                                            Box 2 is at location window.
                                                                            Monkey 1 has moved.
                                                                            Monkey 1 is at location window.
                                                                            Monkey 1 walk to location window.
                                                                            -- In the 2 state:
                                                                            There is monkey 1.
                                                                            There is location window.
                                                                            There is location middle.
                                                                            There is location door.
                                                                            There is box 2.
                                                                            There is banana 3.
                                                                            Monkey 1 has moved.
                                                                            Box 2 has moved.
                                                                            Monkey 1 is at location middle.
                                                                            Box 2 is at location middle.
                                                                            Monkey 1 push to location middle.
                                                                            -- In the 3 state:
                                                                            There is monkey 1.
                                                                            There is location window.
                                                                            There is location middle.
                                                                            There is location door.
                                                                            There is box 2.
                                                                            There is banana 3.
                                                                            Monkey 1 is at location middle.
                                                                            Box 2 is at location middle.
                                                                            Monkey 1 climb.
                                                                            Monkey 1 is on box 2.
                                                                            -- In the 4 state:
                                                                            There is monkey 1.
                                                                            There is location window.
                                                                            There is location middle.
                                                                            There is location door.
                                                                            There is box 2.
                                                                            There is banana 3.
                                                                            Monkey 1 is at location middle.
                                                                            Box 2 is at location middle.
                                                                            Monkey 1 is on box 2.
                                                                            Monkey 1 grasp.
                                                                            Monkey 1 get banana 3.'''))

    def test_river_crossing_problem(self):
        cnl = dedent('''\
                    A location is identified by a name.
                    An item is identified by an id.
                    A farmer is identified by an item.
                    A route is identified by a starting location, and by an arriving location.
                    
                    The following propositions always apply:
                    An item is one of fox, beans, goose.
                    There is a farmer with item id 1.
                    There is a location left_bank.
                    There is a location right_bank.
                    There is a route with starting location equal to left_bank, with arriving location equal to right_bank.
                    There is a route with starting location equal to right_bank, with arriving location equal to left_bank.
                    Item fox eats item goose.
                    Item goose eats item beans.
                    
                    The following propositions apply in the initial state:
                    Item fox is at location left_bank.
                    Item goose is at location left_bank.
                    Item beans are at location left_bank.
                    Farmer F is at location left_bank.
                    
                    The following propositions always apply except in the initial state:
                    Every item I can be moved.
                    It is prohibited that the number of items that are moved is greater than 1.
                    
                    Item X is at location B, when item X is previously at location A and also item X is moved, whenever there is a route with starting location A, with arriving location B.
                    Item X is at location A, when item X is previously at location A and also item X is not moved.
                    Farmer F is at location B, when farmer F is previously at location A, whenever there is a route with starting location A, with arriving location B.
                    It is prohibited that item X is moved, when farmer F is previously at location A and also item X is not previously at location A.
                    
                    The following propositions always apply:
                    It is prohibited that item X is at location A and also item X is at location B, where A is different from B.
                    
                    It is prohibited that item X is at location A and also item Y is at location A, when item X eats item Y and also farmer F is not at location A.
                    
                    The following propositions apply in the final state:
                    It is required that item X is at location right_bank.''')
        answer_set = dedent('''\
                             State 0:
                              farmer(1)
                              item("beans") item("fox") item("goose")
                              location("left_bank") location("right_bank")
                              at(1,"left_bank") at("beans","left_bank") at("fox","left_bank") at("goose","left_bank")
                              eat("fox","goose") eat("goose","beans")
                              route("left_bank","right_bank") route("right_bank","left_bank")
                             State 1:
                              farmer(1)
                              item("beans") item("fox") item("goose")
                              location("left_bank") location("right_bank")
                              moved("goose")
                              at(1,"right_bank") at("beans","left_bank") at("fox","left_bank") at("goose","right_bank")
                              eat("fox","goose") eat("goose","beans")
                              route("left_bank","right_bank") route("right_bank","left_bank")
                             State 2:
                              farmer(1)
                              item("beans") item("fox") item("goose")
                              location("left_bank") location("right_bank")
                              at(1,"left_bank") at("beans","left_bank") at("fox","left_bank") at("goose","right_bank")
                              eat("fox","goose") eat("goose","beans")
                              route("left_bank","right_bank") route("right_bank","left_bank")
                             State 3:
                              farmer(1)
                              item("beans") item("fox") item("goose")
                              location("left_bank") location("right_bank")
                              moved("fox")
                              at(1,"right_bank") at("beans","left_bank") at("fox","right_bank") at("goose","right_bank")
                              eat("fox","goose") eat("goose","beans")
                              route("left_bank","right_bank") route("right_bank","left_bank")
                             State 4:
                              farmer(1)
                              item("beans") item("fox") item("goose")
                              location("left_bank") location("right_bank")
                              moved("goose")
                              at(1,"left_bank") at("beans","left_bank") at("fox","right_bank") at("goose","left_bank")
                              eat("fox","goose") eat("goose","beans")
                              route("left_bank","right_bank") route("right_bank","left_bank")
                             State 5:
                              farmer(1)
                              item("beans") item("fox") item("goose")
                              location("left_bank") location("right_bank")
                              moved("beans")
                              at(1,"right_bank") at("beans","right_bank") at("fox","right_bank") at("goose","left_bank")
                              eat("fox","goose") eat("goose","beans")
                              route("left_bank","right_bank") route("right_bank","left_bank")
                             State 6:
                              farmer(1)
                              item("beans") item("fox") item("goose")
                              location("left_bank") location("right_bank")
                              at(1,"left_bank") at("beans","right_bank") at("fox","right_bank") at("goose","left_bank")
                              eat("fox","goose") eat("goose","beans")
                              route("left_bank","right_bank") route("right_bank","left_bank")
                             State 7:
                              farmer(1)
                              item("beans") item("fox") item("goose")
                              location("left_bank") location("right_bank")
                              moved("goose")
                              at(1,"right_bank") at("beans","right_bank") at("fox","right_bank") at("goose","right_bank")
                              eat("fox","goose") eat("goose","beans")
                              route("left_bank","right_bank") route("right_bank","left_bank")''')
        self.assertEqual(self.compute_telingo_explaination(cnl, answer_set), dedent('''\
                                                                                    -- In the 0 state:
                                                                                    There is route with starting_location equal to right_bank, with arriving_location equal to left_bank.
                                                                                    There is route with starting_location equal to left_bank, with arriving_location equal to right_bank.
                                                                                    There is location right_bank.
                                                                                    There is location left_bank.
                                                                                    There is item goose.
                                                                                    There is item fox.
                                                                                    There is item beans.
                                                                                    There is farmer 1.
                                                                                    Farmer 1 is at location left_bank.
                                                                                    Item beans is at location left_bank.
                                                                                    Item fox is at location left_bank.
                                                                                    Item goose is at location left_bank.
                                                                                    Item fox eat item goose.
                                                                                    Item goose eat item beans.
                                                                                    -- In the 1 state:
                                                                                    There is route with starting_location equal to right_bank, with arriving_location equal to left_bank.
                                                                                    There is route with starting_location equal to left_bank, with arriving_location equal to right_bank.
                                                                                    There is location right_bank.
                                                                                    There is location left_bank.
                                                                                    There is item goose.
                                                                                    There is item fox.
                                                                                    There is item beans.
                                                                                    There is farmer 1.
                                                                                    Item beans is at location left_bank.
                                                                                    Item fox is at location left_bank.
                                                                                    Item fox eat item goose.
                                                                                    Item goose eat item beans.
                                                                                    Item goose is moved.
                                                                                    Farmer 1 is at location right_bank.
                                                                                    Item goose is at location right_bank.
                                                                                    -- In the 2 state:
                                                                                    There is route with starting_location equal to right_bank, with arriving_location equal to left_bank.
                                                                                    There is route with starting_location equal to left_bank, with arriving_location equal to right_bank.
                                                                                    There is location right_bank.
                                                                                    There is location left_bank.
                                                                                    There is item goose.
                                                                                    There is item fox.
                                                                                    There is item beans.
                                                                                    There is farmer 1.
                                                                                    Farmer 1 is at location left_bank.
                                                                                    Item beans is at location left_bank.
                                                                                    Item fox is at location left_bank.
                                                                                    Item goose is at location right_bank.
                                                                                    Item fox eat item goose.
                                                                                    Item goose eat item beans.
                                                                                    -- In the 3 state:
                                                                                    There is route with starting_location equal to right_bank, with arriving_location equal to left_bank.
                                                                                    There is route with starting_location equal to left_bank, with arriving_location equal to right_bank.
                                                                                    There is location right_bank.
                                                                                    There is location left_bank.
                                                                                    There is item goose.
                                                                                    There is item fox.
                                                                                    There is item beans.
                                                                                    There is farmer 1.
                                                                                    Farmer 1 is at location right_bank.
                                                                                    Item beans is at location left_bank.
                                                                                    Item goose is at location right_bank.
                                                                                    Item fox eat item goose.
                                                                                    Item goose eat item beans.
                                                                                    Item fox is moved.
                                                                                    Item fox is at location right_bank.
                                                                                    -- In the 4 state:
                                                                                    There is route with starting_location equal to right_bank, with arriving_location equal to left_bank.
                                                                                    There is route with starting_location equal to left_bank, with arriving_location equal to right_bank.
                                                                                    There is location right_bank.
                                                                                    There is location left_bank.
                                                                                    There is item goose.
                                                                                    There is item fox.
                                                                                    There is item beans.
                                                                                    There is farmer 1.
                                                                                    Item goose is moved.
                                                                                    Farmer 1 is at location left_bank.
                                                                                    Item beans is at location left_bank.
                                                                                    Item fox is at location right_bank.
                                                                                    Item goose is at location left_bank.
                                                                                    Item fox eat item goose.
                                                                                    Item goose eat item beans.
                                                                                    -- In the 5 state:
                                                                                    There is route with starting_location equal to right_bank, with arriving_location equal to left_bank.
                                                                                    There is route with starting_location equal to left_bank, with arriving_location equal to right_bank.
                                                                                    There is location right_bank.
                                                                                    There is location left_bank.
                                                                                    There is item goose.
                                                                                    There is item fox.
                                                                                    There is item beans.
                                                                                    There is farmer 1.
                                                                                    Farmer 1 is at location right_bank.
                                                                                    Item fox is at location right_bank.
                                                                                    Item goose is at location left_bank.
                                                                                    Item fox eat item goose.
                                                                                    Item goose eat item beans.
                                                                                    Item beans is moved.
                                                                                    Item beans is at location right_bank.
                                                                                    -- In the 6 state:
                                                                                    There is route with starting_location equal to right_bank, with arriving_location equal to left_bank.
                                                                                    There is route with starting_location equal to left_bank, with arriving_location equal to right_bank.
                                                                                    There is location right_bank.
                                                                                    There is location left_bank.
                                                                                    There is item goose.
                                                                                    There is item fox.
                                                                                    There is item beans.
                                                                                    There is farmer 1.
                                                                                    Farmer 1 is at location left_bank.
                                                                                    Item beans is at location right_bank.
                                                                                    Item fox is at location right_bank.
                                                                                    Item goose is at location left_bank.
                                                                                    Item fox eat item goose.
                                                                                    Item goose eat item beans.
                                                                                    -- In the 7 state:
                                                                                    There is route with starting_location equal to right_bank, with arriving_location equal to left_bank.
                                                                                    There is route with starting_location equal to left_bank, with arriving_location equal to right_bank.
                                                                                    There is location right_bank.
                                                                                    There is location left_bank.
                                                                                    There is item goose.
                                                                                    There is item fox.
                                                                                    There is item beans.
                                                                                    There is farmer 1.
                                                                                    Item goose is moved.
                                                                                    Farmer 1 is at location right_bank.
                                                                                    Item beans is at location right_bank.
                                                                                    Item fox is at location right_bank.
                                                                                    Item goose is at location right_bank.
                                                                                    Item fox eat item goose.
                                                                                    Item goose eat item beans.'''))

    def test_hanoi_problem(self):
        cnl = dedent('''\
                    A disk is identified by an id.
                    A peg is identified by an id.
                    A goal is identified by a disk, and by a peg.
                    
                    
                    The following propositions always apply:
                    There is a disk with id 0.
                    There is a disk with id 1.
                    There is a disk with id 3.
                    There is a disk with id 2.
                    
                    There is a peg with id 1.
                    There is a peg with id 2.
                    There is a peg with id 3.
                    
                    There is a goal with disk id 3, with peg 3.
                    There is a goal with disk id 2, with peg 3.
                    There is a goal with disk id 1, with peg 3.
                    
                    The following propositions apply in the initial state:
                    Disk X is on peg 1, where X is greater than 0.
                    
                    The following propositions always apply except in the initial state:
                    Whenever there is a disk D, then D can be moved to a peg.
                    It is required that the number of disks that are moved to a peg is equal to 1.
                    
                    A disk D is on a peg P when disk D is moved to peg P.
                    A disk D is moved when disk D is moved to a peg P.
                    A disk D is on a peg P when disk D is previously on peg P and also disk D is not moved.
                    
                    A disk X is blocked in peg P when disk D is previously on peg P, where X is equal to D-1.
                    A disk X is blocked in peg P when disk D is blocked in peg P, where X is equal to D-1.
                    
                    It is prohibited that a disk D is moved to a peg P, when a disk X is blocked in peg P, where X is equal to D-1.
                    It is prohibited that a disk D is moved to a peg P1, when disk D is previously on peg P2 and also disk D is blocked in peg P2.
                    //It is prohibited that the number of peg P where a disk D is on is different from 1, whenever there is a disk with id D greater than 0.
                    
                    The following propositions apply in the final state:
                    It is prohibited that disk D is not on peg P, whenever there is a goal with disk id D, with peg id P.''')
        answer_set = dedent('''\
                             State 0:
                              disk(0) disk(1) disk(2) disk(3)
                              peg(1) peg(2) peg(3)
                              goal(1,3) goal(2,3) goal(3,3)
                              on(1,1) on(2,1) on(3,1)
                             State 1:
                              disk(0) disk(1) disk(2) disk(3)
                              moved(3)
                              peg(1) peg(2) peg(3)
                              blocked_in(0,1) blocked_in(1,1) blocked_in(2,1)
                              goal(1,3) goal(2,3) goal(3,3)
                              moved_to(3,3)
                              on(1,1) on(2,1) on(3,3)
                             State 2:
                              disk(0) disk(1) disk(2) disk(3)
                              moved(2)
                              peg(1) peg(2) peg(3)
                              blocked_in(0,1) blocked_in(0,3) blocked_in(1,1) blocked_in(1,3) blocked_in(2,3)
                              goal(1,3) goal(2,3) goal(3,3)
                              moved_to(2,2)
                              on(1,1) on(2,2) on(3,3)
                             State 3:
                              disk(0) disk(1) disk(2) disk(3)
                              moved(3)
                              peg(1) peg(2) peg(3)
                              blocked_in(0,1) blocked_in(0,2) blocked_in(0,3) blocked_in(1,2) blocked_in(1,3) blocked_in(2,3)
                              goal(1,3) goal(2,3) goal(3,3)
                              moved_to(3,2)
                              on(1,1) on(2,2) on(3,2)
                             State 4:
                              disk(0) disk(1) disk(2) disk(3)
                              moved(1)
                              peg(1) peg(2) peg(3)
                              blocked_in(0,1) blocked_in(0,2) blocked_in(1,2) blocked_in(2,2)
                              goal(1,3) goal(2,3) goal(3,3)
                              moved_to(1,3)
                              on(1,3) on(2,2) on(3,2)
                             State 5:
                              disk(0) disk(1) disk(2) disk(3)
                              moved(3)
                              peg(1) peg(2) peg(3)
                              blocked_in(0,2) blocked_in(0,3) blocked_in(1,2) blocked_in(2,2)
                              goal(1,3) goal(2,3) goal(3,3)
                              moved_to(3,1)
                              on(1,3) on(2,2) on(3,1)
                             State 6:
                              disk(0) disk(1) disk(2) disk(3)
                              moved(2)
                              peg(1) peg(2) peg(3)
                              blocked_in(0,1) blocked_in(0,2) blocked_in(0,3) blocked_in(1,1) blocked_in(1,2) blocked_in(2,1)
                              goal(1,3) goal(2,3) goal(3,3)
                              moved_to(2,3)
                              on(1,3) on(2,3) on(3,1)
                             State 7:
                              disk(0) disk(1) disk(2) disk(3)
                              moved(3)
                              peg(1) peg(2) peg(3)
                              blocked_in(0,1) blocked_in(0,3) blocked_in(1,1) blocked_in(1,3) blocked_in(2,1)
                              goal(1,3) goal(2,3) goal(3,3)
                              moved_to(3,3)
                              on(1,3) on(2,3) on(3,3)''')
        self.assertEqual(self.compute_telingo_explaination(cnl, answer_set), dedent('''\
                                                                                    -- In the 0 state:
                                                                                    There is goal with disk id equal to 3, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 2, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 1, with peg id equal to 3.
                                                                                    There is peg 3.
                                                                                    There is peg 2.
                                                                                    There is peg 1.
                                                                                    There is disk 3.
                                                                                    There is disk 2.
                                                                                    There is disk 1.
                                                                                    There is disk 0.
                                                                                    Disk 1 is on peg 1.
                                                                                    Disk 2 is on peg 1.
                                                                                    Disk 3 is on peg 1.
                                                                                    -- In the 1 state:
                                                                                    There is goal with disk id equal to 3, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 2, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 1, with peg id equal to 3.
                                                                                    There is peg 3.
                                                                                    There is peg 2.
                                                                                    There is peg 1.
                                                                                    There is disk 3.
                                                                                    There is disk 2.
                                                                                    There is disk 1.
                                                                                    There is disk 0.
                                                                                    Disk 1 is on peg 1.
                                                                                    Disk 2 is on peg 1.
                                                                                    Disk 3 is moved.
                                                                                    Disk 0 is blocked in peg 1.
                                                                                    Disk 1 is blocked in peg 1.
                                                                                    Disk 2 is blocked in peg 1.
                                                                                    Disk 3 is moved to peg 3.
                                                                                    Disk 3 is on peg 3.
                                                                                    -- In the 2 state:
                                                                                    There is goal with disk id equal to 3, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 2, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 1, with peg id equal to 3.
                                                                                    There is peg 3.
                                                                                    There is peg 2.
                                                                                    There is peg 1.
                                                                                    There is disk 3.
                                                                                    There is disk 2.
                                                                                    There is disk 1.
                                                                                    There is disk 0.
                                                                                    Disk 0 is blocked in peg 1.
                                                                                    Disk 1 is blocked in peg 1.
                                                                                    Disk 1 is on peg 1.
                                                                                    Disk 3 is on peg 3.
                                                                                    Disk 2 is moved.
                                                                                    Disk 0 is blocked in peg 3.
                                                                                    Disk 1 is blocked in peg 3.
                                                                                    Disk 2 is blocked in peg 3.
                                                                                    Disk 2 is moved to peg 2.
                                                                                    Disk 2 is on peg 2.
                                                                                    -- In the 3 state:
                                                                                    There is goal with disk id equal to 3, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 2, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 1, with peg id equal to 3.
                                                                                    There is peg 3.
                                                                                    There is peg 2.
                                                                                    There is peg 1.
                                                                                    There is disk 3.
                                                                                    There is disk 2.
                                                                                    There is disk 1.
                                                                                    There is disk 0.
                                                                                    Disk 3 is moved.
                                                                                    Disk 0 is blocked in peg 1.
                                                                                    Disk 0 is blocked in peg 3.
                                                                                    Disk 1 is blocked in peg 3.
                                                                                    Disk 2 is blocked in peg 3.
                                                                                    Disk 1 is on peg 1.
                                                                                    Disk 2 is on peg 2.
                                                                                    Disk 0 is blocked in peg 2.
                                                                                    Disk 1 is blocked in peg 2.
                                                                                    Disk 3 is moved to peg 2.
                                                                                    Disk 3 is on peg 2.
                                                                                    -- In the 4 state:
                                                                                    There is goal with disk id equal to 3, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 2, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 1, with peg id equal to 3.
                                                                                    There is peg 3.
                                                                                    There is peg 2.
                                                                                    There is peg 1.
                                                                                    There is disk 3.
                                                                                    There is disk 2.
                                                                                    There is disk 1.
                                                                                    There is disk 0.
                                                                                    Disk 0 is blocked in peg 1.
                                                                                    Disk 0 is blocked in peg 2.
                                                                                    Disk 1 is blocked in peg 2.
                                                                                    Disk 2 is on peg 2.
                                                                                    Disk 3 is on peg 2.
                                                                                    Disk 1 is moved.
                                                                                    Disk 2 is blocked in peg 2.
                                                                                    Disk 1 is moved to peg 3.
                                                                                    Disk 1 is on peg 3.
                                                                                    -- In the 5 state:
                                                                                    There is goal with disk id equal to 3, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 2, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 1, with peg id equal to 3.
                                                                                    There is peg 3.
                                                                                    There is peg 2.
                                                                                    There is peg 1.
                                                                                    There is disk 3.
                                                                                    There is disk 2.
                                                                                    There is disk 1.
                                                                                    There is disk 0.
                                                                                    Disk 3 is moved.
                                                                                    Disk 0 is blocked in peg 2.
                                                                                    Disk 0 is blocked in peg 3.
                                                                                    Disk 1 is blocked in peg 2.
                                                                                    Disk 2 is blocked in peg 2.
                                                                                    Disk 1 is on peg 3.
                                                                                    Disk 2 is on peg 2.
                                                                                    Disk 3 is on peg 1.
                                                                                    Disk 3 is moved to peg 1.
                                                                                    -- In the 6 state:
                                                                                    There is goal with disk id equal to 3, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 2, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 1, with peg id equal to 3.
                                                                                    There is peg 3.
                                                                                    There is peg 2.
                                                                                    There is peg 1.
                                                                                    There is disk 3.
                                                                                    There is disk 2.
                                                                                    There is disk 1.
                                                                                    There is disk 0.
                                                                                    Disk 2 is moved.
                                                                                    Disk 0 is blocked in peg 1.
                                                                                    Disk 0 is blocked in peg 2.
                                                                                    Disk 0 is blocked in peg 3.
                                                                                    Disk 1 is blocked in peg 1.
                                                                                    Disk 1 is blocked in peg 2.
                                                                                    Disk 2 is blocked in peg 1.
                                                                                    Disk 1 is on peg 3.
                                                                                    Disk 3 is on peg 1.
                                                                                    Disk 2 is moved to peg 3.
                                                                                    Disk 2 is on peg 3.
                                                                                    -- In the 7 state:
                                                                                    There is goal with disk id equal to 3, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 2, with peg id equal to 3.
                                                                                    There is goal with disk id equal to 1, with peg id equal to 3.
                                                                                    There is peg 3.
                                                                                    There is peg 2.
                                                                                    There is peg 1.
                                                                                    There is disk 3.
                                                                                    There is disk 2.
                                                                                    There is disk 1.
                                                                                    There is disk 0.
                                                                                    Disk 3 is moved.
                                                                                    Disk 0 is blocked in peg 1.
                                                                                    Disk 0 is blocked in peg 3.
                                                                                    Disk 1 is blocked in peg 1.
                                                                                    Disk 1 is blocked in peg 3.
                                                                                    Disk 2 is blocked in peg 1.
                                                                                    Disk 3 is moved to peg 3.
                                                                                    Disk 1 is on peg 3.
                                                                                    Disk 2 is on peg 3.
                                                                                    Disk 3 is on peg 3.'''))
