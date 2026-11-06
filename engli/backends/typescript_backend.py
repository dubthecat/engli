"""AST -> TypeScript source. Proves Engli is multi-target, not Python-bound.

Portable constructs (types, modules, prompt lookups, control flow) emit real TS.
Python-only boosts (shell commands, Python snippets) emit a marker comment.
"""


class TypeScriptBackend:
    target = "typescript"

    def __init__(self, snippet_resolver=None, command_resolver=None, prompt_resolver=None):
        self.snippet_resolver = snippet_resolver   # python snippets aren't portable
        self.command_resolver = command_resolver   # shell isn't portable
        self.prompt_resolver = prompt_resolver      # prompts are just strings -> portable

    def generate(self, program):
        lines = []
        for stmt in program.body:
            lines.extend(self.stmt(stmt, 0))
        return "\n".join(lines) + "\n"

    def ind(self, n):
        return "  " * n

    def ty(self, t):
        if t is None:
            return "any"
        k = type(t).__name__
        if k == "ListOf":
            return f"Array<{self.ty(t.elem)}>"
        if k == "MapOf":
            return f"Record<{self.ty(t.key)}, {self.ty(t.val)}>"
        return {"number": "number", "whole": "number", "text": "string", "truth": "boolean",
                "anything": "any", "nothing": "void"}.get(t.name, t.name)

    def stmt(self, node, depth):
        m = getattr(self, "s_" + type(node).__name__, None)
        if not m:
            raise NotImplementedError(f"typescript: {type(node).__name__}")
        return m(node, depth)

    def body(self, stmts, depth):
        out = []
        for s in stmts:
            out.extend(self.stmt(s, depth))
        return out

    def s_Let(self, n, d):
        exp = "export " if n.exported else ""
        ann = f": {self.ty(n.type)}" if n.type is not None else ""
        return [self.ind(d) + f"{exp}let {n.name}{ann} = {self.expr(n.value)};"]

    def s_Assign(self, n, d):
        return [self.ind(d) + f"{self.expr(n.target)} = {self.expr(n.value)};"]

    def s_Return(self, n, d):
        return [self.ind(d) + ("return;" if n.value is None else f"return {self.expr(n.value)};")]

    def s_Show(self, n, d):
        return [self.ind(d) + f"console.log({self.expr(n.value)});"]

    def s_ExprStmt(self, n, d):
        return [self.ind(d) + self.expr(n.expr) + ";"]

    def s_Func(self, n, d):
        exp = "export " if n.exported else ""
        ps = ", ".join(f"{p.name}: {self.ty(p.type)}" for p in n.params)
        ret = self.ty(n.ret) if n.ret is not None else "any"
        head = self.ind(d) + f"{exp}function {n.name}({ps}): {ret} {{"
        return [head] + self.body(n.body, d + 1) + [self.ind(d) + "}"]

    def s_If(self, n, d):
        out = [self.ind(d) + f"if ({self.expr(n.cond)}) {{"] + self.body(n.then, d + 1)
        if n.orelse:
            out.append(self.ind(d) + "} else {")
            out += self.body(n.orelse, d + 1)
        out.append(self.ind(d) + "}")
        return out

    def s_ForEach(self, n, d):
        return [self.ind(d) + f"for (const {n.var} of {self.expr(n.iterable)}) {{"] + \
               self.body(n.body, d + 1) + [self.ind(d) + "}"]

    def s_While(self, n, d):
        return [self.ind(d) + f"while ({self.expr(n.cond)}) {{"] + \
               self.body(n.body, d + 1) + [self.ind(d) + "}"]

    def s_Import(self, n, d):
        if n.module_import:
            return [self.ind(d) + f'import * as {n.alias} from "{n.module}";']
        return [self.ind(d) + f'import {{ {", ".join(n.names)} }} from "{n.module}";']

    def s_Snippet(self, n, d):
        return [self.ind(d) + f"// [engli] snippet {n.phrase!r} is a Python-target boost (not emitted for TS)"]

    def s_RunCommand(self, n, d):
        return [self.ind(d) + f"// [engli] Run {n.phrase!r} is a shell command (Python target only)"]

    _BIN = {"and": " && ", "or": " || ", "+": " + ", "-": " - ", "*": " * ",
            "/": " / ", "%": " % ", "==": " === ", "!=": " !== ",
            "<": " < ", "<=": " <= ", ">": " > ", ">=": " >= "}

    def expr(self, n):
        t = type(n).__name__
        if t == "Num":
            return n.value
        if t == "Str":
            return '"' + n.value.replace("\\", "\\\\").replace('"', '\\"') + '"'
        if t == "Bool":
            return "true" if n.value else "false"
        if t == "Null":
            return "null"
        if t == "Name":
            return n.ident
        if t == "ListLit":
            return "[" + ", ".join(self.expr(x) for x in n.items) + "]"
        if t == "DictLit":
            return "{" + ", ".join(self.expr(k) + ": " + self.expr(v) for k, v in n.pairs) + "}"
        if t == "Unary":
            return ("!" if n.op == "not" else "-") + self.expr(n.operand)
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
            s = text if text is not None else n.title
            return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
        raise NotImplementedError(f"ts expr: {t}")
