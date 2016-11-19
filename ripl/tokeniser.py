from enum import Enum

class TokenType(Enum):
    NAME = 0

    STRING   = 10
    INTEGER  = 11
    CHAR     = 12

    LBRACE   = 13
    RBRACE   = 14
    COMMA    = 15

    TRUE     = 16
    FALSE    = 17

    AMPER    = 20
    AT       = 21
    BANG     = 22

    PLUS     = 30
    MINUS    = 31

    LESS             = 40
    GREATER          = 41
    EQUAL            = 42
    NOT_EQUAL        = 43
    LESS_OR_EQUAL    = 44
    GREATER_OR_EQUAL = 45

    COLON    = 80
    LPAREN   = 81
    RPAREN   = 82

    INDENT   = 90
    NEWLINE  = 91
    EOF      = 92

class ProtoToken:
    def __init__(self, char, row_number, col_number, force_plain = False):
        self.char        = char
        self.row_number  = row_number
        self.col_number  = col_number
        self.force_plain = force_plain

class Token():
    def __init__(self, token_type, row_number, col_number):
        self.token_type = token_type
        self.row_number = row_number
        self.col_number = col_number
        self.indent     = 0

class TokenisedRepresentation():
    def __init__(self):
        self.tokens = []

    def add_token(self, token):
        self.tokens.append(token)

    def remove_token(self, token):
        self.tokens.remove(token)

    def __iter__(self):
        for token in self.tokens:
            yield token

class Tokeniser():
    def __init__(self, unit):
        self.unit = unit
        self.tokenised_repr = TokenisedRepresentation()

    def add_token(self, token):
        self.tokenised_repr.add_token(token)

    def filter_proto_tokens(self):
        for token in self.tokenised_repr:
            if type(token) is ProtoToken:
                self.tokenised_repr.remove(token)

    def tokenise(self, row_number, col_number, line):
        if not line.strip():
            self.add_token(Token(TokenType.NEWLINE, row_number, col_number))
            return

        char = line[0]

        token = None

        if   char == "{":
            token = Token(TokenType.LBRACE, row_number, col_number)
        elif char == "}":
            token = Token(TokenType.RBRACE, row_number, col_number)
        elif char == ",":
            token = Token(TokenType.COMMA, row_number, col_number)
        elif char == "&":
            token = Token(TokenType.AMPER, row_number, col_number)
        elif char == "@":
            token = Token(TokenType.AT, row_number, col_number)
        elif char == "!":
            token = Token(TokenType.BANG, row_number, col_number)
        elif char == "+":
            token = Token(TokenType.PLUS, row_number, col_number)
        elif char == "-":
            token = Token(TokenType.MINUS, row_number, col_number)
        elif char == ":":
            token = Token(TokenType.COLON, row_number, col_number)
        elif char == "(":
            token = Token(TokenType.LPAREN, row_number, col_number)
        elif char == ")":
            token = Token(TokenType.RPAREN, row_number, col_number)
        elif char == "\\":
            if len(line) > 1:
                token = ProtoToken(line[1], row_number, col_number, force_plain = True)
                self.add_token(token)
                self.tokenise(row_number, col_number + 2, line[2:])
                return
        else:
            token = ProtoToken(char, row_number, col_number)

        self.add_token(token)
        self.tokenise(row_number, col_number + 1, line[1:])

    def bundle_tokens(self):
        pass

    def generate(self):
        raw = self.unit.pipeline_input

        # First we generate the simple tokens
        for source_line in raw:
            line = source_line.line
            self.tokenise(source_line.row_number, 1, line)

        # Now we take the ProtoTokens and create the more complex ones.
        self.bundle_tokens()

        for token in self.tokenised_repr:
            try:
                print(token.token_type)
            except:
                print(token.char)


