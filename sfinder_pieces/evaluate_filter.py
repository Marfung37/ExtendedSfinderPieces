import operator
import re
from .parser import (
  AST,
  BinaryOp,
  UnaryOp,
  RangeLookup,
  CountLiteral,
  BeforeLiteral,
  RegexLiteral,
)
from .utils import PIECE_ORDER
from dataclasses import dataclass

OPERATORS = {
  "=": operator.eq,
  "!=": operator.ne,
  "<": operator.lt,
  ">": operator.gt,
  "<=": operator.le,
  ">=": operator.ge,
}


@dataclass
class BeforeInterationNode:
  before_pieces_count: list[int]
  after_pieces_count: list[int]
  before_index: int
  after_index: int


def get_char_indices(queue: str) -> list[list[int]]:
  """
  Builds a map of character positions
  e.g., "ISIJ" -> [[], [0, 2], [], [3], [1], [], []]
  """
  positions = [[] for _ in range(7)]
  for index, char in enumerate(queue.encode()):
    positions[PIECE_ORDER[char]].append(index)
  return positions


def evaluate_before(node: BeforeLiteral, queue: str) -> bool:
  # get index of each piece
  pos_map = get_char_indices(queue)

  # slight optimization to reduce overhead of ord function
  before_pieces = [before_piece.encode() for before_piece in node.before_pieces]
  after_pieces = [after_piece.encode() for after_piece in node.after_pieces]

  stack: list[BeforeInterationNode] = []
  stack.append(BeforeInterationNode([0] * 7, [0] * 7, 0, 0))

  while len(stack) > 0:
    stack_node = stack.pop()

    if stack_node.before_index == len(node.before_pieces):
      return True

    before_piece = before_pieces[stack_node.before_index]
    after_piece = after_pieces[stack_node.after_index]

    # get neighbors
    for b_piece in before_piece:
      b_piece_index = PIECE_ORDER[b_piece]
      b_indices = pos_map[b_piece_index]
      b_instance_idx = stack_node.before_pieces_count[b_piece_index]

      # there's no instance of this before piece
      # automatically false I < J if there is no I
      if len(b_indices) <= b_instance_idx:
        continue

      for a_piece in after_piece:
        a_piece_index = PIECE_ORDER[a_piece]
        a_indices = pos_map[a_piece_index]
        a_instance_idx = stack_node.after_pieces_count[a_piece_index]

        # there's no instance of this after piece
        # automatically satisfies I < J if there's no J yet there is an I
        # or both pieces are here so check order
        if (
          len(a_indices) <= a_instance_idx
          or b_indices[b_instance_idx] < a_indices[a_instance_idx]
        ):
          # went through all after pieces
          if stack_node.after_index + 1 == len(node.after_pieces):
            new_before_pieces_count = stack_node.before_pieces_count[:]
            new_before_pieces_count[b_piece_index] += 1

            stack.append(
              BeforeInterationNode(
                new_before_pieces_count, [0] * 7, stack_node.before_index + 1, 0
              )
            )

            continue

          new_after_pieces_count = stack_node.after_pieces_count[:]
          new_after_pieces_count[a_piece_index] += 1

          stack.append(
            BeforeInterationNode(
              stack_node.before_pieces_count,
              new_after_pieces_count,
              stack_node.before_index,
              stack_node.after_index + 1,
            )
          )

  return False


def evaluate_filter(node: AST, queue: str) -> bool:
  match node:
    ###
    # Atomic
    ###
    case RegexLiteral(value=value):
      try:
        # Compile the regex and check for a match
        pattern = re.compile(value)
        return pattern.search(queue) is not None
      except re.error as e:
        raise ValueError(f"Invalid regex: '{value}' - {e}")

    case CountLiteral(pieces=pieces, op=op, count=count):
      comp_op = OPERATORS[op]
      for target in pieces:
        # set of pieces: [LJ]=1 means that # of L = 1 OR # of J = 1
        result = any(comp_op(queue.count(piece), count) for piece in target)

        # this piece part is not satisfied so short circuit as false
        if not result:
          return False
      return True

    case BeforeLiteral():
      return evaluate_before(node, queue)

    ###
    # Operators
    ###

    # restrict range of queue to apply expr
    case RangeLookup(start=start, end=end, expr=expr):
      return evaluate_filter(expr, queue[start:end])

    case UnaryOp(expr=expr):
      # only NOT is a UnaryOp
      return not evaluate_filter(expr, queue)

    case BinaryOp(left=left, op=op, right=right):
      # Evaluate left side first
      left_val = evaluate_filter(left, queue)

      # short circuit if possible
      if op == "AND" and not left_val:
        return False

      elif op == "OR" and left_val:
        return True

      # evaluate and return right side otherwise
      return evaluate_filter(right, queue)

    case _:
      # error case
      raise ValueError(f"Unknown AST node type or operation: {type(node)}")
