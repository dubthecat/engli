"""An HTML -> Engli AST frontend: the "other transcoding route".

Engli's value is a shared AST with multiple backends. A frontend is anything
that produces that AST. This one parses HTML (stdlib html.parser, no deps) into
DOM-construction statements, so `html -> AST -> TypeScript` emits real
document.createElement code. Same AST, so a Python/other backend could consume
it too.
"""
from html.parser import HTMLParser
from . import ast

_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
         "link", "meta", "param", "source", "track", "wbr"}


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.body = []          # list of statements
        self.stack = []         # var names of open parents
        self.roots = []         # top-level element var names
        self._n = 0

    def _var(self, prefix):
        v = f"{prefix}{self._n}"
        self._n += 1
        return v

    def _doc_call(self, method, args):
        return ast.Call(ast.Member(ast.Name("document"), method), args)

    def _append_to_parent(self, child_var):
        if self.stack:
            parent = self.stack[-1]
            self.body.append(ast.ExprStmt(
                ast.Call(ast.Member(ast.Name(parent), "appendChild"), [ast.Name(child_var)])))
        else:
            self.roots.append(child_var)

    def handle_starttag(self, tag, attrs):
        v = self._var("el")
        self.body.append(ast.Let(v, self._doc_call("createElement", [ast.Str(tag)])))
        for k, val in attrs:
            self.body.append(ast.ExprStmt(
                ast.Call(ast.Member(ast.Name(v), "setAttribute"),
                         [ast.Str(k), ast.Str(val if val is not None else "")])))
        self._append_to_parent(v)
        if tag not in _VOID:
            self.stack.append(v)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID and self.stack and self.stack[-1].startswith("el"):
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag not in _VOID and self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if not data.strip():
            return
        v = self._var("t")
        self.body.append(ast.Let(v, self._doc_call("createTextNode", [ast.Str(data)])))
        self._append_to_parent(v)


def parse_html(html):
    """HTML string -> ast.Program with a render() function returning the root."""
    b = _Builder()
    b.feed(html)
    b.close()
    body = list(b.body)
    if len(b.roots) == 1:
        root_expr = ast.Name(b.roots[0])
    else:
        frag = "frag"
        body.insert(0, ast.Let(frag, ast.Call(
            ast.Member(ast.Name("document"), "createDocumentFragment"), [])))
        for r in b.roots:
            body.append(ast.ExprStmt(ast.Call(
                ast.Member(ast.Name(frag), "appendChild"), [ast.Name(r)])))
        root_expr = ast.Name(frag)
    body.append(ast.Return(root_expr))
    return ast.Program([ast.Func("render", [], body)])
