import sys

import output

import pipeline

class SourceLine:
    def __init__(self, row_number, line):
        self.row_number = row_number
        self.line = line

class SourceFile:
    def __init__(self, file_name, raw_lines, raw_flags):
        self.file_name = file_name

        self.lines = []
        for row_number, line in enumerate(raw_lines):
            self.lines.append(SourceLine(row_number, line))

        self.verbose = "v" in raw_flags


    def __iter__(self):
        for line in self.lines:
            yield line

    def get_line(self, number):
        return next(filter(lambda l: l.row_number == number, self.lines), False)

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
                lines = list(line.strip("\n") for line in sourcef)
                return SourceFile(source_path, lines, command.flags)

        except FileNotFoundError:
            output.error("Init", "Could not find source file \"" + source_path + "\"")
            raise output.Abort()
    else:
        output.error("Init","Please specify a source file.")
        raise output.Abort()

if __name__ == "__main__":
    try:
        pipeline_input = initialise()
        pipeline.Pipeline(pipeline_input).begin()
    except output.Abort:
        sys.exit(1)

