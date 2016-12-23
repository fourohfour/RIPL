import time

import output

import tokeniser
import parser
import optimiser

class Unit:
    def __init__(self, unit_name, pipeline_input):
        self.unit_name       = unit_name
        self.pipeline_input  = pipeline_input

        self.tokenised_repr  = None
        self.abstract_repr   = None


class Pipeline:
    def __init__(self, pipeline_input):
        unit_name = "{0}-{1}".format(pipeline_input.file_name, str(int(time.time())))
        unit_name = str(hash(unit_name))

        self.unit = Unit(unit_name, pipeline_input)

    def begin(self):
        tokeniser .Tokeniser(self.unit) .generate()
        parser    .Parser(self.unit)    .generate()
