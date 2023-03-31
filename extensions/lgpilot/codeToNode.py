import sys
import re 

def create_func(writer, library_name, function_name, function_args):
    writer.write(f"from {library_name} import {function_name}\n")
    writer.write(f"def {function_name}({function_args}):\n\t")
    writer.write(f"y = {function_name}({function_args})\n\t")
    writer.write("return y\n")

def create_setup(writer, function_name):
    writer.write(f"\nclass {function_name}Node(lg.Node):\n\t")
    writer.write("INPUT = lg.Topic(InputMessage)\n\tOUTPUT = lg.Topic(OutputMessage)\n\n\t")
    writer.write(f"def setup(self):\n\t\tself.func = {function_name}\n\n\t")

def create_feature(writer, function_name, function_args):
    writer.write("@lg.subscriber(INPUT)\n\t@lg.publisher(OUTPUT)\n\n\t")
    writer.write(f"def {function_name}_feature(self, message: InputMessage):\n\t\t")
    # turn a string containing a list of function args (ex: 'x, y, z') into InputMessage attributes (ex: message.x, message.y, message.z)
    params = [f"message.{i.strip()}" for i in function_args.split(",")]
    # turn a list of parameters (ex: ["message.x", "message.y", "message.z"]) into a string of arguments
    # ex: y = self.func(message.x, message.y, message.z)
    writer.write("y = self.func(" + ", ".join(params) + ")\n\t\tyield self.OUTPUT, y")


def code_to_node(filename):
    """ Take a python file <filename> containing a function and 
    output a file named node.py containing labgraph node. 

    """
    library_name, function_name, function_args = "", "", ""
    with open(filename, 'r') as reader:
        with open("node.py", 'w') as writer:
            for line in reader:
                    # first check if line contains library_name and function name 
                    result = re.search("from (.*) import (.*)", line)
                    if result is not None: # a match was found 
                        library_name, function_name = result.group(1), result.group(2)
                    # next check if line contains function arguments 
                    result = re.search(f"[a-zA-z]* = {function_name}\((.*)\)", line)
                    if result is not None:
                        function_args = result.group(1)

            create_func(writer, library_name, function_name, function_args)
            create_setup(writer, function_name)
            create_feature(writer, function_name, function_args)
            
                    
if __name__ == "__main__":
    code_to_node(sys.argv[1])