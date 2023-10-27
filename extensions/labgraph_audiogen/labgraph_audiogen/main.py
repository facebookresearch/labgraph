import sys


def main():
    print("Hello World from labgraph_audiogen!")
    args = sys.argv
    if args:
        print(f"Args are: {' '.join(args[1:])}")