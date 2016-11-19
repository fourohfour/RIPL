from enum import Enum

class TokenType(Enum):
    NAME = 0

    STRING   = 10
    CHAR     = 11
    INTEGER  = 12

    AMPER    = 20
    AT       = 21

    COLON    = 80
    LPAREN   = 81
    RPAREN   = 82

    INDENT   = 90
    NEWLINE  = 91
    EOF      = 92

class Token():
    def __init__(token_type, row_number, col_number):
        self.token_type = token_type
        self.row_number = row_number
        self.col_number = col_number

class Tokeniser():
    def __init__(self, unit):
        self.unit = unit

    def generate(self):
        raw = unit.pipeline_input

        for source_line in raw:
            line = source_line.line

            for char in line:
                pass
