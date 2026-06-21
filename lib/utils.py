# Lookup table for 'priority' of the piece following TILJSZO order
PIECE_ORDER = [999] * 128

PIECE_ORDER[ord('T')] = 0
PIECE_ORDER[ord('I')] = 1
PIECE_ORDER[ord('L')] = 2
PIECE_ORDER[ord('J')] = 3
PIECE_ORDER[ord('S')] = 4
PIECE_ORDER[ord('Z')] = 5
PIECE_ORDER[ord('O')] = 6

def tetris_order_key(queue: str) -> tuple[int,...]:
  """
  Generate key to order of queues
  """
  return tuple(PIECE_ORDER[ord(piece)] for piece in queue)
