"""Recursive-descent parser: tokens -> Engli AST.

Blocks open with ':' and close with 'End.'. Simple statements end with '.'.

  statement := [Export] (let | define) | set | if | foreach | while | return
             | show | use | run | import | exprstmt
  let     := 'Let' NAME 'be' expr ['as' type] '.'
  define  := 'Define' 'function' NAME ['taking' params] ['giving' type] ':' block 'End' '.'
  params  := NAME ['as' type] (',' NAME ['as' type])*
  import  := 'Import' ( 'module' STRING 'as' NAME | NAMES 'from' STRING ) '.'
  run     := 'Run' STRING '.'
  use     := 'Use' 'snippet' STRING '.'
  type    := 'number'|'whole'|'text'|'truth'|'anything'|'nothing'
           | 'list' 'of' type | 'map' 'of' type 'to' type | NAME

Expression precedence (low -> high):
  or ; and ; not ; comparison ; additive ; multiplicative ; unary- ; postfix ; primary
"""
from . import ast
from .tokens import (NUMBER, STRING, WORD, PERIOD, COLON, COMMA,
                     LPAREN, RPAREN, LBRACKET, RBRACKET, LBRACE, RBRACE, POSSESSIVE, EOF)
from .lexer import tokenize
from .errors import ParseError

_PRIM_TYPES = {"number", "whole", "text", "truth", "anything", "nothing"}


class Parser:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def peek(self, k=0):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def next(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def at_word(self, *words, k=0):
        t = self.peek(k)
        return t.kind == WORD and t.value.lower() in [w.lower() for w in words]

    def eat_kind(self, kind):
        t = self.peek()
        if t.kind != kind:
            raise ParseError(f"expected {kind}, got {t.kind} {t.value!r}", t.line, t.col)
        return self.next()

    def eat_word(self, word):
        t = self.peek()
        if not (t.kind == WORD and t.value.lower() == word.lower()):
            raise ParseError(f"expected '{word}', got {t.value!r}", t.line, t.col)
        return self.next()

    def parse_program(self):
        body = []
        while self.peek().kind != EOF:
            body.append(self.statement())
        return ast.Program(body)

    def block(self):
        body = []
        while not (self.peek().kind == EOF or self.at_word("End") or self.at_word("Otherwise")):
            body.append(self.statement())
        return body

    # -- types --
    def parse_type(self):
        if self.at_word("list"):
            self.next(); self.eat_word("of")
            return ast.ListOf(self.parse_type())
        if self.at_word("map"):
            self.next(); self.eat_word("of")
            k = self.parse_type(); self.eat_word("to"); v = self.parse_type()
            return ast.MapOf(k, v)
        name = self.eat_kind(WORD).value
        return ast.TypeName(name)

    # -- statements --
    def statement(self):
        exported = False
        if self.at_word("Export"):
            self.next(); exported = True
            if not (self.at_word("Let") or self.at_word("Define")):
                t = self.peek()
                raise ParseError("Export must precede Let or Define", t.line, t.col)
        if self.at_word("Let"):
            return self.p_let(exported)
        if self.at_word("Define"):
            return self.p_define(exported)
        if self.at_word("Set"):
            return self.p_set()
        if self.at_word("If"):
            return self.p_if()
        if self.at_word("For"):
            return self.p_foreach()
        if self.at_word("While"):
            return self.p_while()
        if self.at_word("Return"):
            return self.p_return()
        if self.at_word("Show"):
            return self.p_show()
        if self.at_word("Use"):
            return self.p_use()
        if self.at_word("Run"):
            return self.p_run()
        if self.at_word("Import"):
            return self.p_import()
        expr = self.expression()
        self.eat_kind(PERIOD)
        return ast.ExprStmt(expr)

    def p_let(self, exported=False):
        self.eat_word("Let")
        name = self.eat_kind(WORD).value
        self.eat_word("be")
        val = self.expression()
        typ = None
        if self.at_word("as"):
            self.next(); typ = self.parse_type()
        self.eat_kind(PERIOD)
        return ast.Let(name, val, typ, exported)

    def p_set(self):
        self.eat_word("Set")
        target = self.postfix()
        self.eat_word("to")
        val = self.expression()
        self.eat_kind(PERIOD)
        return ast.Assign(target, val)

    def p_define(self, exported=False):
        self.eat_word("Define")
        self.eat_word("function")
        name = self.eat_kind(WORD).value
        params = []
        if self.at_word("taking"):
            self.eat_word("taking")
            if self.at_word("nothing"):
                self.eat_word("nothing")
            else:
                params.append(self.p_param())
                while self.peek().kind == COMMA:
                    self.next()
                    params.append(self.p_param())
        ret = None
        if self.at_word("giving"):
            self.next(); ret = self.parse_type()
        self.eat_kind(COLON)
        body = self.block()
        self.eat_word("End")
        self.eat_kind(PERIOD)
        return ast.Func(name, params, body, ret, exported)

    def p_param(self):
        name = self.eat_kind(WORD).value
        typ = None
        if self.at_word("as"):
            self.next(); typ = self.parse_type()
        return ast.Param(name, typ)

    def p_if(self):
        self.eat_word("If")
        cond = self.expression()
        self.eat_kind(COLON)
        then = self.block()
        orelse = []
        if self.at_word("Otherwise"):
            self.eat_word("Otherwise")
            self.eat_kind(COLON)
            orelse = self.block()
        self.eat_word("End")
        self.eat_kind(PERIOD)
        return ast.If(cond, then, orelse)

    def p_foreach(self):
        self.eat_word("For"); self.eat_word("each")
        var = self.eat_kind(WORD).value
        self.eat_word("in")
        it = self.expression()
        self.eat_kind(COLON)
        body = self.block()
        self.eat_word("End"); self.eat_kind(PERIOD)
        return ast.ForEach(var, it, body)

    def p_while(self):
        self.eat_word("While")
        cond = self.expression()
        self.eat_kind(COLON)
        body = self.block()
        self.eat_word("End"); self.eat_kind(PERIOD)
        return ast.While(cond, body)

    def p_return(self):
        self.eat_word("Return")
        if self.peek().kind == PERIOD:
            self.next(); return ast.Return(None)
        val = self.expression()
        self.eat_kind(PERIOD)
        return ast.Return(val)

    def p_show(self):
        self.eat_word("Show")
        val = self.expression()
        self.eat_kind(PERIOD)
        return ast.Show(val)

    def p_use(self):
        self.eat_word("Use"); self.eat_word("snippet")
        phrase = self.eat_kind(STRING).value
        self.eat_kind(PERIOD)
        return ast.Snippet(phrase)

    def p_run(self):
        self.eat_word("Run")
        phrase = self.eat_kind(STRING).value
        self.eat_kind(PERIOD)
        return ast.RunCommand(phrase)

    def p_import(self):
        self.eat_word("Import")
        if self.at_word("module"):
            self.next()
            module = self.eat_kind(STRING).value
            self.eat_word("as")
            alias = self.eat_kind(WORD).value
            self.eat_kind(PERIOD)
            return ast.Import([], module, alias, module_import=True)
        names = [self.eat_kind(WORD).value]
        while self.peek().kind == COMMA:
            self.next(); names.append(self.eat_kind(WORD).value)
        self.eat_word("from")
        module = self.eat_kind(STRING).value
        self.eat_kind(PERIOD)
        return ast.Import(names, module)

    # -- expressions --
    def expression(self):
        return self.p_or()

    def p_or(self):
        left = self.p_and()
        while self.at_word("or"):
            self.next(); left = ast.Binary("or", left, self.p_and())
        return left

    def p_and(self):
        left = self.p_not()
        while self.at_word("and"):
            self.next(); left = ast.Binary("and", left, self.p_not())
        return left

    def p_not(self):
        if self.at_word("not"):
            self.next(); return ast.Unary("not", self.p_not())
        return self.p_compare()

    def p_compare(self):
        left = self.p_add()
        op = self.match_compare_op()
        if op:
            return ast.Binary(op, left, self.p_add())
        return left

    def match_compare_op(self):
        if not self.at_word("is"):
            return None
        save = self.i
        self.next()
        neg = False
        if self.at_word("not"):
            self.next(); neg = True
        if self.at_word("equal"):
            self.next(); self.eat_word("to")
            return "!=" if neg else "=="
        if self.at_word("greater"):
            self.next(); self.eat_word("than")
            if self.at_word("or"):
                self.next(); self.eat_word("equal"); self.eat_word("to"); return ">="
            return ">"
        if self.at_word("less"):
            self.next(); self.eat_word("than")
            if self.at_word("or"):
                self.next(); self.eat_word("equal"); self.eat_word("to"); return "<="
            return "<"
        if neg:
            self.i = save + 2
            return "!="
        return "=="

    def p_add(self):
        left = self.p_mul()
        while self.at_word("plus") or self.at_word("minus"):
            op = "+" if self.next().value.lower() == "plus" else "-"
            left = ast.Binary(op, left, self.p_mul())
        return left

    def p_mul(self):
        left = self.p_unary()
        while self.at_word("times") or self.at_word("modulo") or self.at_word("divided"):
            w = self.next().value.lower()
            if w == "divided":
                self.eat_word("by"); op = "/"
            else:
                op = "*" if w == "times" else "%"
            left = ast.Binary(op, left, self.p_unary())
        return left

    def p_unary(self):
        if self.at_word("negative"):
            self.next(); return ast.Unary("neg", self.p_unary())
        return self.postfix()

    def postfix(self):
        node = self.primary()
        while True:
            t = self.peek()
            if t.kind == LPAREN:
                self.next(); args = self.arg_list(RPAREN); self.eat_kind(RPAREN)
                node = ast.Call(node, args)
            elif t.kind == POSSESSIVE:
                self.next(); node = ast.Member(node, self.eat_kind(WORD).value)
            elif t.kind == WORD and t.value.lower() == "at":
                self.next(); node = ast.Index(node, self.primary())
            else:
                break
        return node

    def dict_literal(self):
        # { "key": expr, word: expr, ... }  — a bare word key is a string key
        self.eat_kind(LBRACE)
        pairs = []
        if self.peek().kind != RBRACE:
            pairs.append(self.dict_pair())
            while self.peek().kind == COMMA:
                self.next()
                if self.peek().kind == RBRACE:
                    break
                pairs.append(self.dict_pair())
        self.eat_kind(RBRACE)
        return ast.DictLit(pairs)

    def dict_pair(self):
        t = self.peek()
        if t.kind == STRING:
            key = ast.Str(self.next().value)
        elif t.kind == WORD:
            key = ast.Str(self.next().value)        # bare word -> string key
        elif t.kind == NUMBER:
            key = ast.Num(self.next().value)
        else:
            raise ParseError(f"bad dict key {t.kind} {t.value!r}", t.line, t.col)
        self.eat_kind(COLON)
        return (key, self.expression())

    def arg_list(self, close):
        args = []
        if self.peek().kind == close:
            return args
        args.append(self.expression())
        while self.peek().kind == COMMA:
            self.next(); args.append(self.expression())
        return args

    def primary(self):
        t = self.peek()
        if t.kind == NUMBER:
            self.next(); return ast.Num(t.value)
        if t.kind == STRING:
            self.next(); return ast.Str(t.value)
        if t.kind == LPAREN:
            self.next(); e = self.expression(); self.eat_kind(RPAREN); return e
        if t.kind == LBRACKET:
            self.next(); items = self.arg_list(RBRACKET); self.eat_kind(RBRACKET)
            return ast.ListLit(items)
        if t.kind == LBRACE:
            return self.dict_literal()
        if t.kind == WORD:
            w = t.value.lower()
            if w in ("true", "yes"):
                self.next(); return ast.Bool(True)
            if w in ("false", "no"):
                self.next(); return ast.Bool(False)
            if w in ("nothing", "null", "none"):
                self.next(); return ast.Null()
            if w == "prompt":
                self.next(); return ast.PromptLookup(self.eat_kind(STRING).value)
            if w == "call":
                self.next()
                callee = ast.Name(self.eat_kind(WORD).value)
                args = []
                if self.at_word("with"):
                    self.next(); args.append(self.expression())
                    while self.peek().kind == COMMA:
                        self.next(); args.append(self.expression())
                return ast.Call(callee, args)
            self.next(); return ast.Name(t.value)
        raise ParseError(f"unexpected {t.kind} {t.value!r}", t.line, t.col)


def parse(src):
    return Parser(tokenize(src)).parse_program()
