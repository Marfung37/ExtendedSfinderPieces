import pytest
from sfinder_pieces.parser import Parser, GeneratorLiteral
from sfinder_pieces.evaluate_generator import evaluate_generator
from sfinder_pieces.utils import tetris_order_key
from typing import cast

parser = Parser()


@pytest.mark.parametrize(
  "expression, expected_length",
  [
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
    ("*p2", 42),
    ("*p7", 5040),
    ("[[TS]]", 2),
    ("[I[TS]]", 3),
    ("[T[TS]]", 2),
    ("[T[TS]]p2", 3),
  ],
)
def test_evaluate_generator(expression, expected_length):
  ast = cast(GeneratorLiteral, parser.parse(expression)[0])
  assert len(evaluate_generator(ast)) == expected_length


@pytest.mark.parametrize(
  "expression",
  [
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
  ],
)
def test_evaluate_generator_sorted(expression):
  ast = cast(GeneratorLiteral, parser.parse(expression)[0])
  assert evaluate_generator(ast) == sorted(
    evaluate_generator(ast), key=tetris_order_key
  )
