import sys

def create_setup(writer):
    writer.write(f"\nclass FilterNode(lg.Node):\n")
    writer.write("\tINPUT = lg.Topic(InputMessage)\n\tOUTPUT = lg.Topic(OutputMessage)\n")
    writer.write("\tdef setup(self):\n\t\tself.func = filter_function\n")
    return

def create_filter(writer):
    writer.write("\t@lg.subscriber(INPUT)\n\t@lg.publisher(OUTPUT)\n")
    writer.write("\n\tdef filter(self, message: MessageInput):\n")
    writer.write("\t\ty = self.func(message.x)\n\t\tyield self.OUTPUT, y")


def code_to_node(filename):
    """ Take a python file <filename> containing a filter function and 
    output a file named node.py containing labgraph node. 

    """
    with open(filename, 'r') as reader:
        with open("node.py", 'w') as writer:
            filter_function = False
            filter_type = ""
            for line in reader:
                if "import" in line: # copy all import statements
                    writer.write(line)
                if "filter_function" in line: # copy the filter function 
                    filter_function = True
                if filter_function:
                    writer.write(line)
                if "return" in line: 
                    filter_function = False
                    create_setup(writer)
                    create_filter(writer)
                
            
                    
if __name__ == "__main__":
    code_to_node(sys.argv[1])