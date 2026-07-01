import pytest
from sfinder_pieces.parser import Parser, FilterBlock
from sfinder_pieces.evaluate_filter import evaluate_filter
from typing import cast

parser = Parser()


@pytest.mark.parametrize(
  "expression, queue_str, expected",
  [
    # count modifier
    ("{T=0}", "IIII", True),
    ("{T=0}", "IITI", False),
    ("{T=1}", "TIII", True),
    ("{T=1}", "ITII", True),
    ("{T=1}", "IIIT", True),
    ("{T=1}", "ITIT", False),
    ("{T=1}", "TTIT", False),
    ("{T=2}", "ITIT", True),
    ("{T=2}", "TTIT", False),
    ("{T=3}", "TTIT", True),
    ("{T=3}", "TTIT", True),
    ("{T>0}", "TIII", True),
    ("{T>0}", "TITI", True),
    ("{T>0}", "ITTT", True),
    ("{T>0}", "TTTT", True),
    ("{T>0}", "IIII", False),
    ("{T<1}", "IIII", True),
    ("{T<1}", "ITII", False),
    ("{T<1}", "ITIT", False),
    ("{T<=1}", "ITIT", False),
    ("{T<=1}", "IIIT", True),
    ("{T<=1}", "IIII", True),
    ("{T>=1}", "IIII", False),
    ("{T>=1}", "ITII", True),
    ("{T>=1}", "ITTT", True),
    ("{T!=1}", "IIII", True),
    ("{T!=1}", "ITTI", True),
    ("{T!=1}", "TTTT", True),
    ("{T!=1}", "IIIT", False),
    ("{T[LJ]=1}", "TLJ", True),
    ("{T[LJ]=1}", "JTI", True),
    ("{T[LJ]=1}", "TLI", True),
    ("{T[LJ]=1}", "ITS", False),
    ("{*=1}", "TILJSZO", True),
    ("{*=1}", "TILJJSZO", False),
    ("{*=1}", "TILJZO", False),
    ("{*>=1}", "TILJJSZO", True),
    ("{[*]=2}", "TT", True),
    ("{[*]=2}", "II", True),
    ("{[*]=2}", "SS", True),
    ("{[*]=2}", "LL", True),
    ("{[*]=2}", "OO", True),
    ("{[*]=2}", "TILJS", False),
    ("{[*]=2}", "LJSZO", False),
    # before modifier
    ("{T<I}", "TI", True),
    ("{T<I}", "IT", False),
    ("{I<T}", "TI", False),
    ("{I<T}", "IT", True),
    ("{T<I}", "II", False),
    ("{I<T}", "II", True),
    ("{T[SZ]<I}", "TSI", True),
    ("{T[SZ]<I}", "TSZI", True),
    ("{T[SZ]<I}", "TSIZ", True),
    ("{T[SZ]<I}", "TISZ", False),
    ("{T[SZ]<I}", "SZIT", False),
    ("{T[SZ]<I}", "SIZT", False),
    ("{T<I[SZ]}", "TSI", True),
    ("{T<I[SZ]}", "TSZI", True),
    ("{T<I[SZ]}", "TSIZ", True),
    ("{T<I[SZ]}", "STZI", True),
    ("{T<I[SZ]}", "SZIT", False),
    ("{T<I[SZ]}", "SITZ", False),
    ("{T<I[SZ]}", "SZTI", False),
    ("{T[LJ]<I[SZ]}", "TLJISZ", True),
    ("{T[LJ]<I[SZ]}", "TLIS", True),
    ("{T[LJ]<I[SZ]}", "LITS", False),
    ("{T[LJ]<I[SZ]}", "JITS", False),
    ("{T[LJ]<I[SZ]}", "TLSJIZ", True),
    ("{T[LJ]<I[SZ]}", "TJZILS", True),
    ("{II<T}", "IIT", True),
    ("{II<T}", "II", True),
    ("{II<T}", "IITI", True),
    ("{II<T}", "ITII", False),
    ("{II<T}", "ILIT", True),
    ("{II<T}", "ITI", False),
    ("{T<I[IS]}", "TII", True),
    ("{T<I[IS]}", "TIS", True),
    ("{T<I[IS]}", "TIZ", True),
    ("{T<I[IS]}", "IT", False),
    ("{T<I[SZ]}", "LZOJ", False),
    # regex modifier, mostly need to just check if can parse regex and evaluate it
    ("{/^T/}", "TIL", True),
    ("{/^T/}", "TSZ", True),
    ("{/^T/}", "ITL", False),
    ("{/^T/}", "LIT", False),
    # test range modifier
    ("{4:T=1}", "TIII", True),
    ("{4:T=1}", "IIIIT", False),  # T is at index 4 (outside range 0-4)
    ("{4:(T=1&&S=1)}", "IISIT", False),  # T is out of range
    ("{4:(T=1&&S=1)}", "IITIS", False),  # S is out of range
    ("{4:(T=1&&S=1)}", "ITSII", True),  # both S and T within first 4
    ("{3-7:T=1}", "IIITIII", True),  # T is within index 3 to 7
    ("{3-7:T=1}", "TIIIIII", False),  # T is before index 3
    ("{3-7:(T=1&&S=1)}", "IISITIISI", False),  # S is out of range
    ("{3-7:(T=1&&S=1)}", "IITISIIII", False),  # T is out of range
    ("{3-7:(T=1&&S=1)}", "IITISTIII", True),  # both S and T within range
    # basic boolean logic works
    ("{[LJ]=1&&!LJ=1}", "LJ", False),
    ("{[LJ]=1&&!LJ=1}", "LI", True),
    ("{[LJ]=1&&!LJ=1}", "IJ", True),
    ("{[LJ]=1&&!LJ=1}", "IS", False),
    ("{([LJ]=1&&!LJ=1)||LJ=0}", "LJ", False),
    ("{([LJ]=1&&!LJ=1)||LJ=0}", "LI", True),
    ("{([LJ]=1&&!LJ=1)||LJ=0}", "IJ", True),
    ("{([LJ]=1&&!LJ=1)||LJ=0}", "IS", True),
  ],
)
def test_evaluate_filter(expression, queue_str, expected):
  ast = parser.parse(expression)
  assert evaluate_filter(cast(FilterBlock, ast[0]).expr, queue_str) == expected
