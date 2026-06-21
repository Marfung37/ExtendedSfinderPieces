import pytest
from lib.modifier_parser import Parser, evaluate_before, evaluate_ast

parser = Parser()

@pytest.mark.parametrize("expression, expected", [
  ("T=1",  "Count(['T'] = 1)"),
  ("T!=1", "Count(['T'] != 1)"),
  ("T>1",  "Count(['T'] > 1)"),
  ("T<1",  "Count(['T'] < 1)"),
  ("T>=1", "Count(['T'] >= 1)"),
  ("T<=1", "Count(['T'] <= 1)"),
  ("1:T=1", "Range(0-1 -> Count(['T'] = 1))"),
  ("1-2:T=1", "Range(1-2 -> Count(['T'] = 1))"),
  ("/^T/", "Regex(`^T`)"),
  ("1:/^T/", "Range(0-1 -> Regex(`^T`))"),
  ("[LJ]=1&&!LJ=1", "(Count([['L', 'J']] = 1) AND (NOT Count(['L', 'J'] = 1)))"),
  ("([LJ]=1&&!LJ=1)||LJ=0", "((Count([['L', 'J']] = 1) AND (NOT Count(['L', 'J'] = 1))) OR Count(['L', 'J'] = 0))"),
])
def test_ast_parse(expression, expected):
  print(str(parser.parse(expression)))
  assert str(parser.parse(expression)) == expected

@pytest.mark.parametrize("expression, queue_str, expected", [
  ("4:(T=1)", "TIII", True),
  ("4:(T=1)", "IIIIT", False),        # T is at index 4 (outside range 0-4)
  ("3-7:(T=1)", "IIITIII", True),     # T is within index 3 to 7
  ("3-7:(T=1)", "TIIIIII", False),    # T is before index 3
])
def test_range_lookups(expression, queue_str, expected):
  ast = parser.parse(expression)
  assert evaluate_ast(ast, queue_str) == expected
