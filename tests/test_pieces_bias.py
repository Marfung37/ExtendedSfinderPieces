import pytest
import random
import sys
from sfinder_pieces.sfinder_pieces import (
  parse_pattern,
  sfinder_pieces,
  random_sfinder_pieces,
)
from collections import Counter
from scipy.stats import chisquare


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


N_RUNS = 500_000
SIGNIFICANCE_VALUE = 0.001


@pytest.mark.parametrize(
  "expression",
  [("*"), ("[TTO]!"), ("[TTII]p2"), ("[T[SZ]]!"), ("[T[TSZ]]!"), ("[T[TSZ][TSZ]]!")],
)
def test_bias_random_sfinder_pieces(expression):
  parsed_pattern = parse_pattern(expression)
  queues = tuple(sfinder_pieces(parsed_pattern))

  # get expected number counts for uniform distribution
  expected_counts = [N_RUNS / len(queues)] * len(queues)

  # get observed counts from the function
  results = [random_sfinder_pieces(parsed_pattern) for _ in range(N_RUNS)]
  counts = Counter(results)
  observed_counts = list(counts.values())

  _, p_value = chisquare(f_obs=observed_counts, f_exp=expected_counts)

  assert p_value >= SIGNIFICANCE_VALUE
