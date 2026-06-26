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

OPERATORS = {
  "=": operator.eq,
  "!=": operator.ne,
  "<": operator.lt,
  ">": operator.gt,
  "<=": operator.le,
  ">=": operator.ge,
}


def get_char_indices(queue_string: str) -> dict[str, list[int]]:
  """
  Builds a map of character positions.
  e.g., "ISIJ" -> {'I': [0, 2], 'S': [1], 'J': [3]}
  """
  positions = {}
  for index, char in enumerate(queue_string):
    positions.setdefault(char, []).append(index)
  return positions


def evaluate_before(node: BeforeLiteral, queue: str) -> bool:
  # get index of each piece
  pos_map = get_char_indices(queue)

  for before_idx, before_item in enumerate(node.before_pieces):
    for after_idx, after_item in enumerate(node.after_pieces):
      # normalize as 'T' is same as ['T']
      before_piece = before_item if isinstance(before_item, list) else [before_item]
      after_piece = after_item if isinstance(after_item, list) else [after_item]

      # is any of before fully satisfied?
      outer_flag = False
      for b_piece in before_piece:
        # is any of the after fully satisfied by this before piece?
        inner_flag = False

        # determine which instance of this piece is this
        # if second I in the before_pieces then look at second I in queue
        b_instance_idx = node.before_pieces[:before_idx].count(b_piece)

        for a_piece in after_piece:
          a_instance_idx = node.after_pieces[:after_idx].count(a_piece)

          b_indices = pos_map.get(b_piece, [])
          a_indices = pos_map.get(a_piece, [])

          # there's no instance of this after piece
          # automatically satisfies I < J if there's no J
          if len(a_indices) <= a_instance_idx:
            inner_flag = True
            break
          # there's no instance of this before piece
          # automatically false I < J if there's no I yet there is a J
          elif len(b_indices) <= b_instance_idx:
            continue
          # both pieces are here so check order
          elif b_indices[b_instance_idx] < a_indices[a_instance_idx]:
            inner_flag = True
            break

        # short circuit as found a before piece that is before one of the after pieces
        if inner_flag:
          outer_flag = True
          break

      # short circuit if this before piece is not able to be satisfied
      if not outer_flag:
        return False
  return True


# --- Filter Evaluator ---
# This function will traverse the Filter and execute the boolean logic.
def evaluate_filter(node: AST, queue: str) -> bool:
  ###
  # Atomic
  ###

  if isinstance(node, RegexLiteral):
    try:
      # Compile the regex and check for a match
      pattern = re.compile(node.value)
      return pattern.search(queue) is not None
    except re.error as e:
      raise ValueError(f"Invalid regex: '{node.value}' - {e}")

  elif isinstance(node, CountLiteral):
    comp_op = OPERATORS[node.op]
    for target in node.pieces:
      if isinstance(target, list):
        # set of pieces: [LJ]=1 means that # of L = 1 OR # of J = 1
        result = any(comp_op(queue.count(piece), node.count) for piece in target)
      else:
        # single piece
        result = comp_op(queue.count(target), node.count)

      # this piece part is not satisfied so short circuit as false
      if not result:
        return False
    return True

  elif isinstance(node, BeforeLiteral):
    return evaluate_before(node, queue)

  ###
  # Operators
  ###

  # restrict range of queue to apply expr
  elif isinstance(node, RangeLookup):
    return evaluate_filter(node.expr, queue[node.start : node.end])

  elif isinstance(node, UnaryOp):
    if node.op == "NOT":
      return not evaluate_filter(node.expr, queue)

  elif isinstance(node, BinaryOp):
    # Evaluate left side first
    left_val = evaluate_filter(node.left, queue)

    # short circuit if possible
    if node.op == "AND" and not left_val:
      return False

    elif node.op == "OR" and left_val:
      return True

    # evaluate and return right side otherwise
    return evaluate_filter(node.right, queue)

  raise ValueError(f"Unknown AST node type or operation: {type(node)}")
