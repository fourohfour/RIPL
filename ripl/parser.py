from tokeniser import TokenType
from collections import deque
from enum import Enum
import output
import names
import random

class Priority:
    def __init__(self, lp, ln, rp, rn):
        self.lp = lp
        self.ln = ln
        self.rp = rp
        self.rn = rn

    @classmethod
    def highest(cls):
        return cls(0, False, 0, False)

    @classmethod
    def lowest(cls):
        return cls(0, True, 0, True)

    @classmethod
    def step(cls, prev):
        return cls(prev.lp + 1, False, prev.rp + 1, False)

    def highest_left(self):
        self.lp = 0
        return self

    def highest_right(self):
        self.rp = 0
        return self

    def nullify_left(self):
        self.ln = True
        return self

    def nullify_right(self):
        self.rn = True
        return self

    def __lt__(self, other):
        self_p  = 1000 if self.rn  else self.rp
        other_p = 1000 if other.ln else other.lp
        # If self has a larger numerical priority, then it is of lower priority
        return self_p > other_p

    def __gt__(self, other):
        self_p  = 1000 if self.rn  else self.rp
        other_p = 1000 if other.ln else other.lp
        # If self has a smaller numerical priority, then it is of higher priority
        # If both have the same priority, the first takes precedence (self)
        return self_p <= other_p

    def __str__(self):
        return "{:<5} : {:<5}".format("NULL" if self.ln else self.lp, "NULL" if self.rn else self.rp)

class Label:
    pass

class ScopeLabel(Label):
    priority = Priority.lowest()

class TokenLabel(Label):
    def __init__(self, token):
        self.token = token

# Code Block - sequence of code
class CodeBlockLabel(TokenLabel):
    priority = Priority.highest()

# Expression - anything enclosed by parens
class ExpressionLabel(TokenLabel):
    priority = Priority.step(CodeBlockLabel.priority)

# Structure - like `{3, 5, 4, 1}`
class StructureLabel(TokenLabel):
    priority = Priority.step(ExpressionLabel.priority)

# Structure Offset - like `x.3`
class StructureOffsetLabel(TokenLabel):
    priority = Priority.step(StructureLabel.priority)

# Point Access - like `&a`
class PointAccessLabel(TokenLabel):
    priority = Priority.step(StructureOffsetLabel.priority).highest_left()

# Operators - like `2 + 2`
class OperatorLabel(TokenLabel):
    priority = Priority.step(PointAccessLabel.priority)

# Procedures - like `@output`
class ProcedureLabel(TokenLabel):
    priority = Priority.step(OperatorLabel.priority).highest_left().nullify_right()

# Assignment - like `x ! 2`
class AssignmentLabel(TokenLabel):
    priority = Priority.step(ProcedureLabel.priority)

# Name - like `foo`
class NameLabel(TokenLabel):
    priority = Priority.highest()

# Literal - like `"hello"` or `2`
class LiteralLabel(TokenLabel):
    priority = Priority.highest()

class Parent:
    def __init__(self, parents):
        self.parents = parents

    def add(self, parent):
        if parent not in self.parents:
            self.parents.append(parent)

    def remove(self, parent):
        if parent in self.parents:
            self.parents.remove(parent)

    def get(self):
        if len(self.parents) == 1:
            return self.parents[0]
        return None

    def __iter__(self):
        for p in self.parents:
            yield p

class TrackingList(list):
    def __init__(self, parent, lst):
        self.parent = parent
        super().__init__(lst)

    def append(self, item):
        if item.ident == self.parent.ident:
            raise IndexError
        super().append(item)

class Node:
    def __init__(self, parent, children):
        self.parent    = parent
        self.children  = TrackingList(self, children)
        self.label     = None
        self.ident     = names.get_first_name() + str(random.randint(0,100))

    def set_label(self, label):
        self.label = label
        return self

    def _add_parent(self, parent):
        self.parent.add(parent)

    def _remove_parent(self, parent):
        self.parent.remove(parent)

    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)

        child._add_parent(self)

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)

        child._remove_parent(self)

    @classmethod
    def root(cls):
        return cls(Parent([]), [])

    @classmethod
    def undisputed(cls, parent, children = []):
        node = cls(Parent([parent]), children)
        parent.add_child(node)
        return node

    @classmethod
    def disputed(cls, parents, children = []):
        node = cls(Parent(parents), children)
        for parent in parents:
            parent.add_child(node)
        return node

    def traverse(self, lvl):
        t_list = [(lvl * "    ") + "-> {}: [{} : {}]"
                                   .format(self.ident,
                                           str(self.label.token.value)
                                           if hasattr(self.label, "token") and self.label.token.value is not "" else
                                           type(self.label).__name__,
                                           str(self.label.token.token_type.name)
                                           if hasattr(self.label, "token") else
                                           "")]
        for child in self.children:
            if type(self.label) is ScopeLabel:
                if child.parent.get() is None:
                    continue
            t_list += child.traverse(lvl + 1)
        return t_list

class SyntaxTree:
    def __init__(self):
        self.root = Node.root().set_label(ScopeLabel())

    def __str__(self):
        return "\n".join(self.root.traverse(0))

class TokenTape:
    def __init__(self, tokenised_repr):
        self.tokenised_repr = tokenised_repr
        self.ptr = -1

    def cur(self):
        try:
            return self.tokenised_repr.tokens[self.ptr]
        except IndexError:
            return None

    def scroll(self, movement):
        self.ptr += movement

    def next_token(self):
        self.scroll(1)
        return self.cur()

    def peek(self, ahead = 1):
        peek_ptr = self.ptr + ahead
        try:
            return self.tokenised_repr.tokens[peek_ptr]
        except IndexError:
            return None

    def __iter__(self):
        while True:
            n_item = self.next_token()
            if n_item is None:
                return
            yield n_item

class Action(Enum):
    EOF       = 1
    ADD_SCOPE = 2
    END_SCOPE = 3
    JMP_SCOPE = 4
    CLR_SCOPE = 5
    PARSE     = 10
    EXPECT    = 11

class Procedure:
    def __init__(self):
        self.actions = []

    def action(self, action, **action_args):
        self.actions.append((action, action_args))
        return self

class Scope:
    def __init__(self, node, inline, expires = -1):
        self.node   = node
        self.inline = inline
        self.expires = expires

    def update_expiry(self):
        self.expires -= 1

    def is_expired(self):
        return self.expires == 0

class Parser:
    def __init__(self, unit):
        self.unit = unit

    def get_parse_action(self, token):
        t = token.token_type

        if   t is TokenType.RETURN:
            return Procedure().action(Action.CLR_SCOPE)

        elif t is TokenType.EOF:
            return Procedure().action(Action.EOF)

        elif t is TokenType.INDENT:
            return Procedure().action(Action.JMP_SCOPE)

        elif t is TokenType.COLON:
            return Procedure().action(Action.ADD_SCOPE, label = CodeBlockLabel(token))

        elif t is TokenType.LPAREN:
            return Procedure().action(Action.ADD_SCOPE, label = ExpressionLabel(token))

        elif t is TokenType.RPAREN:
            return Procedure().action(Action.END_SCOPE)

        elif t is TokenType.LBRACE:
            return Procedure().action(Action.ADD_SCOPE, label = StructureLabel(token))

        elif t is TokenType.RBRACE:
            return Procedure().action(Action.END_SCOPE)

        elif t is TokenType.AT:
            return Procedure().action(Action.EXPECT, tokens = 1, label = ProcedureLabel(token))

        else:
            label = None

            if   t is TokenType.NAME:
                label = NameLabel(token)

            elif t is TokenType.STRING:
                label = LiteralLabel(token)

            elif t is TokenType.CHAR:
                label = LiteralLabel(token)

            elif t is TokenType.INTEGER:
                label = LiteralLabel(token)

            elif t is TokenType.DOT:
                label = StructureOffsetLabel(token)

            elif t is TokenType.TRUE:
                label = LiteralLabel(token)

            elif t is TokenType.FALSE:
                label = LiteralLabel(token)

            elif t is TokenType.AMPER:
                label = PointAccessLabel(token)

            elif t is TokenType.BANG:
                label = AssignmentLabel(token)

            else:
                label = OperatorLabel(token)

            return Procedure().action(Action.PARSE, label = label)

    def add_node(self, label, previous, scope):
        node = None
        if previous is None:
            node = Node.undisputed(scope.node).set_label(label)
        else:
            if previous.label.priority < label.priority:
               node = Node.disputed([scope.node, previous]).set_label(label)
            else:
                node = Node.undisputed(scope.node).set_label(label)
                node.add_child(previous)

        return node



    def parse(self):
        previous   = None
        scopes     = [Scope(self.tree.root, False)] # (scope node, inline)
        scope_ptr  = 0
        for token in self.tokens:
            node = None

            expired = []
            for scope in scopes:
                scope.update_expiry()
                if scope.is_expired():
                    expired.append(scope)

            proc = self.get_parse_action(token)

            for scope in expired:
                proc.action(Action.END_SCOPE)

            for action in proc.actions:
                if   action[0] in (Action.ADD_SCOPE, Action.EXPECT, Action.PARSE):
                    if scope_ptr != (len(scopes) - 1):
                        closed_scopes = scopes[scope_ptr + 1:]
                        for scope in closed_scopes:
                            if scope.inline:
                                scope_node = scope.node.parent.get()
                                self.unit.pipeline_input.log_error("Parser", scope_node.label.token.row_number, scope_node.label.token.col_number,
                                                                   "Un-closed inline scope.")

                        previous = scopes[scope_ptr + 1].node.parent.get()
                        del scopes[scope_ptr + 1:]

                if   action[0] in (Action.ADD_SCOPE, Action.EXPECT):
                    label  = action[1]["label"]
                    node   = self.add_node(label, previous, scopes[scope_ptr])
                    s_node = Node.undisputed(node).set_label(ScopeLabel())

                    if action[0] is Action.EXPECT:
                        scopes.append(Scope(s_node, not isinstance(label, CodeBlockLabel), expires = action[1]["tokens"]))
                    else:
                        scopes.append(Scope(s_node, not isinstance(label, CodeBlockLabel)))

                    previous = None
                    scope_ptr += 1

                elif action[0] is Action.END_SCOPE:
                    closed_scope = scopes.pop().node
                    previous     = closed_scope.parent.get()
                    scope_ptr -= 1

                elif action[0] is Action.JMP_SCOPE:
                    previous = None
                    scope_ptr += 1

                elif action[0] is Action.CLR_SCOPE:
                    for scope in scopes:
                        if not scope.is_expired() and scope.inline:
                            scope_node = scope.node.parent.get()
                            self.unit.pipeline_input.log_error("Parser", scope_node.label.token.row_number, scope_node.label.token.col_number,
                                                               "Line break prior to expiry of scope.")
                    previous = None
                    scope_ptr = 0

                elif action[0] is Action.PARSE:
                    label = action[1]["label"]
                    node = self.add_node(label, previous, scopes[scope_ptr])
                    previous = node

                elif action[0] is Action.EOF:
                    return


    def generate(self):
        self.tree   = SyntaxTree()
        self.tokens = TokenTape(self.unit.tokenised_repr)
        self.parse()
        if self.unit.pipeline_input.verbose:
            for line in str(self.tree).split("\n"):
                output.info("Parser", line)
