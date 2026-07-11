import pytest
import random
import sys
from sfinder_pieces.sfinder_pieces import sfinder_pieces, random_sfinder_pieces
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
SIGNIFICANCE_VALUE = 0.05


@pytest.mark.parametrize("expression", [("*"), ("[TTO]!"), ("[TTII]p2")])
def test_bias_random_sfinder_pieces(expression):
  queues = tuple(sfinder_pieces(expression))

  # get expected number counts for uniform distribution
  expected_counts = [N_RUNS / len(queues)] * len(queues)

  # get observed counts from the function
  results = [random_sfinder_pieces(expression) for _ in range(N_RUNS)]
  counts = Counter(results)
  observed_counts = list(counts.values())

  _, p_value = chisquare(f_obs=observed_counts, f_exp=expected_counts)

  assert p_value >= SIGNIFICANCE_VALUE
