from .parser import Parser, GeneratorLiteral, FilterBlock
from .evaluate_generator import evaluate_generator
from .evaluate_filter import evaluate_filter
from collections.abc import Iterator
from itertools import product, chain
import random


parser = Parser()


def clean_product(*args: Iterator[str]) -> Iterator[str]:
  return ("".join(part) for part in product(*args))


def evaluate_blocks(blocks: list[GeneratorLiteral | FilterBlock]) -> Iterator[str]:
  running_iterators: list[Iterator[str]] = []
  for block in blocks:
    match block:
      case GeneratorLiteral():
        running_iterators.append(iter(evaluate_generator(block)))
      case FilterBlock(expr=expr):

        def filter_func(queue):
          return evaluate_filter(expr, queue)

        running_iterators = [filter(filter_func, clean_product(*running_iterators))]

  # cannot end with GeneratorLiteral so running iterators should only contain one element
  return running_iterators[0]


def parse_pattern(pattern: str) -> list[list[list[GeneratorLiteral | FilterBlock]]]:
  """Parses a given pattern into layered list for patterns to be appended together, patterns to be product together, individual blocks in AST"""
  # can list separate patterns together using semicolons to just append on
  patterns = pattern.split(";")
  parsed = []
  for pattern in patterns:
    # separate into parts where filter will apply
    parts = pattern.split(",")

    # parse everything and put in parsed
    all_blocks = []
    for part in parts:
      blocks = parser.parse(part)

      # starting with filter will just be removed as not filtering anything
      while isinstance(blocks[0], FilterBlock):
        blocks = blocks[1:]

      # GeneratorLiterals at the end can be own separate 'blocks'
      all_blocks_initial_end = len(all_blocks)
      while len(blocks) > 0 and isinstance(blocks[-1], GeneratorLiteral):
        all_blocks.insert(all_blocks_initial_end, [blocks.pop()])

      if len(blocks) > 0:
        all_blocks.insert(all_blocks_initial_end, blocks)

    parsed.append(all_blocks)

  return parsed


def sfinder_pieces(pattern: str) -> Iterator[str]:
  running_parts: list[Iterator[str]] = []
  parsed_pattern = parse_pattern(pattern)

  for appending_parts in parsed_pattern:
    running_iterators: list[Iterator[str]] = []
    for blocks in appending_parts:
      running_iterators.append(evaluate_blocks(blocks))

    running_parts.append(clean_product(*running_iterators))

  return chain(*running_parts)


def sfinder_pieces_random_choice(pattern: str) -> str:
  # gets one of the possible queues with uniform randomness
  parsed_pattern = parse_pattern(pattern)

  weights: list[int] = []
  choices: list[str] = []  # choice for each part
  for appending_parts in parsed_pattern:
    weight = 1
    queue_choice = ""
    for blocks in appending_parts:
      evaluated_blocks = tuple(evaluate_blocks(blocks))
      weight *= len(evaluated_blocks)
      queue_choice += random.choice(evaluated_blocks)

    weights.append(weight)
    choices.append(queue_choice)

  return random.choices(choices, weights=weights)[0]


print("\n".join(list(sfinder_pieces("*p4{T[LJ]<I[SZ]}"))))
