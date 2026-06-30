from itertools import product, permutations, chain
from .parser import GeneratorLiteral
from .utils import tetris_order_key
from math import perm
import random


def evaluate_generator(node: GeneratorLiteral) -> list[str]:
  # get all possible pools
  pools = product(*node.pool)

  # get permutations for each pool
  raw_perms = (permutations(pool, node.permute) for pool in pools)

  # flatten into strings
  queues = (
    "".join(chain.from_iterable(pool_perm))
    for pool_perms in raw_perms
    for pool_perm in pool_perms
  )

  # sort and remove duplicates
  return sorted(set(queues), key=tetris_order_key)


def sampleable_generator(node: GeneratorLiteral) -> bool:
  # determines if given node can use the faster random_evaluate_generator to get a random queue
  # if all pieces are unique in pool then valid

  # flatten pool
  flat_pool = [piece for part in node.pool for piece in part]
  return len(flat_pool) == len(set(flat_pool))


def random_evaluate_generator(node: GeneratorLiteral) -> str:
  # gives a random element and computes total number of possible queues
  # correct if no duplicates in pool as otherwise can be biased
  pools = list(product(*node.pool))

  pool = random.choice(pools)

  return "".join(random.sample(pool, node.permute))


def total_queues(node: GeneratorLiteral) -> int:
  # assumes passes sampleable_generator
  # computes the total number possible queues
  return perm(len(node.pool), node.permute)
