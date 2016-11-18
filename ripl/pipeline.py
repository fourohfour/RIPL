import time

import output

import generator
import optimiser

class Unit:
    def __init__(self, unit_name):
        self.unit_name         = unit_name

        self.pipeline_input    = None
        self.intermediate_repr = None


class Pipeline:
    def __init__(self, pipeline_input):
        unit_name = "{0}-{1}".format(pipeline_input.file_name, str(int(time.time())))
        self.unit = Unit(unit_name)

        self.unit.pipeline_input = pipeline_input

    def begin(self):
        pass

