from itertools import product, permutations, chain
from .parser import GeneratorLiteral
from .utils import tetris_order_key


def evaluate_generator(node: GeneratorLiteral) -> list[str]:
  # get all possible pools
  pools = product(*node.pool)

  # get permutations for each pool
  raw_perms = (permutations(pool, node.permutate) for pool in pools)

  # flatten into strings
  queues = (
    "".join(chain.from_iterable(perm))
    for pool_perms in raw_perms
    for perm in pool_perms
  )

  # sort and remove duplicates
  return sorted(set(queues), key=tetris_order_key)
