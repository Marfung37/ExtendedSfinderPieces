import re
from collections.abc import Callable
from .utils import tetris_order_key
from typing import Final

# constant to just list tokens used for contexts, unused constant
CONTEXT_SPEC = [("LBRACE", r"\{"), ("RBRACE", r"\}")]

GEN_SPEC = [
  ("GEN_PIECES", r"[TILJSZO*]|\[\^?(?:[TILJSZO]|\[\^?[TILJSZO]+\])+\]"),
  ("PERMUTATE", r"!|p\d+"),
  ("WS", r"\s+"),  # Skip whitespace
  ("MISMATCH", r"."),  # catch any invalid characters
]

FILTER_SPEC = [
  ("RANGE_OP", r"\d+(?:-\d+)?:"),
  ("PIECES", r"(?:[TILJSZO*]|\[[TILJSZO*]+\])+"),
  ("COMP_OP", r"=|<=|>=|!=|=|<|>"),
  ("NUMBER", r"\d+"),
  ("REGEX", r"/[^/]+/"),  # regex within forward slashes, ie /abc/
  ("OR", r"\|\|"),
  ("AND", r"&&"),
  ("NOT", r"!"),
  ("LPAREN", r"\("),
  ("RPAREN", r"\)"),
  ("WS", r"\s+"),  # Skip whitespace
  ("MISMATCH", r"."),  # catch any invalid characters
]
GEN_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in GEN_SPEC))
FILTER_REGEX = re.compile(
  "|".join(f"(?P<{name}>{pattern})" for name, pattern in FILTER_SPEC)
)
# separate the different contexts for the tokens
CONTEXT_SPLIT_REGEX = re.compile(r"(\{.+?\})|([^{}]+)|(.)")


class Token:
  def __init__(self, kind: str | None = None, value: str | None = None):
    self.kind = kind
    self.value = value

  def __repr__(self):
    return f"({self.kind}, '{self.value}')"


def tokenize(text: str) -> list[Token]:
  tokens = []

  for match in CONTEXT_SPLIT_REGEX.finditer(text):
    filter_block, gen_block, invalid_char = match.groups()

    if gen_block:
      for m in GEN_REGEX.finditer(gen_block):
        kind = m.lastgroup
        value = m.group()
        if kind == "WS":
          continue  # skip whitespace
        if kind == "MISMATCH":
          raise ValueError(f"Unexpected character '{value}' at position {m.start()}")
        tokens.append(Token(kind, value))
    elif filter_block:
      inside_filter = filter_block[1:-1]  # strip the {}
      tokens.append(Token("LBRACE", "{"))
      for m in FILTER_REGEX.finditer(inside_filter):
        kind = m.lastgroup
        value = m.group()
        if kind == "WS":
          continue  # skip whitespace
        if kind == "REGEX":
          value = value[1:-1]  # strip forward slashes
        if kind == "MISMATCH":
          raise ValueError(f"Unexpected character '{value}' at position {m.start()}")
        tokens.append(Token(kind, value))
      tokens.append(Token("RBRACE", "}"))
    elif invalid_char:
      # only possible invalid characters are { or }
      raise ValueError(f"Found '{invalid_char}' without its counterpart")

  if len(tokens) == 0:
    raise ValueError(f"Expression {text} could not be tokenized")

  return tokens


class AST:
  pass


class FilterBlock(AST):
  def __init__(self, expr: AST):
    self.expr = expr

  def __repr__(self):
    return f"Filter({self.expr})"


class GeneratorLiteral(AST):
  def __init__(self, pool: list[str], permutate: int):
    self.pool = pool
    self.permutate = permutate

  def __repr__(self):
    return f"Generator({self.pool}p{self.permutate})"


class BinaryOp(AST):
  def __init__(self, left, op, right):
    self.left = left
    self.op = op  # Store the operator token or type
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
  def __init__(self, pieces: list[str], op: str, count: int):
    self.pieces = pieces
    self.op = op
    self.count = count

  def __repr__(self):
    return f"Count({self.pieces} {self.op} {self.count})"


class BeforeLiteral(AST):
  def __init__(self, before_pieces: list[str], after_pieces: list[str]):
    self.before_pieces = before_pieces
    self.after_pieces = after_pieces

  def __repr__(self):
    return f"Before({self.before_pieces} < {self.after_pieces})"


class RegexLiteral(AST):
  def __init__(self, value: str):
    self.value = value

  def __repr__(self):
    return f"Regex(`{self.value}`)"


# expression to get individual piece or sets of pieces
PIECES_REGEX = r"[TILJSZO*]|\[[TILJSZO*]+\]"
GENERATOR_REGEX = r"[TILJSZO]|\[\^?[TILJSZO]+\]"

TETRIS_PIECES: Final[set[str]] = set("TILJSZO")
TETRIS_ORDERED_PIECES: Final[list[str]] = list("TILJSZO")


class Parser:
  """
  Recursive Descent Parser with precedence OR, AND, NOT, ATOMIC for Filter and Basic Parsing for Generator
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

  def _generator_parse_pool(self, pool_expr: str) -> list[str]:
    pool: list[str]
    if pool_expr == "*":
      return TETRIS_ORDERED_PIECES
    # singular piece
    if len(pool_expr) == 1:
      return [pool_expr]

    # must have []
    raw_pieces = pool_expr[1:-1]
    outer_complement = raw_pieces.startswith("^")
    if outer_complement:
      # strip the leading ^
      raw_pieces = raw_pieces[1:]

    sub_patterns = re.findall(GENERATOR_REGEX, raw_pieces)

    pool = []
    base_pieces: list[str] = []
    for item in sub_patterns:
      if item.startswith("["):
        # strip the []
        item = item[1:-1]
        if item.startswith("^"):
          unique_pieces = TETRIS_PIECES - set(item[1:])
        else:
          unique_pieces = set(item)

        pool.append("".join(sorted(unique_pieces, key=tetris_order_key)))
      else:
        base_pieces.append(item)
    if outer_complement:
      base_pieces = list(TETRIS_PIECES - set(base_pieces))

    base_pieces.sort(key=tetris_order_key)
    if len(base_pieces) > 0:
      pool = base_pieces + pool

    return pool

  def _filter_parse_pieces(
    self, raw_pieces: str, duplicates: bool = False
  ) -> list[str]:
    sub_patterns = re.findall(PIECES_REGEX, raw_pieces)

    base_pieces = set()
    parsed_pieces = []
    for item in sub_patterns:
      # expand wildcard
      if item == "*":
        if duplicates:
          parsed_pieces.extend(TETRIS_ORDERED_PIECES)
        else:
          base_pieces = TETRIS_PIECES
      elif item.startswith("["):
        # strip the []
        inner_raw_pieces = item[1:-1]
        # get all pieces within []
        pieces_set = set(inner_raw_pieces)
        if "*" in pieces_set:
          parsed_pieces.append("TILJSZO")
        else:
          parsed_pieces.append("".join(sorted(pieces_set, key=tetris_order_key)))
      else:
        if duplicates:
          parsed_pieces.append(item)
        else:
          base_pieces.add(item)
    if not duplicates:
      parsed_pieces.extend(sorted(base_pieces, key=tetris_order_key))

    return parsed_pieces

  def parse(
    self, expr: str, lexer: Callable[[str], list[Token]] | None = None
  ) -> list[GeneratorLiteral | FilterBlock]:
    if lexer is None:
      lexer = self._lexer
    self._tokens = lexer(expr)
    self._pos = 0

    result = []
    while self._pos < len(self._tokens):
      if self._peek().kind == "LBRACE":
        self._consume("LBRACE")
        result.append(self._parse_filter())
        self._consume("RBRACE")
      else:
        result.append(self._parse_generator())

    return result

  def _parse_generator(self) -> GeneratorLiteral:
    if self._peek().kind == "GEN_PIECES":
      pool_expr = self._consume("GEN_PIECES")
      if pool_expr.value is None:
        raise ValueError("No expression given for a GEN_PIECES token")

      pool = self._generator_parse_pool(pool_expr.value)
      permutate = 1
      if len(pool) > 1 and self._peek().kind == "PERMUTATE":
        permutate_expr = self._consume("PERMUTATE")
        if permutate_expr.value is None:
          raise ValueError("No expression given for a PERMUTATE token")

        if permutate_expr.value == "!":
          permutate = len(pool)
        else:
          # strip the starting p letter for value
          permutate = int(permutate_expr.value[1:])
          if permutate == 0:
            raise ValueError(f"Permutate cannot be 0 in {pool_expr.value}p0")
      if permutate > len(pool):
        # permutate given larger than the pool
        raise ValueError(
          f"Given permutate {permutate} larger than the pool {pool_expr.value} -> {pool}"
        )
      return GeneratorLiteral(pool, permutate)
    else:
      raise ValueError(
        f"Expected GEN_PIECES token for generator but got {self._peek().kind} instead"
      )

  def _parse_filter(self) -> FilterBlock:
    return FilterBlock(self._parse_or())

  def _parse_or(self) -> AST:
    left = self._parse_and()
    while self._peek().kind == "OR":
      self._consume("OR")
      right = self._parse_and()
      left = BinaryOp(left, "OR", right)
    return left

  def _parse_and(self) -> AST:
    left = self._parse_unary()
    while self._peek().kind == "AND":
      self._consume("AND")
      right = self._parse_unary()
      left = BinaryOp(left, "AND", right)
    return left

  def _parse_unary(self) -> AST:
    # NOT
    if self._peek().kind == "NOT":
      self._consume("NOT")
      expr = self._parse_unary()
      return UnaryOp("NOT", expr)

    # range operator
    if self._peek().kind == "RANGE_OP":
      range_expr = self._consume("RANGE_OP")
      if range_expr.value is None:
        raise ValueError("No range expression found for RANGE_OP token")

      expr = self._parse_unary()
      endpoints = list(map(int, range_expr.value.rstrip(":").split("-")))
      if len(endpoints) == 1:
        # only one endpoint given is the end
        return RangeLookup(0, endpoints[0], expr)
      else:
        return RangeLookup(endpoints[0], endpoints[1], expr)

    return self._parse_atom()

  def _parse_atom(self):
    token = self._peek()
    if token is None:
      raise ValueError("Reached each of tokens too early")

    # if parentheses
    if token.kind == "LPAREN":
      self._consume("LPAREN")
      expr = self._parse_or()
      self._consume("RPAREN")
      return expr

    # if regex
    elif token.kind == "REGEX":
      regex_expr = self._consume("REGEX")
      if regex_expr.value is None:
        raise ValueError("No regex expression found for REGEX token")
      return RegexLiteral(regex_expr.value)

    elif token.kind == "PIECES":
      pieces = self._consume("PIECES")
      if pieces.value is None:
        raise ValueError("No pieces expression found for PIECES token")
      op = self._consume("COMP_OP")
      if op.value is None:
        raise ValueError("No comparison operator found for COMP_OP token")

      next_token = self._peek()
      # if before
      if next_token.kind == "PIECES":
        if op.value != "<":
          raise ValueError("Comparison of pieces expression that isn't before operator")
        after_pieces = self._consume("PIECES")
        if after_pieces.value is None:
          raise ValueError(
            "No pieces expression found for PIECES token after noticing before filter"
          )
        return BeforeLiteral(
          self._filter_parse_pieces(pieces.value, True),
          self._filter_parse_pieces(after_pieces.value, True),
        )
      elif next_token.kind == "NUMBER":
        count = self._consume("NUMBER")
        if count.value is None:
          raise ValueError(
            "No number found for NUMBER token after noticing count filter"
          )
        return CountLiteral(
          self._filter_parse_pieces(pieces.value), op.value, int(count.value)
        )
      else:
        raise ValueError(f"Unexpected token after PIECES COMP_OP: {token}")

    else:
      raise ValueError(f"Unexpected token: {token}")
