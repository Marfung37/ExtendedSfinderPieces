import pytest
from sfinder_pieces.parser import Parser
from sfinder_pieces.sfinder_pieces import sfinder_pieces, sfinder_pieces_random_choice
from math import comb, perm

parser = Parser()


@pytest.mark.parametrize(
  "expression, expected_length",
  [
    # check if same as generator directly
    ("T", 1),
    ("I", 1),
    ("L", 1),
    ("J", 1),
    ("S", 1),
    ("Z", 1),
    ("O", 1),
    ("*", 7),
    ("[TS]", 2),
    ("[LSO]", 3),
    ("[TT]", 1),
    ("[TTI]", 2),
    ("[TS]!", 2),
    ("[LSO]!", 6),
    ("[LSO]p2", 6),
    ("*p2", perm(7, 2)),
    ("*p7", perm(7)),
    ("[[TS]]", 2),
    ("[I[TS]]", 3),
    ("[T[TS]]", 2),
    ("[T[TS]]p2", 3),
    # multiple generator expressions
    ("**", 49),
    ("*p7*p3", perm(7) * perm(7, 3)),
    ("*,*", 49),
    ("*p7,*p3", perm(7) * perm(7, 3)),
    ("[TL]![LJ]!", 4),
    ("[TL[SZ]]![LJ[SZ]]!", perm(3) * 2 * perm(3) * 2),
    # filter expressions
    ("*p4{T=1}", comb(6, 3) * perm(4)),
    ("*,*p4{T=1}", 7 * comb(6, 3) * perm(4)),
    ("**p4{T=1}", comb(6, 4) * perm(4) + 6 * comb(6, 3) * perm(4)),
    ("[IL]!{T=1}", 0),
    ("[TIL]!{1-3:T=1}", perm(3) - perm(2)),  # T not first
    ("[TIL]!{/^T/}", perm(2)),  # T first
    ("[ILLS]!{LL<I}", 4),
    ("[TISZ]!{T[SZ]<I}", 10),
    ("*p2*p2{[*]=2}", 924),
    ("*p4{T<I[SZ]}", 334),
    ("*p4{T[LJ]<I[SZ]}", 250),
    # some expressions from database
    ("*p7{!(IO<LJ||/[TO]$/||/T[LJ]$/)}", 2720),
    ("[LSZO]!{L<Z||LZ<S},[TIJ]!,*p3{!I[LJ][ZO]=1||(IJZ=1&&/^J/)}", 18048),
    ("[SZ]!,*p4{JSZO=1&&(/^SJ/||/^J.?S/||/^.JS/)}", 16),
    ("[LJSZ]!{2:LZ=1||3:LSZ=1||L<Z},[TIO]!,[^TIO]!{L<Z&&LZ<J}", 384),
  ],
)
def test_evaluate_sfinder_pieces(expression, expected_length):
  assert len(tuple(sfinder_pieces(expression))) == expected_length
