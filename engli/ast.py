"""Engli AST — the shared intermediate representation.

Every frontend (the Engli parser, the HTML transcoder) produces these nodes, and
every backend (Python, TypeScript, English) consumes them. One AST, many targets
— that is what makes Engli a real language rather than a string rewriter.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class Node:
    pass


# ---- types ----------------------------------------------------------------
@dataclass
class TypeName(Node):
    name: str             # number | whole | text | truth | anything | nothing | <Custom>

@dataclass
class ListOf(Node):
    elem: Node

@dataclass
class MapOf(Node):
    key: Node
    val: Node


# ---- expressions ----------------------------------------------------------
@dataclass
class Num(Node):
    value: str            # kept as text; backend decides int/float rendering

@dataclass
class Str(Node):
    value: str

@dataclass
class Bool(Node):
    value: bool

@dataclass
class Null(Node):
    pass

@dataclass
class Name(Node):
    ident: str

@dataclass
class ListLit(Node):
    items: List[Node]

@dataclass
class DictLit(Node):
    pairs: List[Tuple[Node, Node]]   # (key, value)

@dataclass
class Unary(Node):
    op: str               # 'not' | 'neg'
    operand: Node

@dataclass
class Binary(Node):
    op: str
    left: Node
    right: Node

@dataclass
class Call(Node):
    func: Node
    args: List[Node]

@dataclass
class Member(Node):
    obj: Node
    name: str

@dataclass
class Index(Node):
    obj: Node
    index: Node

@dataclass
class PromptLookup(Node):     # prompt "<Role Title>"  -> the mapped prompt text
    title: str


# ---- statements -----------------------------------------------------------
@dataclass
class Param(Node):
    name: str
    type: Optional[Node] = None

@dataclass
class Let(Node):
    name: str
    value: Node
    type: Optional[Node] = None
    exported: bool = False

@dataclass
class Assign(Node):
    target: Node
    value: Node

@dataclass
class Return(Node):
    value: Optional[Node]

@dataclass
class Show(Node):
    value: Node

@dataclass
class ExprStmt(Node):
    expr: Node

@dataclass
class Func(Node):
    name: str
    params: List[Param]
    body: List[Node]
    ret: Optional[Node] = None
    exported: bool = False

@dataclass
class If(Node):
    cond: Node
    then: List[Node]
    orelse: List[Node] = field(default_factory=list)

@dataclass
class ForEach(Node):
    var: str
    iterable: Node
    body: List[Node]

@dataclass
class While(Node):
    cond: Node
    body: List[Node]

@dataclass
class Snippet(Node):          # Use snippet "<phrase>"  -> inline codemap/functionmap
    phrase: str

@dataclass
class RunCommand(Node):       # Run "<english phrase>"  -> resolved shell command
    phrase: str

@dataclass
class Import(Node):
    names: List[str]          # [] when module_import is True
    module: str
    alias: Optional[str] = None
    module_import: bool = False   # Import module "m" as alias

@dataclass
class Program(Node):
    body: List[Node]
