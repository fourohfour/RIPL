from enum import Enum

import output

class TokenType(Enum):
    PROTO = -1

    NAME  = 0

    STRING   = 10
    INTEGER  = 11
    CHAR     = 12

    LBRACE   = 13
    RBRACE   = 14
    COMMA    = 15

    DOT      = 16

    TRUE     = 17
    FALSE    = 18

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

    RETURN   = 90
    INDENT   = 91
    EOF      = 92

class ProtoToken:
    def __init__(self, char, row_number, col_number, force_plain = False):
        self.char        = char
        self.row_number  = row_number
        self.col_number  = col_number
        self.force_plain = force_plain

        self.token_type  = TokenType.PROTO

class Token:
    def __init__(self, token_type, row_number, col_number, value=""):
        self.token_type = token_type
        self.row_number = row_number
        self.col_number = col_number
        self.value      = value

        self.char       = ""

    def __str__(self):
        return ("{name:<10}" + (" with value {value:<10}" if self.value else " " * 22) + "at {row}, {col}").format(
               name  = self.token_type.name,
               value = self.value,
               row   = self.row_number,
               col   = self.col_number
               )



class TokenisedRepresentation():
    def __init__(self):
        self.tokens = []

    def add_token(self, token):
        self.tokens.append(token)

    def remove_token(self, token):
        self.tokens.remove(token)

    def find_token(self, token):
        return self.tokens.find(token)

    def filter_proto_tokens(self):
        pre_filter = list(self.tokens)
        for index, token in enumerate(pre_filter):
            if type(token) is ProtoToken:
                self.remove_token(token)

    def __iter__(self):
        for token in self.tokens:
            yield token

class Tokeniser():
    def __init__(self, unit):
        self.unit = unit
        self.tokenised_repr = TokenisedRepresentation()

    def add_token(self, token):
        self.tokenised_repr.add_token(token)

    def tokenise(self, row_number, col_number, line, force_plain = False):
        # Add return token to start of line
        if col_number == 1:
            self.add_token(Token(TokenType.RETURN, row_number, 0))

        # End recursion at end of line
        if not line:
            return

        # Get the character to tokenise
        char = line[0]
        token = None


        # Characters that have meaning even when force_plain is True
        # Quote characters (") and (') are able to break force_plain
        # Escape character (\) needs to be able to escape Quote characters
        if   char == "\"":
            token = ProtoToken(char, row_number, col_number, force_plain = False)
            force_plain = not force_plain
        elif char == "'":
            token = ProtoToken(char, row_number, col_number, force_plain = False)
            force_plain = not force_plain
        elif char == "\\":
            if len(line) > 1:
                token = ProtoToken(line[1], row_number, col_number, force_plain = True)
                self.add_token(token)
                self.tokenise(row_number, col_number + 2, line[2:], force_plain = force_plain)
                return

        # We don't want to interpret a character twice, so check if token is still None
        if token is None:
            # Only interpret these characters if force_plain is False
            if not force_plain:
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
                elif char == ".":
                    token = Token(TokenType.DOT, row_number, col_number)

            # Regardless of force_plain, if we haven't got a token yet we want to create a Proto
            if token is  None:
                token = ProtoToken(char, row_number, col_number, force_plain = force_plain)


        # Add the token to the representation and tokenise the next character
        # We pass the value of force_plain along when we recurse
        self.add_token(token)
        self.tokenise(row_number, col_number + 1, line[1:], force_plain = force_plain)

    def bundle_tokens(self):
        lines = []
        line  = []
        for token in self.tokenised_repr:
            if token.token_type is TokenType.RETURN:
                if line:
                    lines.append(line)
                line = []
            line.append(token)
        lines.append(line)

        indent_levels = [0]

        for line in lines:
            space_count = 0
            for token in line:
                if type(token) is ProtoToken:
                    if token.char == " ":
                        space_count += 1
                    else:
                        break
                else:
                    pass

            if space_count > indent_levels[-1]:
                indent_levels.append(space_count)

            elif space_count < indent_levels[-1]:
                while space_count < indent_levels[-1]:
                    indent_levels.pop()

                if not space_count == indent_levels[-1]:
                    self.unit.pipeline_input.log_error("Tokeniser", line[0].row_number, space_count,
                                                       "Bad Dedent - does not match any outer indentation level.")

            for index, token in enumerate(line):
                if index in indent_levels[1:]:
                    line[index] = Token(TokenType.INDENT, token.row_number, token.col_number)

        tokens = [token for line in lines for token in line]

        def breaks_name(token):
            if type(token) is Token:
                return True
            else:
                if not token.force_plain:
                    breaking_chars = list("<>=~ \"'")
                    if token.char in breaking_chars:
                        return True
            return False


        bundled_chain = []

        skip_to = 0
        for index, token in enumerate(tokens):
            if skip_to is not 0:
                if index < skip_to:
                    continue
                else:
                    skip_to = 0

            if breaks_name(token):
                if type(token) is Token:
                    bundled_chain.append(token)
                else:
                    if   token.char == "\"":
                        string = ""
                        for strindex, strchar in enumerate(tokens[index + 1:], start = 1):
                            if not breaks_name(strchar):
                                string += strchar.char

                            elif type(strchar) is not ProtoToken:
                                self.unit.pipeline_input.log_error("Tokeniser", strchar.row_number, strchar.col_number,
                                                                   "Unterminated String")
                            elif not strchar.char == "\"":
                                self.unit.pipeline_input.log_error("Tokeniser", strchar.row_number, strchar.col_number,
                                                                   "Bad String Terminator")
                            else:
                                skip_to = index + strindex + 1
                                break
                        bundled_chain.append(Token(TokenType.STRING, token.row_number, token.col_number, value = string))

                    elif token.char == "'":
                        char = ""
                        for charindex, charchar in enumerate(tokens[index + 1:], start = 1):
                            if not breaks_name(charchar):
                                char += charchar.char
                            elif type(charchar) is not ProtoToken:
                                self.unit.pipeline_input.log_error("Tokeniser", charchar.row_number, charchar.col_number,
                                                                   "Unterminated Character")
                            elif not charchar.char == "'":
                                self.unit.pipeline_input.log_error("Tokeniser", charchar.row_number, charchar.col_number,
                                                                   "Bad Character Terminator")

                            else:
                                skip_to = index + charindex + 1
                                break
                        bundled_chain.append(Token(TokenType.CHAR, token.row_number, token.col_number, value = char))

                    elif token.char == ">":
                        next_char = tokens[index + 1]

                        if next_char.char == "=":
                            bundled_chain.append(Token(TokenType.GREATER_OR_EQUAL, token.row_number, token.col_number))
                            skip_to = index + 2
                        else:
                            bundled_chain.append(Token(TokenType.GREATER, token.row_number, token.col_number))

                    elif token.char == "<":
                        next_char = tokens[index + 1]

                        if next_char.char == "=":
                            bundled_chain.append(Token(TokenType.LESS_OR_EQUAL, token.row_number, token.col_number))
                            skip_to = index + 2
                        else:
                            bundled_chain.append(Token(TokenType.LESS, token.row_number, token.col_number))

                    elif token.char == "=":
                        bundled_chain.append(Token(TokenType.EQUAL, token.row_number, token.col_number))

                    elif token.char == "~":
                        next_char = tokens[index + 1]

                        if next_char.char == "=":
                            bundled_chain.append(Token(TokenType.NOT_EQUAL, token.row_number, token.col_number))
                            skip_to = index + 2

            else:
                name = ""
                for nameindex, namechar in enumerate(tokens[index:]):
                    if not breaks_name(namechar):
                        name += namechar.char
                    else:
                        skip_to = index + nameindex
                        break
                if all([n in list("0123456789") for n in list(name)]):
                    bundled_chain.append(Token(TokenType.INTEGER, token.row_number, token.col_number, value = int(name)))
                elif name.lower() == "true":
                    bundled_chain.append(Token(TokenType.TRUE, token.row_number, token.col_number))
                elif name.lower() == "false":
                    bundled_chain.append(Token(TokenType.FALSE, token.row_number, token.col_number))
                else:
                    bundled_chain.append(Token(TokenType.NAME, token.row_number, token.col_number, value = name))

        pure_repr = TokenisedRepresentation()

        for token in bundled_chain:
            pure_repr.add_token(token)

        pure_repr.filter_proto_tokens()
        self.tokenised_repr = pure_repr

    def generate(self):
        raw = self.unit.pipeline_input

        # First we generate the simple tokens
        for source_line in raw:
            line = source_line.line
            self.tokenise(source_line.row_number, 1, line)

        self.add_token(Token(TokenType.EOF, source_line.row_number, -1))

        # Now we take the ProtoTokens and create the more complex ones.
        self.bundle_tokens()

        self.unit.tokenised_repr = self.tokenised_repr

        if self.unit.pipeline_input.verbose:
            for token in self.unit.tokenised_repr:
                output.info("Tokeniser", str(token))


