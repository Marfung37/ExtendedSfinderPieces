import pytest
from sfinder_pieces.parser import Parser

parser = Parser()


@pytest.mark.parametrize(
  "expression, expected",
  [
    # generator expressions
    ("*", "Generator(['T', 'I', 'L', 'J', 'S', 'Z', 'O']p1)"),
    ("[TILJSZO]", "Generator(['T', 'I', 'L', 'J', 'S', 'Z', 'O']p1)"),
    ("[TI]", "Generator(['T', 'I']p1)"),
    ("[SIJ]", "Generator(['I', 'J', 'S']p1)"),
    ("*p2", "Generator(['T', 'I', 'L', 'J', 'S', 'Z', 'O']p2)"),
    ("*p6", "Generator(['T', 'I', 'L', 'J', 'S', 'Z', 'O']p6)"),
    ("*!", "Generator(['T', 'I', 'L', 'J', 'S', 'Z', 'O']p7)"),
    ("[TI]p2", "Generator(['T', 'I']p2)"),
    ("[TI]!", "Generator(['T', 'I']p2)"),
    ("[SIJ]p2", "Generator(['I', 'J', 'S']p2)"),
    ("[SIJ]!", "Generator(['I', 'J', 'S']p3)"),
    ("[TTI]", "Generator(['T', 'T', 'I']p1)"),
    ("[TTI]!", "Generator(['T', 'T', 'I']p3)"),
    ("[ITT]!", "Generator(['T', 'T', 'I']p3)"),
    ("[^TIJ]", "Generator(['L', 'S', 'Z', 'O']p1)"),
    ("[^TIJ]!", "Generator(['L', 'S', 'Z', 'O']p4)"),
    ("[^JTI]!", "Generator(['L', 'S', 'Z', 'O']p4)"),
    ("[L[SZ]]", "Generator(['L', ['S', 'Z']]p1)"),
    ("[L[SZ]]!", "Generator(['L', ['S', 'Z']]p2)"),
    ("[[TI]L[SZ]]!", "Generator(['L', ['T', 'I'], ['S', 'Z']]p3)"),
    ("[L[^SZ]]!", "Generator(['L', ['T', 'I', 'L', 'J', 'O']]p2)"),
    ("[^TI[LJ]]!", "Generator(['L', 'J', 'S', 'Z', 'O', ['L', 'J']]p6)"),
    ("[^TILJSZ[O]]!", "Generator(['O', ['O']]p2)"),
    (
      "[^TIJ[^LJO]]!",
      "Generator(['L', 'S', 'Z', 'O', ['T', 'I', 'S', 'Z']]p5)",
    ),
    ("[^TILJSZ[^O]]!", "Generator(['O', ['T', 'I', 'L', 'J', 'S', 'Z']]p2)"),
    # filter expressions
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
def test_ast_parse_part(expression, expected):
  assert str(parser.parse(expression)[0]) == expected


@pytest.mark.parametrize(
  "expression",
  [
    # generator invalid expressions
    ("[T]p2"),
    ("*p8"),
    ("[t]"),
    ("[I"),
    ("I]"),
    ("[^^O]"),
    ("[SZJJ]p0"),
    ("[T]p"),
    ("*p"),
    ("abdfa[T]"),
    ("[Tabdfa]"),
    # filter invalid expressions
    ("{1=1}"),
    ("{1=T}"),
    ("{T=T}"),
    ("{T>I}"),
    ("{3>I}"),
    ("{1-:T=1}"),
    ("{-2:T=1}"),
    ("{/abc}"),
    ("{abc/}"),
    ("{[[[T]]]=1}"),
    ("{T=1&L=1}"),
    ("{T=1{}I=1}"),
    ("{T=1{I=1}"),
    ("{T=1    I=1}"),
  ],
)
def test_ast_parse_error(expression):
  with pytest.raises(ValueError):
    parser.parse(expression)


@pytest.mark.parametrize(
  "expression, expected",
  [
    (
      "**",
      "[Generator(['T', 'I', 'L', 'J', 'S', 'Z', 'O']p1), Generator(['T', 'I', 'L', 'J', 'S', 'Z', 'O']p1)]",
    ),
    ("{T=1}{L=1}", "[Filter(Count(['T'] = 1)), Filter(Count(['L'] = 1))]"),
    ("[TIL]p2{L=1}", "[Generator(['T', 'I', 'L']p2), Filter(Count(['L'] = 1))]"),
  ],
)
def test_ast_parse(expression, expected):
  assert str(parser.parse(expression)) == expected
