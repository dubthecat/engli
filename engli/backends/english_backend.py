"""AST -> Engli English. The 'code to English' route: render any program (or an
HTML-transcoded AST) back into readable Engli. Round-trips with the parser.
"""


class EnglishBackend:
    target = "english"

    def __init__(self, snippet_resolver=None, command_resolver=None, prompt_resolver=None):
        pass  # English rendering needs no map resolution

    def generate(self, program):
        out = []
        for stmt in program.body:
            out.extend(self.stmt(stmt, 0))
        return "\n".join(out) + "\n"

    def ind(self, n):
        return "    " * n

    def ty(self, t):
        if t is None:
            return ""
        k = type(t).__name__
        if k == "ListOf":
            return f"list of {self.ty(t.elem)}"
        if k == "MapOf":
            return f"map of {self.ty(t.key)} to {self.ty(t.val)}"
        return t.name

    def stmt(self, node, depth):
        m = getattr(self, "s_" + type(node).__name__)
        return m(node, depth)

    def body(self, stmts, depth):
        out = []
        for s in stmts:
            out.extend(self.stmt(s, depth))
        return out

    def s_Let(self, n, d):
        exp = "Export " if n.exported else ""
        ann = f" as {self.ty(n.type)}" if n.type is not None else ""
        return [self.ind(d) + f"{exp}Let {n.name} be {self.expr(n.value)}{ann}."]

    def s_Assign(self, n, d):
        return [self.ind(d) + f"Set {self.expr(n.target)} to {self.expr(n.value)}."]

    def s_Return(self, n, d):
        return [self.ind(d) + ("Return." if n.value is None else f"Return {self.expr(n.value)}.")]

    def s_Show(self, n, d):
        return [self.ind(d) + f"Show {self.expr(n.value)}."]

    def s_ExprStmt(self, n, d):
        return [self.ind(d) + f"{self.expr(n.expr)}."]

    def s_Func(self, n, d):
        exp = "Export " if n.exported else ""
        ps = ", ".join(p.name + (f" as {self.ty(p.type)}" if p.type is not None else "") for p in n.params)
        taking = f" taking {ps}" if ps else ""
        giving = f" giving {self.ty(n.ret)}" if n.ret is not None else ""
        head = self.ind(d) + f"{exp}Define function {n.name}{taking}{giving}:"
        return [head] + self.body(n.body, d + 1) + [self.ind(d) + "End."]

    def s_If(self, n, d):
        out = [self.ind(d) + f"If {self.expr(n.cond)}:"] + self.body(n.then, d + 1)
        if n.orelse:
            out.append(self.ind(d) + "Otherwise:")
            out += self.body(n.orelse, d + 1)
        out.append(self.ind(d) + "End.")
        return out

    def s_ForEach(self, n, d):
        return [self.ind(d) + f"For each {n.var} in {self.expr(n.iterable)}:"] + \
               self.body(n.body, d + 1) + [self.ind(d) + "End."]

    def s_While(self, n, d):
        return [self.ind(d) + f"While {self.expr(n.cond)}:"] + \
               self.body(n.body, d + 1) + [self.ind(d) + "End."]

    def s_Import(self, n, d):
        if n.module_import:
            return [self.ind(d) + f'Import module "{n.module}" as {n.alias}.']
        return [self.ind(d) + f'Import {", ".join(n.names)} from "{n.module}".']

    def s_Snippet(self, n, d):
        return [self.ind(d) + f'Use snippet "{n.phrase}".']

    def s_RunCommand(self, n, d):
        return [self.ind(d) + f'Run "{n.phrase}".']

    _BIN = {"and": " and ", "or": " or ", "+": " plus ", "-": " minus ",
            "*": " times ", "/": " divided by ", "%": " modulo ",
            "==": " is equal to ", "!=": " is not equal to ",
            "<": " is less than ", "<=": " is less than or equal to ",
            ">": " is greater than ", ">=": " is greater than or equal to "}

    def expr(self, n):
        t = type(n).__name__
        if t == "Num":
            return n.value
        if t == "Str":
            return '"' + n.value.replace("\\", "\\\\").replace('"', '\\"') + '"'
        if t == "Bool":
            return "true" if n.value else "false"
        if t == "Null":
            return "nothing"
        if t == "Name":
            return n.ident
        if t == "ListLit":
            return "[" + ", ".join(self.expr(x) for x in n.items) + "]"
        if t == "DictLit":
            return "{" + ", ".join(self.expr(k) + ": " + self.expr(v) for k, v in n.pairs) + "}"
        if t == "Unary":
            return ("not " if n.op == "not" else "negative ") + self.expr(n.operand)
        if t == "Binary":
            return "(" + self.expr(n.left) + self._BIN[n.op] + self.expr(n.right) + ")"
        if t == "Call":
            return f"{self.expr(n.func)}(" + ", ".join(self.expr(a) for a in n.args) + ")"
        if t == "Member":
            return f"{self.expr(n.obj)}'s {n.name}"
        if t == "Index":
            return f"{self.expr(n.obj)} at {self.expr(n.index)}"
        if t == "PromptLookup":
            return f'prompt "{n.title}"'
        raise NotImplementedError(f"english expr: {t}")
