from sfinder_pieces import sfinder_pieces
from sys import argv

if __name__ == "__main__":
  if len(argv) != 2:
    print("Usage: python pieces.py [pattern]")
    exit()
  # print out all queues for passed in string
  pattern = argv[1]

  for queue in sfinder_pieces(pattern):
    print(queue)
