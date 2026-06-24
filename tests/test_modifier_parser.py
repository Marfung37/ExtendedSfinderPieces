import pytest
from lib.modifier_parser import Parser, BeforeLiteral, evaluate_before, evaluate_ast

parser = Parser()


@pytest.mark.parametrize(
  "expression, expected",
  [
    ("T=1", "Count(['T'] = 1)"),
    ("T!=1", "Count(['T'] != 1)"),
    ("T>1", "Count(['T'] > 1)"),
    ("T<1", "Count(['T'] < 1)"),
    ("T>=1", "Count(['T'] >= 1)"),
    ("T<=1", "Count(['T'] <= 1)"),
    ("1:T=1", "Range(0-1 -> Count(['T'] = 1))"),
    ("1-2:T=1", "Range(1-2 -> Count(['T'] = 1))"),
    ("/^T/", "Regex(`^T`)"),
    ("1:/^T/", "Range(0-1 -> Regex(`^T`))"),
    ("[LJ]=1&&!LJ=1", "(Count([['L', 'J']] = 1) AND (NOT Count(['L', 'J'] = 1)))"),
    (
      "([LJ]=1&&!LJ=1)||LJ=0",
      "((Count([['L', 'J']] = 1) AND (NOT Count(['L', 'J'] = 1))) OR Count(['L', 'J'] = 0))",
    ),
  ],
)
def test_ast_parse(expression, expected):
  print(str(parser.parse(expression)))
  assert str(parser.parse(expression)) == expected


@pytest.mark.parametrize(
  "node, queue, expected",
  [
    (BeforeLiteral(["T"], ["I"]), "TI", True),
    (BeforeLiteral(["T"], ["I"]), "IT", False),
    (BeforeLiteral(["I"], ["T"]), "TI", False),
    (BeforeLiteral(["I"], ["T"]), "IT", True),
    (BeforeLiteral(["T"], ["I"]), "II", False),
    (BeforeLiteral(["I"], ["T"]), "II", True),
    (BeforeLiteral(["T", ["S", "Z"]], ["I"]), "TSI", True),
    (BeforeLiteral(["T", ["S", "Z"]], ["I"]), "TSZI", True),
    (BeforeLiteral(["T", ["S", "Z"]], ["I"]), "TSIZ", True),
    (BeforeLiteral(["T", ["S", "Z"]], ["I"]), "TISZ", False),
    (BeforeLiteral(["T", ["S", "Z"]], ["I"]), "SZIT", False),
    (BeforeLiteral(["T", ["S", "Z"]], ["I"]), "SIZT", False),
    (BeforeLiteral(["T"], ["I", ["S", "Z"]]), "TSI", True),
    (BeforeLiteral(["T"], ["I", ["S", "Z"]]), "TSZI", True),
    (BeforeLiteral(["T"], ["I", ["S", "Z"]]), "TSIZ", True),
    (BeforeLiteral(["T"], ["I", ["S", "Z"]]), "STZI", True),
    (BeforeLiteral(["T"], ["I", ["S", "Z"]]), "SZIT", False),
    (BeforeLiteral(["T"], ["I", ["S", "Z"]]), "SITZ", False),
    (BeforeLiteral(["T"], ["I", ["S", "Z"]]), "SZTI", False),
    (BeforeLiteral(["T", ["L", "J"]], ["I", ["S", "Z"]]), "TLJISZ", True),
    (BeforeLiteral(["T", ["L", "J"]], ["I", ["S", "Z"]]), "TLIS", True),
    (BeforeLiteral(["T", ["L", "J"]], ["I", ["S", "Z"]]), "LITS", False),
    (BeforeLiteral(["T", ["L", "J"]], ["I", ["S", "Z"]]), "JITS", False),
    (BeforeLiteral(["T", ["L", "J"]], ["I", ["S", "Z"]]), "TLSJIZ", True),
    (BeforeLiteral(["T", ["L", "J"]], ["I", ["S", "Z"]]), "TJZILS", True),
    (BeforeLiteral(["I", "I"], ["T"]), "IIT", True),
    (BeforeLiteral(["I", "I"], ["T"]), "II", True),
    (BeforeLiteral(["I", "I"], ["T"]), "IITI", True),
    (BeforeLiteral(["I", "I"], ["T"]), "ITII", False),
    (BeforeLiteral(["I", "I"], ["T"]), "ILIT", True),
    (BeforeLiteral(["I", "I"], ["T"]), "ITI", False),
    (BeforeLiteral(["T"], ["I", ["I", "S"]]), "TII", True),
    (BeforeLiteral(["T"], ["I", ["I", "S"]]), "TIS", True),
    (BeforeLiteral(["T"], ["I", ["I", "S"]]), "TIZ", True),
    (BeforeLiteral(["T"], ["I", ["I", "S"]]), "IT", False),
  ],
)
def test_evaluate_before(node: BeforeLiteral, queue: str, expected: bool):
  assert evaluate_before(node, queue) == expected


@pytest.mark.parametrize(
  "expression, queue_str, expected",
  [
    # count modifier
    ("T=0", "IIII", True),
    ("T=0", "IITI", False),
    ("T=1", "TIII", True),
    ("T=1", "ITII", True),
    ("T=1", "IIIT", True),
    ("T=1", "ITIT", False),
    ("T=1", "TTIT", False),
    ("T=2", "ITIT", True),
    ("T=2", "TTIT", False),
    ("T=3", "TTIT", True),
    ("T=3", "TTIT", True),
    ("T>0", "TIII", True),
    ("T>0", "TITI", True),
    ("T>0", "ITTT", True),
    ("T>0", "TTTT", True),
    ("T>0", "IIII", False),
    ("T<1", "IIII", True),
    ("T<1", "ITII", False),
    ("T<1", "ITIT", False),
    ("T<=1", "ITIT", False),
    ("T<=1", "IIIT", True),
    ("T<=1", "IIII", True),
    ("T>=1", "IIII", False),
    ("T>=1", "ITII", True),
    ("T>=1", "ITTT", True),
    ("T!=1", "IIII", True),
    ("T!=1", "ITTI", True),
    ("T!=1", "TTTT", True),
    ("T!=1", "IIIT", False),
    # test range modifier
    ("4:(T=1)", "TIII", True),
    ("4:(T=1)", "IIIIT", False),  # T is at index 4 (outside range 0-4)
    ("3-7:(T=1)", "IIITIII", True),  # T is within index 3 to 7
    ("3-7:(T=1)", "TIIIIII", False),  # T is before index 3
  ],
)
def test_evaluate_ast(expression, queue_str, expected):
  ast = parser.parse(expression)
  assert evaluate_ast(ast, queue_str) == expected
