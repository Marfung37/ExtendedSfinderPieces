import pytest
import random
import sys
from sfinder_pieces.sfinder_pieces import sfinder_pieces, random_sfinder_pieces
from math import comb, perm, ceil


# helpful function to give seed of random if test fails
@pytest.fixture(autouse=True)
def automatically_seed_random():
  # Generate a random seed for this run
  seed = random.randint(0, sys.maxsize)
  random.seed(seed)

  # This yields control to the test function
  yield

  # If you run pytest with `-s`, this will always print.
  # Otherwise, pytest will only show this stdout if the test FAILS.
  print(f"\n--- RANDOM SEED USED FOR THIS RUN: {seed} ---")


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
    ("T;I", 2),
    ("[TIL]p2;[SZO]p2", perm(3, 2) + perm(3, 2)),
    # filter expressions
    ("*p4{T=1}", comb(6, 3) * perm(4)),
    ("*,*p4{T=1}", 7 * comb(6, 3) * perm(4)),
    ("**p4{T=1}", comb(6, 4) * perm(4) + 6 * comb(6, 3) * perm(4)),
    ("[IL]!{T=1}", 0),
    ("[TIL]!{1-3:T=1}", perm(3) - perm(2)),  # T not first
    ("[TIL]!{/^T/}", perm(2)),  # T first
    ("[TIL]!{1-3:T=1};[TIL]!{/^T/}", perm(3)),
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


SAMPLE_RATIO = 1 / 10


@pytest.mark.parametrize(
  "expression",
  [
    # check if same as generator directly
    ("T"),
    ("I"),
    ("L"),
    ("J"),
    ("S"),
    ("Z"),
    ("O"),
    ("*"),
    ("[TS]"),
    ("[LSO]"),
    ("[TT]"),
    ("[TTI]"),
    ("[TS]!"),
    ("[LSO]!"),
    ("[LSO]p2"),
    ("*p2"),
    ("*p7"),
    ("[[TS]]"),
    ("[I[TS]]"),
    ("[T[TS]]"),
    ("[T[TS]]p2"),
    # multiple generator expressions
    ("**"),
    ("*p7*p3"),
    ("*,*"),
    ("*p7,*p3"),
    ("[TL]![LJ]!"),
    ("[TL[SZ]]![LJ[SZ]]!"),
    ("T;I"),
    # filter expressions
    ("*p4{T=1}"),
    ("*,*p4{T=1}"),
    ("**p4{T=1}"),
    ("[IL]!{T=1}"),
    ("[TIL]!{1-3:T=1}"),  # T not first
    ("[TIL]!{/^T/}"),  # T first
    ("[TIL]!{1-3:T=1};[TIL]!{/^T/}"),
    ("[ILLS]!{LL<I}"),
    ("[TISZ]!{T[SZ]<I}"),
    ("*p2*p2{[*]=2}"),
    ("*p4{T<I[SZ]}"),
    ("*p4{T[LJ]<I[SZ]}"),
    # some expressions from database
    ("*p7{!(IO<LJ||/[TO]$/||/T[LJ]$/)}"),
    ("[LSZO]!{L<Z||LZ<S},[TIJ]!,*p3{!I[LJ][ZO]=1||(IJZ=1&&/^J/)}"),
    ("[SZ]!,*p4{JSZO=1&&(/^SJ/||/^J.?S/||/^.JS/)}"),
    ("[LJSZ]!{2:LZ=1||3:LSZ=1||L<Z},[TIO]!,[^TIO]!{L<Z&&LZ<J}"),
  ],
)
def test_evaluate_random_sfinder_pieces(expression):
  all_queues = set(sfinder_pieces(expression))

  if len(all_queues) == 0:
    assert random_sfinder_pieces(expression) is None
    return

  # use a bounded sample size within min(5, max length of queues)-50
  samples = min(max(min(5, len(all_queues)), ceil(SAMPLE_RATIO * len(all_queues))), 50)
  for _ in range(samples):
    assert random_sfinder_pieces(expression) in all_queues
