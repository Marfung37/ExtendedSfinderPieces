import re
from collections.abc import Callable
import operator
from .utils import tetris_order_key

OPERATORS = {
  '=': operator.eq,
  '!=': operator.ne,
  '<' : operator.lt,
  '>' : operator.gt,
  '<=': operator.le,
  '>=': operator.ge,
}

TOKEN_SPEC = [
  ('RANGE_OP', r'\d+(?:-\d+)?:'),
  ('PIECES',   r'(?:[TILJSZO*]|\[[TILJSZO*]+\])+'),
  ('COMP_OP',  r'=|<=|>=|!=|=|<|>'),
  ('NUMBER',   r'\d+'),
  ('REGEX',    r'/[^/]+/'), # regex within forward slashes, ie /abc/
  ('OR',       r'\|\|'),
  ('AND',      r'&&'),
  ('NOT',      r'!'),
  ('LPAREN',   r'\('),
  ('RPAREN',   r'\)'),
  ('WS',       r'\s+'),  # Skip whitespace
]
MASTER_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
token_re = re.compile(MASTER_REGEX)

# expression to get individual piece or sets of pieces
PIECES_REGEX = r'[TILJSZO*]|\[[TILJSZO*]+\]' 

class Token:
  def __init__(self, kind: str | None = None, value: str | None = None):
    self.kind = kind
    self.value = value
  def __repr__(self):
    return f"({self.kind}, '{self.value}')"

class AST:
  pass

class BinaryOp(AST):
  def __init__(self, left, op, right):
    self.left = left
    self.op = op # Store the operator token or type
    self.right = right
  def __repr__(self):
    return f"({self.left} {self.op} {self.right})"

class UnaryOp(AST):
  def __init__(self, op, expr):
    self.op = op
    self.expr = expr
  def __repr__(self):
    return f"({self.op} {self.expr})"

class RangeLookup(AST):
  def __init__(self, start: int, end: int, expr: AST):
    self.start = start
    self.end = end
    self.expr = expr

  def __repr__(self):
    range_str = f"{self.start}-{self.end}"
    return f"Range({range_str} -> {self.expr})"

class CountLiteral(AST):
  def __init__(self, pieces: list[str | list[str]], op: str, count: int):
    self.pieces = pieces
    self.op = op
    self.count = count

  def __repr__(self):
    return f"Count({self.pieces} {self.op} {self.count})"

class BeforeLiteral(AST):
  def __init__(self, before_pieces: list[str | list[str]], after_pieces: list[str | list[str]]):
    self.before_pieces = before_pieces
    self.after_pieces = after_pieces

  def __repr__(self):
    return f"Before({self.before_pieces} < {self.after_pieces})"

class RegexLiteral(AST):
  def __init__(self, value: str):
    self.value = value
  def __repr__(self):
    return f"Regex(`{self.value}`)"

def tokenize(text):
  tokens = []
  for match in token_re.finditer(text):
    kind = match.lastgroup
    value = match.group()
    if kind == 'WS':
      continue  # skip whitespace
    if kind == 'REGEX':
      value = value[1:-1] # strip forward slashes
    tokens.append(Token(kind, value))

  if len(tokens) == 0:
    raise ValueError(f"Expression {text} could not be tokenized")

  return tokens

class Parser:
  """
  Recursive Descent Parser with precedence OR, AND, NOT, ATOMIC
  """
  def __init__(self, lexer: Callable[[str], list[Token]] = tokenize):
    self._tokens = []
    self._pos = 0
    self._lexer = lexer

  def _peek(self) -> Token:
    return self._tokens[self._pos] if self._pos < len(self._tokens) else Token()

  def _consume(self, expected=None) -> Token:
    token = self._peek()
    if expected and token.kind != expected:
      raise ValueError(f"Expected {expected} but got {token.kind}")
    self._pos += 1
    return token

  def _parse_pieces(self, raw_pieces: str, duplicates: bool = False) -> list[str | list[str]]:
    sub_patterns = re.findall(PIECES_REGEX, raw_pieces)

    base_pieces = set()
    parsed_pieces = []
    for item in sub_patterns:
      # expand wildcard
      if item == '*':
        if duplicates:
          parsed_pieces.extend('TILJSZO')
        else:
          base_pieces |= set('TILJSZO')
      elif item.startswith('['):
        inner_raw_pieces = item.strip('[]')
        # get all pieces within []
        pieces_set = set(inner_raw_pieces)
        if '*' in pieces_set:
          parsed_pieces.append(list('TILJSZO'))
        else:
          parsed_pieces.append(sorted(list(pieces_set), key=tetris_order_key))
      else:
        if duplicates:
          parsed_pieces.append(item)
        else:
          base_pieces.add(item)
    if not duplicates:
      parsed_pieces.extend(sorted(list(base_pieces), key=tetris_order_key))

    return parsed_pieces

  def parse(self, expr: str, lexer: Callable[[str], list[Token]] | None = None) -> AST:
    if lexer is None:
      lexer = self._lexer
    self._tokens = lexer(expr)
    self._pos = 0
    return self._parse_tokens()

  def _parse_tokens(self) -> AST:
    return self._parse_or()

  def _parse_or(self) -> AST:
    left = self._parse_and()
    while self._peek().kind == 'OR':
      self._consume('OR')
      right = self._parse_and()
      left = BinaryOp(left, 'OR', right)
    return left

  def _parse_and(self) -> AST:
    left = self._parse_unary()
    while self._peek().kind == 'AND':
      self._consume('AND')
      right = self._parse_unary()
      left = BinaryOp(left, 'AND', right)
    return left

  def _parse_unary(self) -> AST:
    # NOT
    if self._peek().kind == 'NOT':
      self._consume('NOT')
      expr = self._parse_unary()
      return UnaryOp('NOT', expr)

    # range operator
    if self._peek().kind == 'RANGE_OP':
      range_expr = self._consume('RANGE_OP')
      if range_expr.value is None:
        raise ValueError(f"No range expression found for RANGE_OP token")

      expr = self._parse_unary()
      endpoints = list(map(int, range_expr.value.rstrip(':').split('-')))
      if len(endpoints) == 1:
        # only one endpoint given is the end
        return RangeLookup(0, endpoints[0], expr)
      else:
        return RangeLookup(endpoints[0], endpoints[1], expr)

    return self._parse_atom()

  def _parse_atom(self):
    token = self._peek()
    if token is None:
      raise ValueError(f"Reached each of tokens too early")

    # if parentheses
    if token.kind == 'LPAREN':
      self._consume('LPAREN')
      expr = self._parse_tokens()
      self._consume('RPAREN')
      return expr

    # if regex
    elif token.kind == 'REGEX':
      regex_expr = self._consume('REGEX')
      if regex_expr.value is None:
        raise ValueError(f"No regex expression found for REGEX token")
      return RegexLiteral(regex_expr.value) 

    elif token.kind == 'PIECES':
      pieces = self._consume('PIECES')
      if pieces.value is None:
        raise ValueError(f"No pieces expression found for PIECES token")
      op = self._consume('COMP_OP')
      if op.value is None:
        raise ValueError(f"No comparison operator found for COMP_OP token")

      next_token = self._peek()
      # if before
      if next_token.kind == 'PIECES':
        if op.value != '<':
          raise ValueError(f"Comparison of pieces expression that isn't before operator")
        after_pieces = self._consume('PIECES')
        if after_pieces.value is None:
          raise ValueError(f"No pieces expression found for PIECES token after noticing before modifier")
        return BeforeLiteral(self._parse_pieces(pieces.value, True), self._parse_pieces(after_pieces.value, True))
      elif next_token.kind == 'NUMBER':
        count = self._consume('NUMBER')
        if count.value is None:
          raise ValueError(f"No number found for NUMBER token after noticing count modifier")
        return CountLiteral(self._parse_pieces(pieces.value), op.value, int(count.value))
      else:
        raise ValueError(f"Unexpected token after PIECES COMP_OP: {token}")

    else:
      raise ValueError(f"Unexpected token: {token}")

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

# --- AST Evaluator ---
# This function will traverse the AST and execute the boolean logic.
def evaluate_ast(node, queue: str) -> bool:
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
    return evaluate_ast(node.expr, queue[node.start: node.end])

  elif isinstance(node, UnaryOp):
    if node.op == 'NOT':
      return not evaluate_ast(node.expr, queue)

  elif isinstance(node, BinaryOp):
    # Evaluate left side first
    left_val = evaluate_ast(node.left, queue)

    # short circuit if possible
    if node.op == 'AND' and not left_val:
      return False

    elif node.op == 'OR' and left_val:
      return True

    # evaluate and return right side otherwise
    return evaluate_ast(node.right, queue)

  raise ValueError(f"Unknown AST node type or operation: {type(node)}")

if __name__ == "__main__":
  parser = Parser()

  print(parser.parse("LLJ < SI", tokenize))
  print(parser.parse("[*I]=2", tokenize))
  print(parser.parse("[TLJ]IO=1||[TI][LJ]O=1", tokenize))
  print(parser.parse("3-5:I<J && 4:T=1 && !/^T/ && [TLJ]IO=1 || [TI][LJ]O=1", tokenize))

  print(evaluate_ast(parser.parse('I<J'), 'IJ'))
  print(evaluate_ast(parser.parse('I<J'), 'JI'))
  print(evaluate_ast(parser.parse('II<J'), 'IJI'))
  print(evaluate_ast(parser.parse('II<J'), 'IIJ'))
  print(evaluate_ast(parser.parse('II<[LJ]'), 'IIJ'))
  print(evaluate_ast(parser.parse('II<[LJ]'), 'IIL'))
  print(evaluate_ast(parser.parse('[TI]<[LJ]'), 'TILJ'))
  print(evaluate_ast(parser.parse('[TI]<[LJ]'), 'JTLI'))
  print(evaluate_ast(parser.parse('[TI]<[LJ]'), 'LJTI'))
  print(evaluate_ast(parser.parse('[TI]<[LJ]'), 'LIJT'))
