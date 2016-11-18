import sys

import output

import pipeline

class SourceFile:
    def __init__(self, lines, flags):
        self.lines = lines
        self.flags = flags

    def has_flag(self, flag):
        return flag in self.flags

    def __iter__(self):
        for line in lines:
            yield line

class Command:
    def __init__(self, args, flags):
        self.args = args
        self.flags = flags

def get_command(supplied):
    args = supplied[1:]
    flags = set()
    for arg in args:
        if arg[0] is "-":
            flags.update(list(arg[1:]))
            args.remove(arg)

    return Command(args, flags)

def initialise():
    command = get_command(sys.argv)
    if command.args:
        source_path = command.args[0]

        try:
            with open(source_path) as sourcef:
                lines = list(line for line in sourcef)
                return SourceFile(lines, command.flags)

        except FileNotFoundError:
            output.error("Init", "Could not find source file \"" + source_path + "\"")

    else:
        output.error("Init","Please specify a source file.")

if __name__ == "__main__":
    source = initialise()
    pipeline.Pipeline(source).begin()
