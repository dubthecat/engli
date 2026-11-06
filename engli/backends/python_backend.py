"""AST -> Python source (with type hints, modules, and map-boost bridges)."""


class PythonBackend:
    target = "python"

    def __init__(self, snippet_resolver=None, command_resolver=None, prompt_resolver=None):
        self.snippet_resolver = snippet_resolver
        self.command_resolver = command_resolver
        self.prompt_resolver = prompt_resolver

    def generate(self, program):
        lines = []
        exports = []
        for stmt in program.body:
            lines.extend(self.stmt(stmt, 0))
            name = getattr(stmt, "name", None)
            if getattr(stmt, "exported", False) and name:
                exports.append(name)
        if exports:
            lines.append("__all__ = [" + ", ".join(repr(e) for e in exports) + "]")
        return "\n".join(lines) + "\n"

    def ind(self, n):
        return "    " * n

    # -- types --
    def ty(self, t):
        if t is None:
            return "Any"
        k = type(t).__name__
        if k == "ListOf":
            return f"list[{self.ty(t.elem)}]"
        if k == "MapOf":
            return f"dict[{self.ty(t.key)}, {self.ty(t.val)}]"
        return {"number": "float", "whole": "int", "text": "str", "truth": "bool",
                "anything": "Any", "nothing": "None"}.get(t.name, t.name)

    # -- statements --
    def stmt(self, node, depth):
        m = getattr(self, "s_" + type(node).__name__, None)
        if not m:
            raise NotImplementedError(f"python: {type(node).__name__}")
        return m(node, depth)

    def body(self, stmts, depth):
        if not stmts:
            return [self.ind(depth) + "pass"]
        out = []
        for s in stmts:
            out.extend(self.stmt(s, depth))
        return out

    def s_Let(self, n, d):
        ann = f": {self.ty(n.type)}" if n.type is not None else ""
        return [self.ind(d) + f"{n.name}{ann} = {self.expr(n.value)}"]

    def s_Assign(self, n, d):
        return [self.ind(d) + f"{self.expr(n.target)} = {self.expr(n.value)}"]

    def s_Return(self, n, d):
        return [self.ind(d) + ("return" if n.value is None else f"return {self.expr(n.value)}")]

    def s_Show(self, n, d):
        return [self.ind(d) + f"print({self.expr(n.value)})"]

    def s_ExprStmt(self, n, d):
        return [self.ind(d) + self.expr(n.expr)]

    def s_Func(self, n, d):
        ps = ", ".join(p.name + (f": {self.ty(p.type)}" if p.type is not None else "") for p in n.params)
        ret = f" -> {self.ty(n.ret)}" if n.ret is not None else ""
        return [self.ind(d) + f"def {n.name}({ps}){ret}:"] + self.body(n.body, d + 1)

    def s_If(self, n, d):
        out = [self.ind(d) + f"if {self.expr(n.cond)}:"] + self.body(n.then, d + 1)
        if n.orelse:
            out.append(self.ind(d) + "else:")
            out += self.body(n.orelse, d + 1)
        return out

    def s_ForEach(self, n, d):
        return [self.ind(d) + f"for {n.var} in {self.expr(n.iterable)}:"] + self.body(n.body, d + 1)

    def s_While(self, n, d):
        return [self.ind(d) + f"while {self.expr(n.cond)}:"] + self.body(n.body, d + 1)

    def s_Import(self, n, d):
        if n.module_import:
            return [self.ind(d) + f"import {self._pymod(n.module)} as {n.alias}"]
        return [self.ind(d) + f"from {self._pymod(n.module)} import {', '.join(n.names)}"]

    def _pymod(self, module):
        m = module.strip()
        if m.startswith("./"):
            m = m[2:]
        if m.endswith(".engli"):
            m = m[:-6]
        return m.replace("/", ".")

    def s_Snippet(self, n, d):
        code = self.snippet_resolver(n.phrase) if self.snippet_resolver else None
        if code is None:
            return [self.ind(d) + f"# [engli] snippet not found: {n.phrase!r}"]
        return [self.ind(d) + f"# [engli boost] {n.phrase}"] + \
               [self.ind(d) + ln for ln in code.splitlines()]

    def s_RunCommand(self, n, d):
        cmd = self.command_resolver(n.phrase) if self.command_resolver else None
        if cmd is None:
            return [self.ind(d) + f"# [engli] command not found: {n.phrase!r}"]
        esc = cmd.replace("\\", "\\\\").replace('"', '\\"')
        return [self.ind(d) + f'# [engli command] {n.phrase}',
                self.ind(d) + f'__import__("subprocess").run("{esc}", shell=True)']

    # -- expressions --
    _BIN = {"and": " and ", "or": " or ", "+": " + ", "-": " - ", "*": " * ",
            "/": " / ", "%": " % ", "==": " == ", "!=": " != ",
            "<": " < ", "<=": " <= ", ">": " > ", ">=": " >= "}

    def expr(self, n):
        t = type(n).__name__
        if t == "Num":
            return n.value
        if t == "Str":
            return repr(n.value)
        if t == "Bool":
            return "True" if n.value else "False"
        if t == "Null":
            return "None"
        if t == "Name":
            return n.ident
        if t == "ListLit":
            return "[" + ", ".join(self.expr(x) for x in n.items) + "]"
        if t == "DictLit":
            return "{" + ", ".join(self.expr(k) + ": " + self.expr(v) for k, v in n.pairs) + "}"
        if t == "Unary":
            return ("not " if n.op == "not" else "-") + self.expr(n.operand)
        if t == "Binary":
            return "(" + self.expr(n.left) + self._BIN[n.op] + self.expr(n.right) + ")"
        if t == "Call":
            return f"{self.expr(n.func)}(" + ", ".join(self.expr(a) for a in n.args) + ")"
        if t == "Member":
            return f"{self.expr(n.obj)}.{n.name}"
        if t == "Index":
            return f"{self.expr(n.obj)}[{self.expr(n.index)}]"
        if t == "PromptLookup":
            text = self.prompt_resolver(n.title) if self.prompt_resolver else None
            return repr(text if text is not None else n.title)
        raise NotImplementedError(f"python expr: {t}")
