import sys

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    print(f"Hello World from labgraph_audiogen with args: {' '.join(args)}")