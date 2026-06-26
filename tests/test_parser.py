import pytest
from lib.parser import Parser

parser = Parser()


@pytest.mark.parametrize(
  "expression, expected",
  [
    ("{T=1}", "Filter(Count(['T'] = 1))"),
    ("{T!=1}", "Filter(Count(['T'] != 1))"),
    ("{T>1}", "Filter(Count(['T'] > 1))"),
    ("{T<1}", "Filter(Count(['T'] < 1))"),
    ("{T>=1}", "Filter(Count(['T'] >= 1))"),
    ("{T<=1}", "Filter(Count(['T'] <= 1))"),
    ("{1:T=1}", "Filter(Range(0-1 -> Count(['T'] = 1)))"),
    ("{1-2:T=1}", "Filter(Range(1-2 -> Count(['T'] = 1)))"),
    ("{/^T/}", "Filter(Regex(`^T`))"),
    ("{1:/^T/}", "Filter(Range(0-1 -> Regex(`^T`)))"),
    (
      "{[LJ]=1&&!LJ=1}",
      "Filter((Count([['L', 'J']] = 1) AND (NOT Count(['L', 'J'] = 1))))",
    ),
    (
      "{([LJ]=1&&!LJ=1)||LJ=0}",
      "Filter(((Count([['L', 'J']] = 1) AND (NOT Count(['L', 'J'] = 1))) OR Count(['L', 'J'] = 0)))",
    ),
  ],
)
def test_ast_parse(expression, expected):
  assert str(parser.parse(expression)[0]) == expected
